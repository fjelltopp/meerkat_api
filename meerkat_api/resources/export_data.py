"""
Data resource for exporting data
"""
from flask_restful import Resource
from flask import request
import json
import uuid

from meerkat_api import db, output_csv, output_xls
from meerkat_abacus.model import form_tables, DownloadDataFiles
from meerkat_api.authentication import authenticate
from meerkat_abacus.task_queue import export_form, export_category, export_data


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
        export_data.delay(uid, use_loc_ids)
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

    def get(self, form_name, category, download_name):
        uid = str(uuid.uuid4())
        if "variables" in request.args.keys():
            variables = json.loads(request.args["variables"])
        else:
            return "No variables"
        export_category.delay(uid, form_name, category,
                              download_name, variables)
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
            return {"string": res.csvcontent, "filename": res.type}
        return {"string": "", "filename": "missing"}


class GetXLSDownload(Resource):
    """
    Serves a pregenerated xls file

    Args:
       uuid: uuid of download
    """
    decorators = [authenticate]
    representations = {'text/xls': output_xls}

    def get(self, uid):
        res = db.session.query(DownloadDataFiles).filter(
            DownloadDataFiles.uuid == uid
        ).first()
        if res:
            return {"string": res.xlscontent, "filename": res.type}
        return {"string": "", "filename": "missing"}


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
        export_form.delay(uid, form, fields)
        return uid
