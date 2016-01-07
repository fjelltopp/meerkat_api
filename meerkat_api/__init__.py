"""
meerkat_api.py

Root Flask app for the Meerkat API.
"""
from flask import Flask
from flask.json import JSONEncoder
from flask.ext.sqlalchemy import SQLAlchemy
from flask_restful import Api
from datetime import datetime

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

api.add_resource(EpiWeek, "/epi_week",
                 "/epi_week/<date>")
api.add_resource(EpiWeekStart, "/epi_week_start/<year>/<epi_week>")

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
api.add_resource(MapVariable, "/map/<variable_id>")
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

api.add_resource(PublicHealth, "/reports/public_health/<location>")
api.add_resource(CdReport, "/reports/cd_report/<location>")

@app.route('/')
def hello_world():
    return "WHO"
