"""
meerkat_api.py

Root Flask app for the Meerkat API.
"""
from flask import Flask
from flask.json import JSONEncoder
from flask.ext.sqlalchemy import SQLAlchemy
from flask_restful import Api
from datetime import datetime
import types
import io
import csv


from meerkat_abacus import config
from meerkat_abacus import model

# Create the Flask app
app = Flask(__name__)
app.config.from_object('config.Development')
app.config.from_envvar('MEERKAT_API_SETTINGS', silent=True)
db = SQLAlchemy(app)
api = Api(app)

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.isoformat()
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)
app.json_encoder = CustomJSONEncoder


@api.representation('text/csv')
def output_csv(data, code, headers=None):
    filename = "file"
    data_is_list = isinstance(data, list)
    keys = data[0].keys() if data_is_list else data.keys()
    if isinstance(data, dict) and "keys" in data.keys():
        keys = data["keys"]
        filename = data["filename"]
        data = data["data"]
        data_is_list = True

    output = io.StringIO()
    writer = csv.DictWriter(output, keys, extrasaction="ignore")
    writer.writeheader()
    if data_is_list:
        writer.writerows(data)
    else:
        writer.writerow(data)

    resp = app.make_response(str(output.getvalue()))
    resp.headers.extend(headers or {
        "Content-Disposition": "attachment; filename={}.csv".format(filename)})

    return resp

from meerkat_api.resources.locations import Location, Locations, LocationTree, TotClinics
from meerkat_api.resources.variables import Variables, Variable
from meerkat_api.resources.data import Aggregate, AggregateYear
from meerkat_api.resources.data import AggregateCategory
from meerkat_api.resources.map import Clinics, MapVariable
from meerkat_api.resources.alerts import Alert, Alerts, AggregateAlerts
from meerkat_api.resources.explore import QueryVariable, QueryCategory
from meerkat_api.resources.epi_week import EpiWeek, EpiWeekStart
from meerkat_api.resources.completeness import Completeness
from meerkat_api.resources.reports import PublicHealth, CdReport
from meerkat_api.resources.frontpage import KeyIndicators, TotMap, NumAlerts, ConsultationMap
from meerkat_api.resources.export_data import ExportData, ExportForm, ExportAlerts
from meerkat_api.authentication import require_api_key

api.add_resource(EpiWeek, "/epi_week",
                 "/epi_week/<date>")
api.add_resource(EpiWeekStart, "/epi_week_start/<year>/<epi_week>")
api.add_resource(KeyIndicators, "/key_indicators")
api.add_resource(TotMap, "/tot_map")
api.add_resource(ConsultationMap, "/consultation_map")
api.add_resource(NumAlerts, "/num_alerts")

api.add_resource(ExportData, "/export/data")
api.add_resource(ExportForm, "/export/form/<form>")
api.add_resource(ExportAlerts, "/export/alerts")

api.add_resource(Locations, "/locations")
api.add_resource(LocationTree, "/locationtree")
api.add_resource(Location, "/location/<location_id>")
api.add_resource(TotClinics, "/tot_clinics/<location_id>")
api.add_resource(Variables, "/variables/<category>")
api.add_resource(Variable, "/variable/<variable_id>")
api.add_resource(Aggregate, "/aggregate/<variable_id>/<location_id>")
api.add_resource(Alert, "/alert/<alert_id>")
api.add_resource(Alerts, "/alerts")
api.add_resource(AggregateAlerts, "/aggregate_alerts")
api.add_resource(AggregateYear,
                 "/aggregate_year/<variable_id>/<location_id>",
                 "/aggregate_year/<variable_id>/<location_id>/<year>")
api.add_resource(AggregateCategory,
                 "/aggregate_category/<category>/<location_id>",
                 "/aggregate_category/<category>/<location_id>/<year>")
api.add_resource(Clinics, "/clinics/<location_id>")
api.add_resource(MapVariable, "/map/<variable_id>",
                 "/map/<variable_id>/<location>")

api.add_resource(QueryVariable,
                 "/query_variable/<variable>/<group_by>",
                 "/query_variable/<variable>/<group_by>"
                 "/<start_date>/<end_date>")
api.add_resource(QueryCategory,
                 "/query_category/<group_by1>/<group_by2>",
                 "/query_category/<group_by1>/<group_by2>"
                 "/<start_date>/<end_date>")
api.add_resource(Completeness, "/completeness/<variable>/<number_per_week>")

#Reports

api.add_resource(PublicHealth, "/reports/public_health/<location>",
                 "/reports/public_health/<location>/<end_date>",
                 "/reports/public_health/<location>/<end_date>/<start_date>")
api.add_resource(CdReport, "/reports/cd_report/<location>",
                 "/reports/cd_report/<location>/<end_date>",
                 "/reports/cd_report/<location>/<end_date>/<start_date>")


@app.route('/')
def hello_world():
    return "WHO"


@app.route('/test-authentication')
@require_api_key
def test_authentication():
    return "Authenticated"
