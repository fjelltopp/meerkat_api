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

    Returns:\n
        csv_file: with a row for each row in the data table\n
    """
    decorators = [authenticate]

    def get(self, use_loc_ids=False):

        uid = str(uuid.uuid4())
        export_data.delay(uid, use_loc_ids)
        return uid



class ExportCategory(Resource):
    """
    Export cases from case form that matches a category

    We take a variable dictionary of form field name: display_name.
    There are some special commands that can be given in the form field name:

    * icd_name$category will translate an icd code in icd_code to names given 
       by the variables in category
    * clinic,region and district will give this location information

    * the $translate keyword can be used to translate row values to other ones.
       I.e to change gender from male, female to M, F

    * field$month, field$year, field$epi_week: will extract the month, year
       or epi_week from the field

    * alert_links$alert_investigation$field: will get the field in the c
       orrepsonding alert_investigation

    Args:\n
       category: category to match\n
       variables: variable dictionary\n
    Returns:\n
       csv_file\n
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
    decorators = [authenticate]
    representations = {'text/csv': output_csv}
    
    def get(self, uid):
        res = db.session.query(DownloadDataFiles).filter(
            DownloadDataFiles.uuid == uid).first()
        return {"string": res.content, "filename": res.type}

    
class GetStatus(Resource):
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

    Args:\n
       form: the form to export\n

    Returns:\n
       csv-file\n
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
