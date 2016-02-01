"""
Data resource for exporting data
"""
from flask_restful import Resource
from sqlalchemy import or_, extract, func, Integer
from datetime import datetime
from sqlalchemy.sql.expression import cast


from meerkat_api.util import row_to_dict, rows_to_dicts, date_to_epi_week
from meerkat_api import db, app, output_csv
from meerkat_abacus.model import Data, form_tables
from meerkat_abacus.util import epi_week_start_date
from meerkat_api.resources.variables import Variables
from meerkat_api.authentication import require_api_key
from meerkat_abacus.util import get_locations, get_locations_by_deviceid
from meerkat_api.resources.alerts import get_alerts

class ExportData(Resource):
    """
    Export data table from db
    """
    representations = {'text/csv': output_csv}
    decorators = [require_api_key]

    def get(self):
        results = db.session.query(Data)
        i = 0
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
    
class ExportForm(Resource):
    """
    Allows one to export a form,
    Args:
       - form: the form to export
    """
    representations = {'text/csv': output_csv}
    decorators = [require_api_key]
    
    def get(self, form):
        if form in form_tables.keys():
            results = db.session.query(form_tables[form])
            locs_by_deviceid =  get_locations_by_deviceid(db.session)
            locs = get_locations(db.session)
            dict_rows = []
            keys = set()
            for row in results:
                dict_row = row.data
                if row.data["deviceid"] in locs_by_deviceid:
                    dict_row["location"] = locs[locs_by_deviceid[row.data["deviceid"]]].name
                else:
                    dict_row["location"] = ""
                keys = keys.union(dict_row.keys())
                dict_rows.append(dict_row)
        return {"data": dict_rows,
                "keys": keys,
                "filename": form}
