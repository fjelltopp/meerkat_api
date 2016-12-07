"""
Data resource for exporting data
"""
from flask_restful import Resource
from flask import request, abort, current_app, abort
from sqlalchemy import or_, text
from sqlalchemy.orm import aliased
from dateutil.parser import parse
from datetime import datetime, timedelta
import json
import uuid
import json, io, csv, logging

from meerkat_api.util import row_to_dict
from meerkat_api import db, app, output_csv
from meerkat_abacus.model import Data, form_tables, DownloadDataFiles
from meerkat_abacus.util import all_location_data
from meerkat_abacus.config import country_config, config_directory
from meerkat_api.resources.variables import Variables
from meerkat_api.resources.epi_week import EpiWeek
from meerkat_api.authentication import authenticate
from meerkat_abacus.task_queue import export_form, export_category, export_data
from meerkat_abacus.util import get_locations, get_locations_by_deviceid, get_links


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


class GetDownload(Resource):
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
            return {"string": res.content, "filename": res.type}
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
