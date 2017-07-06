"""
Data resource for exporting data
"""
from flask_restful import Resource
from flask import request, redirect, g
import json
import uuid

from meerkat_api import db, output_csv, output_xls
from meerkat_abacus.model import form_tables, DownloadDataFiles
from meerkat_api.authentication import authenticate
from meerkat_abacus.task_queue import export_form
from meerkat_abacus.task_queue import export_category, export_data, export_data_table

# Uncomment to run export data during request
# from meerkat_abacus.task_queue import app as celery_app
# celery_app.conf.CELERY_ALWAYS_EAGER = True


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

    Starts generation of data file

    Args:
       use_loc_ids: If we use names are location ids
    Returns:\n
       uuid

    """
    decorators = [authenticate]

    def get(self, use_loc_ids=False):

        uid = str(uuid.uuid4())
        export_data.delay(uid, g.allowed_location, use_loc_ids)
        return uid


class ExportDataTable(Resource):
    """
    Export data table with aggregated data from db

    Starts generation of data file

    Args:
       use_loc_ids: If we use names are location ids
    Returns:\n
       uuid

    """
    decorators = [authenticate]

    def get(self, download_name, restrict_by):
        if "variables" in request.args.keys():
            variables = json.loads(request.args["variables"])
        else:
            return "No variables"
        if "group_by" in request.args.keys():
            group_by = json.loads(request.args["group_by"])
        else:
            return "No variables"

        location_conditions = []

        if "location_conditions" in request.args.keys():
            location_conditions = json.loads(request.args["location_conditions"])

        uid = str(uuid.uuid4())
        export_data_table.delay(uid, download_name,
                                restrict_by, variables, group_by,
                                location_conditions=location_conditions)
        return uid


class ExportCategory(Resource):
    """
    Export cases from case form that matches a category

    Starts generation of data file
    Args:\n
       category: category to match\n
       variables: variable dictionary\n
    Returns:\n
       uuid
    """
    decorators = [authenticate]

    def get(self, form_name, category, download_name, data_type=None):
        uid = str(uuid.uuid4())
        if "variables" in request.args.keys():
            variables = json.loads(request.args["variables"])
        else:
            return "No variables"
        language = request.args.get("language", "en")
        export_category.delay(uid, form_name, category,
                              download_name, variables, data_type,
                              g.allowed_location,
                              start_date=request.args.get("start_date", None),
                              end_date=request.args.get("end_date", None),
                              language=language)
        return uid


class GetCSVDownload(Resource):
    """
    serves a pregenerated csv file

    Args:
       uuid: uuid of download
    """
    decorators = [authenticate]
    representations = {'text/csv': output_csv}

    def get(self, uid):
        res = db.session.query(DownloadDataFiles).filter(
            DownloadDataFiles.uuid == uid).first()
        if res:
            return redirect("/exported_data/" + uid + "/" + res.type + ".csv")
        return {"url": "", "filename": "missing"}


class GetXLSDownload(Resource):
    """
    Serves a pregenerated xls file

    Args:
       uuid: uuid of download
    """
    decorators = [authenticate]
    representations = {('application/vnd.openxmlformats-'
                        'officedocument.spreadsheetml.sheet'): output_xls}

    def get(self, uid):
        res = db.session.query(DownloadDataFiles).filter(
            DownloadDataFiles.uuid == uid
        ).first()
        if res:
            return redirect("/exported_data/" + uid + "/" + res.type + ".xlsx")
        return {"url": "", "filename": "missing"}


class GetStatus(Resource):
    """
    Checks the current status of the generation

    Args:
       uuid: uuid to check status for
    """
    decorators = [authenticate]

    def get(self, uid):

        results = db.session.query(DownloadDataFiles).filter(
            DownloadDataFiles.uuid == uid).first()
        if results:
            return {"status": results.status, "success": results.success}
        else:
            return None


class ExportForm(Resource):
    """
    Export a form. If fields is in the request variable we only include
    those fields.

    Starts background export

    Args:\n
       form: the form to export\n

    """
    # representations = {'text/csv': output_csv}
    decorators = [authenticate]

    def get(self, form):
        uid = str(uuid.uuid4())
        if "fields" in request.args.keys():
            fields = request.args["fields"].split(",")
        else:
            fields = None
        export_form.delay(uid, form, g.allowed_location, fields)
        return uid
