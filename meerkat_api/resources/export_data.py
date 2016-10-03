"""
Data resource for exporting data
"""
from flask_restful import Resource
from flask import request, abort, current_app
from sqlalchemy import or_, text
from sqlalchemy.orm import aliased
from dateutil.parser import parse
import json
import json, io, csv, logging

from meerkat_api.util import row_to_dict
from meerkat_api import db, app, output_csv
from meerkat_abacus.model import Data, form_tables
from meerkat_abacus.util import all_location_data
from meerkat_abacus.config import country_config, config_directory
from meerkat_api.resources.variables import Variables
from meerkat_api.resources.epi_week import EpiWeek
from meerkat_api.authentication import authenticate
from meerkat_abacus.util import get_locations, get_locations_by_deviceid
from meerkat_api.resources.alerts import get_alerts


class Forms(Resource):
    """
    Return a dict of forms with all their columns

    Returns:\n
       forms: dict of forms with all their variables\n
    """
    decorators = [authenticate]

    def get(self):
        return_data = {}
        for form in form_tables.keys():
            print(form)
            results = db.session.query(form_tables[form]).first()
            if results and results.data:
                return_data[form] = list(results.data.keys(
                )) + ["clinic", "district", "region"]
            else:
                return_data[form] = []
        return return_data


class ExportData(Resource):
    """
    Export data table from db

    Returns:\n
        csv_file: with a row for each row in the data table\n
    """
    representations = {'text/csv': output_csv}
    decorators = [authenticate]

    def get(self, use_loc_ids=False):
        results = db.session.query(Data)
        variables = set()
        locs = get_locations(db.session)
        for row in results:
            variables = variables.union(set(row.variables.keys()))
        fieldnames = ["id", "country", "region", "district", "clinic",
                      "clinic_type", "geolocation", "date", "uuid"
                      ] + list(variables)
        dict_rows = []
        for row in results:
            dict_row = row_to_dict(row)
            if not use_loc_ids:
                for l in ["country", "region", "district", "clinic"]:
                    if dict_row[l]:
                        dict_row[l] = locs[dict_row[l]].name
            dict_row.update(dict_row.pop("variables"))
            dict_rows.append(dict_row)
        return {"data": dict_rows, "keys": fieldnames, "filename": "data"}


class ExportCategory(Resource):
    """
    Export cases from case form that matches a category

    We take a variable dictionary of form field name: display_name.
    There are some special commands that can be given in the form field name:

    * icd_name$category will translate an icd code in icd_code to names given by the variables in category

    * clinic,region and district will give this location information

    * field$month, field$year, field$epi_week: will extract the month, year or epi_week from the field

    * alert_links$alert_investigation$field: will get the field in the correpsonding alert_investigation

    * calc$bmi calculates bmi as: 
      results./bmi_weight / ((results./bmi_height/100) * (results./bmi_height/100))
    
    Args:\n
       category: category to match\n
       variables: variable dictionary\n
    Returns:\n
       csv_file\n
    """
    representations = {'text/csv': output_csv}

    decorators = [authenticate]

    def get(self, form_name, category, download_name):
        app.logger.warning("Export Category Called")


        if "variables" in request.args.keys():
            variables = json.loads(request.args["variables"])
        else:
            return []
        var = Variables()
        data_vars = var.get(category)
        data_keys = data_vars.keys()
        if len(data_keys) == 0:
            return []
        return_keys = []
        translation_dict = {}
        alert = False
        icd_code_to_name = {}
        link_ids = []
        have_links = False

        min_translation = {}
        
        #Set up icd_code_to_name if needed and determine if alert_links are included
        for v in variables:
            return_keys.append(v[1])

            if "icd_name$" in v[0]:
                category = v[0].split("$")[1]
                icd_name = var.get(category)
                icd_code_to_name[v[0]] = {}
                for i in icd_name.keys():
                    condition = icd_name[i]["condition"]
                    if "," in condition:
                        # If a variable have many icd codes we take all of them into account
                        codes = condition.split(",")
                    else:
                        codes = [condition]
                    for c in codes:
                        icd_code_to_name[v[0]][c.strip()] = icd_name[i]["name"]
            if "$translate" in v[0]:
                split = v[0].split("$")
                field = "$".join(split[:-1])
                trans = split[-1]
                tr_dict = json.loads(trans.split(";")[1].replace("'",'"'))
                min_translation[v[1]] = tr_dict
                v[0] = field
                print(min_translation)
            if "gen_link$" in v[0]:
                have_links = True
                link_ids.append(v[0].split("$")[1])
            translation_dict[v[1]] = v[0]
            
        link_ids = set(link_ids)
        links_by_type, links_by_name = get_links(config_directory +
                                                 country_config["links_file"])
        # DB query, with yield_per(200) for memory reasons

        columns = [Data, form_tables[form_name]]
           
        link_id_index = {}
        joins = []
        for i, l in enumerate(link_ids):
            form = aliased(form_tables[links_by_name[l]["to_form"]])
            joins.append((form, Data.links[(l,-1)].astext == form.uuid))
            link_id_index[l] = i + 2
            columns.append(form.data)
            
            
            
        results= db.session.query(*columns).join(
            form_tables[form_name], Data.uuid == form_tables[form_name].uuid)
        for join in joins:
            results = results.outerjoin(join[0], join[1])
        results = results.filter(
            or_(Data.variables.has_key(key)
                for key in data_keys)).yield_per(200)
        locs = get_locations(db.session)
        dict_rows = []

        #Prepare each row
        for r in results:
            dict_row = {}
            for k in return_keys:
                form_var = translation_dict[k]
                if "icd_name$" in form_var:
                    if r[1].data["icd_code"] in icd_code_to_name[form_var]:
                        dict_row[k] = icd_code_to_name[form_var][r[1].data[
                            "icd_code"]]
                    else:
                        dict_row[k] = None
                elif form_var == "clinic":
                    dict_row[k] = locs[r[0].clinic].name
                elif form_var == "region":
                    dict_row[k] = locs[r[0].region].name
                elif form_var == "district":
                    if r[0].district:
                        dict_row[k] = locs[r[0].district].name
                    else:
                        dict_row[k] = None
                elif "$year" in form_var:
                    field = form_var.split("$")[0]
                    if field in r[1].data and r[1].data[field]:
                        dict_row[k] = parse(r[1].data[field]).year
                    else:
                        dict_row[k] = None
                elif "$month" in form_var:
                    field = form_var.split("$")[0]
                    if field in r[1].data and r[1].data[field]:
                        dict_row[k] = parse(r[1].data[field]).month
                    else:
                        dict_row[k] = None
                elif "$epi_week" in form_var:
                    ewg = EpiWeek()
                    field = form_var.split("$")[0]
                    if field in r[1].data and r[1].data[field]:
                        dict_row[k] = ewg.get(r[1].data[field])["epi_week"]
                    else:
                        dict_row[k] = None

                #A general framework for referencing links in the download data.
                #link$<link id>$<linked form field>
                elif "gen_link$" in form_var:
                    link = form_var.split("$")[1]
                    link_index = link_id_index[link]
                    if r[link_index]:
                        dict_row[k] = r[link_index][form_var.split("$")[-1]]
                    else:
                        dict_row[k] = None

                elif "code" == form_var.split("$")[0]:
                    # code$cod_1,cod_2,Text_1,Text_2$default_value
                    split = form_var.split("$")
                    codes = split[1].split(",")
                    text = split[2].split(",")
                    if len(split) > 3:
                        default_value = split[3]
                    else:
                        default_value = None
                    final_text = []
                    for i in range(len(codes)):
                        if codes[i] in r[0].variables:
                            final_text.append(text[i])
                    if len(final_text) > 0:
                        dict_row[k] = " ".join(final_text)
                    else :
                        dict_row[k] = default_value

                elif "code_value" == form_var.split("$")[0]:
                    code = form_var.split("$")[1]
                    if code in r[0].variables:
                        dict_row[k] = r[0].variables[code]
                    else:
                        dict_row[k] = None
                elif "value" == form_var.split(":")[0]:
                    dict_row[k] = form_var.split(":")[1]
                else:
                    if form_var in r[1].data:
                        dict_row[k] = r[1].data[form_var]
                    else:
                        dict_row[k] = None

                if min_translation and k in min_translation:
                    tr_dict = min_translation[k]
                    if dict_row[k] in tr_dict.keys():
                        dict_row[k] = tr_dict[dict_row[k]]
                                         
            dict_rows.append(dict_row)
        #app.logger.warning(str(dict_rows))
        return {"data": dict_rows,
                "keys": return_keys,
                "filename": download_name}


class ExportForm(Resource):
    """
    Export a form. If fields is in the request variable we only include
    those fields. 

    Args:\n
       form: the form to export\n

    Returns:\n
       csv-file\n
    """
    representations = {'text/csv': output_csv}
    decorators = [authenticate]
    
    def get(self, form):
        locations, locs_by_deviceid, regions, districts, devices = all_location_data(
            db.session)
        if "fields" in request.args.keys():
            specified_keys = True
            keys = request.args["fields"].split(",")
        else:
            keys = ["clinic", "region", "district"]
            if form not in form_tables:
                return {"filename": form, "file": io.StringIO()}
            sql = text("SELECT DISTINCT(jsonb_object_keys(data)) from {}".
                       format(form_tables[form].__tablename__))
            result = db.engine.execute(sql)
            for r in result:
                keys.append(r[0])
        f = io.StringIO()
        csv_writer = csv.DictWriter(f, keys, extrasaction='ignore')
        csv_writer.writeheader()
        i = 0
        if form in form_tables.keys():
            results = db.session.query(form_tables[form].data).yield_per(1000)
            dict_rows = []
            for row in results:

                dict_row = row.data
                clinic_id = locs_by_deviceid.get(row.data["deviceid"], None)
                if clinic_id:
                    dict_row["clinic"] = locations[clinic_id].name
                    # Sort out district and region
                    if locations[clinic_id].parent_location in districts:
                        dict_row["district"] = locations[locations[clinic_id]
                                                         .parent_location].name
                        dict_row["region"] = locations[locations[locations[
                            clinic_id].parent_location].parent_location].name
                    elif locations[clinic_id].parent_location in regions:
                        dict_row["district"] = ""
                        dict_row["region"] = locations[locations[clinic_id]
                                                       .parent_location].name
                else:
                    dict_row["clinic"] = ""
                    dict_row["district"] = ""
                    dict_row["region"] = ""
                for key in list(row.data.keys()):
                    if key in keys and key not in dict_row:
                        dict_row[key] = row.data[key]
                dict_rows.append(dict_row)
                if i % 1000 == 0:
                    csv_writer.writerows(dict_rows)
                    dict_rows = []
#                    app.logger.info(i)
                i += 1
            csv_writer.writerows(dict_rows)
            return {"filename": form, "file": f}
