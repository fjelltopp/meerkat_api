"""
meerkat_api.py

Root Flask app for the Meerkat API.
"""
from flask import Flask, make_response, abort
from flask.json import JSONEncoder
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from datetime import datetime
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
# from werkzeug.contrib.profiler import ProfilerMiddleware
from io import BytesIO
import flask_excel as excel

import io
import csv
import os
import resource
import pyexcel
import logging

# Create the Flask app
app = Flask(__name__)
app.config.from_object('config.Config')
app.config.from_envvar('MEERKAT_API_SETTINGS', silent=True)
if os.environ.get("MEERKAT_API_DB_SETTINGS"):
    app.config["SQLALCHEMY_DATABASE_URL"] = os.environ.get(
        "MEERKAT_API_DB_URL"
    )


db = SQLAlchemy(app)
api = Api(app)


class CustomJSONEncoder(JSONEncoder):
    """
    Custom JSON encoder to encode all datetime objects as ISO fromat
    """
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, WKBElement):
                shp_obj = to_shape(obj)
                if shp_obj.geom_type == "Point":
                    return shp_obj.coords
                if shp_obj.geom_type == "Polygon":
                    return shp_obj.exterior.coords
                else:
                    return None
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)
app.json_encoder = CustomJSONEncoder


@api.representation('text/csv')
def output_csv(data_dict, code, headers=None):
    """
    Function to write data to a csv file. If data is list of dicts we
    use the first element's keys as csv headers. If data is a dict it should
    have a keys key with a list of keys in the correct order. Data should
    then also include a filename and a list of dicts for each row

    Args:
       data: list of dicts with output data or dict with data and keys
       code: Response code
       headers: http headers
    """
    filename = "file"
    out_string = ""
    if data_dict:
        if "data" in data_dict:
            keys = data_dict["keys"]
            filename = data_dict["filename"]
            data = data_dict["data"]
            output = io.StringIO()
            writer = csv.DictWriter(output, keys, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)
            out_string = output.getvalue()
        elif "file" in data_dict:
            output = data_dict["file"]
            filename = data_dict["filename"]
            out_string = output.getvalue()
        elif "string" in data_dict:
            out_string = data_dict["string"]
            filename = data_dict["filename"]
    resp = make_response(out_string, code)
    resp.headers.extend(headers or {
        "Content-Disposition": "attachment; filename={}.csv".format(filename)})
    # To monitor memory usage
    app.logger.info('Memory usage: %s (kb)' % int(
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    ))
    return resp


@api.representation('application/vnd.openxmlformats-'
                    'officedocument.spreadsheetml.sheet')
def output_xls(data, code, headers=None):
    """
    Function to write data to a xls file.

    Args:
       data: StringIO output of xls writer.
       code: Response code
       headers: http headers
    """
    filename = "file"
    out_data = ""
    if data and "data" in data:
        filename = data["filename"]
        out_data = data['data']
        resp = make_response(out_data, code)
        resp.headers.extend(headers or {
            "Content-Disposition": "attachment; filename={}.xlsx".format(
                filename
            )
        })
        # To monitor memory usage
        app.logger.info('Memory usage: %s (kb)' % int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        ))
        return resp
    else:
        abort(404)


# Importing all the resources here to avoid circular imports
from meerkat_api.resources.locations import Location, Locations, LocationTree, TotClinics
from meerkat_api.resources.variables import Variables, Variable
from meerkat_api.resources.data import Aggregate, AggregateYear
from meerkat_api.resources.data import AggregateCategory, Records
from meerkat_api.resources.map import Clinics, MapVariable, IncidenceMap, Shapes
from meerkat_api.resources.alerts import Alert, Alerts, AggregateAlerts
from meerkat_api.resources.explore import QueryVariable, QueryCategory
from meerkat_api.resources.epi_week import EpiWeek, EpiWeekStart
from meerkat_api.resources.completeness import Completeness, NonReporting
from meerkat_api.resources.reports import PublicHealth, CdReport, \
    CdPublicHealth, CdPublicHealthMad, NcdPublicHealth,RefugeePublicHealth, \
    RefugeeCd,RefugeeDetail, Pip, WeeklyEpiMonitoring, Malaria, \
    VaccinationReport, AFROBulletin,\
    NcdReport, NcdReportNewVisits, NcdReportReturnVisits
from meerkat_api.resources.frontpage import KeyIndicators, TotMap, NumAlerts, ConsultationMap, RefugeePage, NumClinics
from meerkat_api.resources.export_data import ExportData, ExportForm, Forms, ExportCategory, GetCSVDownload, GetXLSDownload, GetStatus
from meerkat_api.resources.incidence import IncidenceRate, WeeklyIncidenceRate
from meerkat_api.resources.indicators import Indicators
from meerkat_api.resources.devices import Devices
#from meerkat_api.resources.links import Link, Links



# All urls

# Epi weeks
api.add_resource(EpiWeek, "/epi_week",
                 "/epi_week/<date>")
api.add_resource(EpiWeekStart, "/epi_week_start/<year>/<epi_week>")

# Frontpage
api.add_resource(KeyIndicators, "/key_indicators")
api.add_resource(TotMap, "/tot_map")
api.add_resource(ConsultationMap, "/consultation_map")
api.add_resource(NumAlerts, "/num_alerts")
api.add_resource(NumClinics, "/num_clinics")
api.add_resource(RefugeePage, "/refugee_page")

# Export data
api.add_resource(GetCSVDownload, "/export/getcsv/<uid>")
api.add_resource(GetXLSDownload, "/export/getxls/<uid>")
api.add_resource(GetStatus, "/export/get_status/<uid>")
api.add_resource(ExportData, "/export/data",
                 "/export/data/<use_loc_ids>")
api.add_resource(ExportForm, "/export/form/<form>")
api.add_resource(Forms, "/export/forms")
api.add_resource(ExportCategory,
                 "/export/category/<form_name>/<category>/<download_name>",
                 "/export/category/<form_name>/<category>/<download_name>/<data_type>")

# Location urls
api.add_resource(Locations, "/locations")
api.add_resource(LocationTree, "/locationtree")
api.add_resource(Location, "/location/<location_id>")
api.add_resource(TotClinics, "/tot_clinics/<location_id>")

# Variables
api.add_resource(Variables, "/variables/<category>")
api.add_resource(Variable, "/variable/<variable_id>")

# Aggregate Data
api.add_resource(Aggregate, "/aggregate/<variable_id>/<location_id>")
api.add_resource(AggregateAlerts, "/aggregate_alerts",
                 "/aggregate_alerts/<central_review>")
api.add_resource(AggregateYear,
                 "/aggregate_year/<variable_id>/<location_id>",
                 "/aggregate_year/<variable_id>/<location_id>/<year>")
api.add_resource(AggregateCategory,
                 "/aggregate_category/<category>/<location_id>",
                 "/aggregate_category/<category>/<location_id>/<year>",
                 "/aggregate_category/<category>/<location_id>/<year>/<lim_variable>")
# Alerts
api.add_resource(Alert, "/alert/<alert_id>")
api.add_resource(Alerts, "/alerts")



# Map
api.add_resource(Clinics, "/clinics/<location_id>",
                 "/clinics/<location_id>/<clinic_type>")
api.add_resource(Shapes, "/geo_shapes/<level>")

api.add_resource(MapVariable, "/map/<variable_id>",
                 "/map/<variable_id>/<location>",
                 "/map/<variable_id>/<location>/<end_date>",
                 "/map/<variable_id>/<location>/<end_date>/<start_date>" )
api.add_resource(IncidenceMap, "/incidence_map/<variable_id>")

# IncidenceRate
api.add_resource(
    IncidenceRate,
    "/incidence_rate/<variable_id>/<level>",
    "/incidence_rate/<variable_id>/<level>/<mult_factor>"
)
api.add_resource(
    WeeklyIncidenceRate,
    "/weekly_incidence/<variable_id>/<loc_id>",
    "/weekly_incidence/<variable_id>/<loc_id>/<year>",
    "/weekly_incidence/<variable_id>/<loc_id>/<year>/<mult_factor>"
)


# Explore data
api.add_resource(QueryVariable,
                 "/query_variable/<variable>/<group_by>",
                 "/query_variable/<variable>/<group_by>"
                 "/<start_date>/<end_date>")
api.add_resource(QueryCategory,
                 "/query_category/<group_by1>/<group_by2>",
                 "/query_category/<group_by1>/<group_by2>/<only_loc>",
                 "/query_category/<group_by1>/<group_by2>"
                 "/<start_date>/<end_date>",
                 "/query_category/<group_by1>/<group_by2>"
                 "/<start_date>/<end_date>/<only_loc>")

# Devices
api.add_resource(Devices, "/devices")

# Reports
api.add_resource(PublicHealth, "/reports/public_health/<location>",
                 "/reports/public_health/<location>/<end_date>",
                 "/reports/public_health/<location>/<end_date>/<start_date>")
api.add_resource(NcdReport, "/reports/ncd_report/<location>",
                 "/reports/ncd_report/<location>/<end_date>",
                 "/reports/ncd_report/<location>/<end_date>/<start_date>")
api.add_resource(NcdReportNewVisits, "/reports/ncd_report_new_visits/<location>",
                 "/reports/ncd_report_new_visits/<location>/<end_date>",
                 "/reports/ncd_report_new_visits/<location>/<end_date>/<start_date>")
api.add_resource(NcdReportReturnVisits, "/reports/ncd_report_return_visits/<location>",
                 "/reports/ncd_report_return_visits/<location>/<end_date>",
                 "/reports/ncd_report_return_visits/<location>/<end_date>/<start_date>")
api.add_resource(CdPublicHealth, "/reports/cd_public_health/<location>",
                 "/reports/cd_public_health/<location>/<end_date>",
                 "/reports/cd_public_health/<location>/<end_date>/<start_date>")
api.add_resource(CdPublicHealthMad, "/reports/cd_public_health_mad/<location>",
                 "/reports/cd_public_health_mad/<location>/<end_date>",
                 "/reports/cd_public_health_mad/<location>/<end_date>/<start_date>")
api.add_resource(NcdPublicHealth, "/reports/ncd_public_health/<location>",
                 "/reports/ncd_public_health/<location>/<end_date>",
                 "/reports/ncd_public_health/<location>/<end_date>/<start_date>")
api.add_resource(RefugeePublicHealth, "/reports/refugee_public_health/<location>",
                 "/reports/refugee_public_health/<location>/<end_date>",
                 "/reports/refugee_public_health/<location>/<end_date>/<start_date>")
api.add_resource(RefugeeCd, "/reports/refugee_cd/<location>",
                 "/reports/refugee_cd/<location>/<end_date>",
                 "/reports/refugee_cd/<location>/<end_date>/<start_date>")
api.add_resource(RefugeeDetail, "/reports/refugee_detail/<location>",
                 "/reports/refugee_detail/<location>/<end_date>",
                 "/reports/refugee_detail/<location>/<end_date>/<start_date>")
api.add_resource(CdReport, "/reports/cd_report/<location>",
                 "/reports/cd_report/<location>/<end_date>",
                 "/reports/cd_report/<location>/<end_date>/<start_date>")
api.add_resource(Pip, "/reports/pip/<location>",
                 "/reports/pip/<location>/<end_date>",
                 "/reports/pip/<location>/<end_date>/<start_date>")
api.add_resource(WeeklyEpiMonitoring, "/reports/epi_monitoring/<location>",
                 "/reports/epi_monitoring/<location>/<end_date>",
                 "/reports/epi_monitoring/<location>/<end_date>/<start_date>")
api.add_resource(Malaria, "/reports/malaria/<location>",
                 "/reports/malaria/<location>/<end_date>",
                 "/reports/malaria/<location>/<end_date>/<start_date>")
api.add_resource(VaccinationReport, "/reports/vaccination/<location>",
                 "/reports/vaccination/<location>/<end_date>",
                 "/reports/vaccination/<location>/<end_date>/<start_date>")
api.add_resource(AFROBulletin, "/reports/afro/<location>",
                 "/reports/afro/<location>/<end_date>",
                 "/reports/afro/<location>/<end_date>/<start_date>")

# Misc
api.add_resource(NonReporting, "/non_reporting/<variable>/<location>",
                 "/non_reporting/<variable>/<location>/<exclude>")
api.add_resource(Completeness,
                 "/completeness/<variable>/<location>/<number_per_week>",
                 "/completeness/<variable>/<location>/<number_per_week>/<start_week>",
                 "/completeness/<variable>/<location>/<number_per_week>/<start_week>/<exclude>",
                 "/completeness/<variable>/<location>/<number_per_week>/<start_week>/<exclude>/<weekend>",
                 "/completeness/<variable>/<location>/<number_per_week>/<start_week>/<exclude>/<weekend>/<non_reporting_variable>",
                 "/completeness/<variable>/<location>/<number_per_week>/<start_week>/<exclude>/<weekend>/<non_reporting_variable>/<end_date>")
api.add_resource(Records, "/records/<variable>/<location_id>")

api.add_resource(Indicators, "/indicators/<transforms>/<variables>/<location>")

@app.route('/')
def hello_world():
    return "WHO"
