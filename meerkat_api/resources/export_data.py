"""
Data resource for exporting data
"""
from flask_restful import Resource
from flask import request, abort, current_app
from sqlalchemy import or_, text
from dateutil.parser import parse
import json, io, csv, logging

from meerkat_api.util import row_to_dict
from meerkat_api import db, app, output_csv
from meerkat_abacus.model import Data, form_tables, Links
from meerkat_abacus.util import all_location_data
from meerkat_abacus.config import country_config, links
from meerkat_api.resources.variables import Variables
from meerkat_api.resources.epi_week import EpiWeek
from meerkat_api.authentication import require_api_key
from meerkat_abacus.util import get_locations, get_locations_by_deviceid
from meerkat_api.resources.alerts import get_alerts


class Forms(Resource):
    """
    Return a dict of forms with all their columns

    Returns:\n
       forms: dict of forms with all their variables\n
    """
    decorators = [require_api_key]

    def get(self):
        return_data = {}
        for form in form_tables.keys():
            results = db.session.query(form_tables[form]).first()
            if results:
                return_data[form] = list(results.data.keys()) + ["clinic", "district", "region"]
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
    decorators = [require_api_key]

    def get(self, use_loc_ids=False):
        results = db.session.query(Data)
        variables = set()
        locs = get_locations(db.session)
        for row in results:
            variables = variables.union(set(row.variables.keys()))
        fieldnames = ["id", "country", "region", "district", "clinic",
                      "clinic_type", "geolocation", "date", "uuid"] + list(variables)
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


class ExportAlerts(Resource):
    """
    Export all alerts with investigation information as csv file

    Returns:\n
        csv_file: csv file with alert data\n
    """
    representations = {'text/csv': output_csv}
    decorators = [require_api_key]
    
    def get(self):
        alerts = get_alerts({})
        output_dicts = []
        locs_by_deviceid = get_locations_by_deviceid(db.session)
        locs = get_locations(db.session)
        keys = set()
        
        for a in alerts.values():
            output_dict = a["alerts"]
            output_dict["date"] = output_dict["date"].isoformat()
            output_dict.update(output_dict.pop("data"))
            output_dict["clinic"] = locs[output_dict["clinic"]].name
            if "links" in a:
                for link in a["links"]:
                    output_dict[link+"_date"] = a["links"][link]["to_date"].isoformat()
                    for key in a["links"][link]["data"]:
                        if isinstance(a["links"][link]["data"][key], list):
                            output_dict[link + "_"+key] = ";".join(a["links"][link]["data"][key])
                        else:
                            output_dict[link + "_"+key] = a["links"][link]["data"][key]
                            if key == "investigator":
                                output_dict[link + "_"+key] = locs[locs_by_deviceid[a["links"][link]["data"][key]]].name
            keys = keys.union(output_dict.keys())
            output_dicts.append(output_dict)

        return {"data": output_dicts, "keys": keys, "filename": "alerts"}



class ExportCategory(Resource):
    """
    Export cases from case form that matches a category

    We take a variable dictionary of form field name: display_name.
    There are some special commands that can be given in the form field name:

    * icd_name$category will translate an icd code in icd_code to names given by the variables in category

    * clinic,region and district will give this location information

    * field$month, field$year, field$epi_week: will extract the month, year or epi_week from the field

    * alert_links$alert_investigation$field: will get the field in the correpsonding alert_investigation
    
    Args:\n
       category: category to match\n
       variables: variable dictionary\n
    Returns:\n
       csv_file\n
    """
    representations = {'text/csv': output_csv}
    decorators = [require_api_key]
    
    def get(self, category, download_name):
        app.logger.warning( "Export Category Called")

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
        #Set up icd_code_to_name if needed and determine if alert_links are included
        for v in variables:
            return_keys.append(v[1])
            translation_dict[v[1]] = v[0]
            if "alert_link" in v[0]:
                alert = True
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

            if "gen_link$" in v[0]:
                have_links = True
                link_ids.append( v[0].split("$")[1] )

               
        # Sort out alerts
        if alert:
            alerts = get_alerts({})
            link_tables = {}
            for l in links.links:
                link_tables[l["id"]] = l["to_table"]
          
        #Ordered link definitions so we can definitions easily when adding linked data.  
        ordered_links = {}
        for link in links.links:
            ordered_links[link["id"]] = link
        link_ids = set(link_ids)

        # Need to get all the links from the DB first due to speed issues
        if have_links:
            link_data = {}
            for link in link_ids:
                link_def = ordered_links[link]
                table = form_tables[link_def['to_table']]
                links_values = db.session.query(Links.to_id).filter(Links.link_def == link).all()
                to_ids = []
                for l in links_values:
                    to_ids.append(l[0])
                to_data = db.session.query(table).filter(table.uuid.in_(to_ids))
                link_data_by_value = {}
                for d in to_data:
                    link_data_by_value[d.data[link_def["to_column"]]]= d.data
                link_data[link] = link_data_by_value

                
        # DB query, with yield_per(200) for memory reasons
        results = db.session.query(Data,form_tables["case"]).join(form_tables["case"], Data.uuid==form_tables["case"].uuid).filter(
            or_(Data.variables.has_key(key) for key in data_keys)
        ).yield_per(200)
        
        locs = get_locations(db.session)
        dict_rows = []

        #Prepare each row
        for r in results:
            dict_row = {}
            for k in return_keys:
                form_var = translation_dict[k]
                if "icd_name$" in form_var:
                    if r[1].data["icd_code"] in icd_code_to_name[form_var]:
                        dict_row[k] = icd_code_to_name[form_var][r[1].data["icd_code"]]
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
                    link_def = ordered_links[link]
                    if link_data[link]:
                        if r[1].data[link_def['from_column']] in link_data[link]:
                            dict_row[k] = link_data[link][r[1].data[link_def['from_column']]][form_var.split("$")[-1]]
                    else:
                        dict_row[k] = None

                #Mahoosive hack... Might be nice to add a genral "calc" keyword.
                elif "calc$bmi" in form_var:
                    logging.warning(r[1].data)
                    weight = int(r[1].data['results./bmi_weight'])
                    height = int(r[1].data['results./bmi_height'])
                    logging.warning(weight)
                    logging.warning(height)
                    calculation = weight/((height/100)*(height/100))
                    logging.warning(calculation)
                    dict_row[k] = calculation

                elif "alert_link" in form_var:
                    alert_id = r[0].uuid[-country_config["alert_id_length"]:]
                    if alert_id in alerts:
                        link, field = form_var.split("$")[-2:]
                        alert = alerts[alert_id]
                        if "links" in alert:
                            if link in alert["links"]:
                                to_uuid = alert["links"][link]["to_id"]
                                table = form_tables[link_tables[link]]
                                result = db.session.query(table).filter(
                                    table.uuid == to_uuid).one()
                                if field in result.data:
                                    dict_row[k] = result.data[field]
                                else:
                                    dict_row[k] = None
                            else:
                                dict_row[k] = None
                        else:
                            dict_row[k] = None
                    else:
                        dict_row[k] = None
                else:
                    if form_var in r[1].data:
                        dict_row[k] = r[1].data[form_var]
                    else:
                        dict_row[k] = None
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
    decorators = [require_api_key]
    
    def get(self, form):
        locations, locs_by_deviceid, regions, districts, devices = all_location_data(db.session)
        if "fields" in request.args.keys():
            specified_keys = True
            keys = request.args["fields"].split(",")
        else:
            keys = ["clinic", "region", "district"]
            sql = text("SELECT DISTINCT(jsonb_object_keys(data)) from {}".format(form_tables[form].__tablename__))
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
                        dict_row["district"] = locations[locations[clinic_id].parent_location].name
                        dict_row["region"] = locations[locations[locations[clinic_id].parent_location].parent_location].name
                    elif locations[clinic_id].parent_location in regions:
                        dict_row["district"] = ""
                        dict_row["region"] = locations[locations[clinic_id].parent_location].name
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
            return {"filename": form,
                    "file": f}
