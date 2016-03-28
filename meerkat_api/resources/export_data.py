"""
Data resource for exporting data
"""
from flask_restful import Resource
from flask import request, abort
from sqlalchemy import or_, extract, func, Integer
from datetime import datetime
from sqlalchemy.sql.expression import cast
from dateutil.parser import parse
import json

from meerkat_api.util import row_to_dict, rows_to_dicts, date_to_epi_week
from meerkat_api import db, app, output_csv
from meerkat_abacus.model import Data, form_tables
from meerkat_abacus.util import all_location_data
from meerkat_abacus.config import country_config, links
from meerkat_api.resources.variables import Variables
from meerkat_api.authentication import require_api_key
from meerkat_abacus.util import get_locations, get_locations_by_deviceid
from meerkat_api.resources.alerts import get_alerts


class Forms(Resource):
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
    """
    representations = {'text/csv': output_csv}
    decorators = [require_api_key]

    def get(self):
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
            for l in ["country", "region", "district", "clinic"]:
                if dict_row[l]:
                    dict_row[l] = locs[dict_row[l]].name
            dict_row.update(dict_row.pop("variables"))
            dict_rows.append(dict_row)
        return {"data": dict_rows, "keys": fieldnames, "filename": "data"}


class ExportAlerts(Resource):
    """
    Export all alerts with investigation information
    """
    representations = {'text/csv': output_csv}
    decorators = [require_api_key]
    def get(self):
        alerts = get_alerts({})
        output_dicts = []
        locs_by_deviceid =  get_locations_by_deviceid(db.session)
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
                            output_dict[link+"_"+key] = ";".join(a["links"][link]["data"][key])
                        else:
                            output_dict[link+"_"+key] = a["links"][link]["data"][key]
                            if key == "investigator":
                                output_dict[link+"_"+key] = locs[locs_by_deviceid[a["links"][link]["data"][key]]].name
            keys = keys.union(output_dict.keys())
            output_dicts.append(output_dict)

        return {"data": output_dicts, "keys": keys, "filename": "alerts"}



class ExportCategory(Resource):
    """
    Export cases from case form that matches a category

    Args:
       - category: category to match
       - variables: variable dictionary
    """
    representations = {'text/csv': output_csv}
    decorators = [require_api_key]
    
    def get(self, category, download_name):
        if "variables" in request.args.keys():
            variables = json.loads(request.args["variables"])
        else:
            abort(501)
        var = Variables()
        data_vars = var.get(category)
        data_keys = data_vars.keys()
        if len(data_keys) == 0:
            abort(501)
        return_keys = []
        translation_dict = {}
        alert = False

        icd_code_to_name = {}
        for v in variables:
            return_keys.append(v[1])
            translation_dict[v[1]] = v[0]
            if "alert_link" in v[0]:
                alert = True
            if "icd_name$" in v[0]:
                category = v[0].split("$")[1]
                app.logger.info(category)
                icd_name = var.get(category)
                app.logger.info(len(icd_name))
                icd_code_to_name[v[0]] = {}
                for i in icd_name.keys():
                    condition = icd_name[i]["condition"]
                    if "," in condition:
                        codes = condition.split(",")
                    else:
                        codes = [condition]
                    for c in codes:
                        icd_code_to_name[v[0]][c.strip()] = icd_name[i]["name"]
        for key in icd_code_to_name.keys():
            app.logger.info(key,len(icd_code_to_name[key]))
        if alert:
            alerts = get_alerts({})
            link_tables = {}
            for l in links.links:
                link_tables[l["id"]] = l["to_table"]

            
        results = db.session.query(Data,form_tables["case"]).join(form_tables["case"], Data.uuid==form_tables["case"].uuid).filter(
            or_(Data.variables.has_key(key) for key in data_keys)
        ).yield_per(200)
        locs = get_locations(db.session)
        dict_rows = []
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
                    dict_row[k] = locs[r[0].district].name
                elif "$year" in form_var:
                    field = form_var.split("$")[0]
                    if field in r[1].data:
                        dict_row[k] = parse(r[1].data[field]).year
                    else:
                        dict_row[k] = None
                elif "$month" in form_var:
                    field = form_var.split("$")[0]
                    if field in r[1].data:
                        dict_row[k] = parse(r[1].data[field]).month
                    else:
                        dict_row[k] = None
                elif "$epi_week" in form_var:
                    field = form_var.split("$")[0]
                    if field in r[1].data:
                        dict_row[k] = date_to_epi_week(parse(r[1].data[field]))
                    else:
                        dict_row[k] = None
                elif "alert_link" in form_var:
                    alert_id = r[0].uuid[-country_config["alert_id_length"]:]
                    if alert_id in alerts:
                        link, field = form_var.split("$")[-2:]
                        alert = alerts[alert_id]
                        if "links" in alert:
                            if link in alert["links"]:
                                to_uuid = alert["links"][link]["to_id"]
                                table = form_tables[link_tables[link]]
                                result = db.session.query(table).filter(table.uuid == to_uuid).one()
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

        return {"data": dict_rows,
                "keys": return_keys,
                "filename": download_name}
        
    

    
class ExportForm(Resource):
    """
    Allows one to export a form,
    Args:
       - form: the form to export
    """
    representations = {'text/csv': output_csv}
    decorators = [require_api_key]
    
    def get(self, form):
        specified_keys = False
        locations, locs_by_deviceid, regions, districts = all_location_data(db.session)
        if "fields" in request.args.keys():
            specified_keys = True
            keys = request.args["fields"].split(",")

        if form in form_tables.keys():
            results = db.session.query(form_tables[form]).yield_per(200)
            dict_rows = []
            if not specified_keys:
                keys = set(["clinic", "district", "region"])
            i = 0
            for row in results:
                dict_row = {}
                clinic_id = locs_by_deviceid.get(row.data["deviceid"], None)
                if clinic_id:
                    dict_row["clinic"] = locations[clinic_id].name
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
                if not specified_keys:
                    keys = keys.union(row.data.keys())
                for key in list(row.data.keys()):
                    if key in keys and key not in dict_row:
                        dict_row[key] = row.data[key]
                dict_rows.append(dict_row)
                dict_row = {}
            return {"data": dict_rows,
                    "keys": keys,
                    "filename": form}
