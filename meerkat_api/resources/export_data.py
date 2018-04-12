"""
Data resource for exporting data
"""
import json
import uuid
import yaml
import logging
from flask import request, redirect, g
from flask_restful import Resource, abort
from meerkat_abacus.model import form_tables, DownloadDataFiles
from meerkat_abacus.config import config as abacus_config
from api_background.export_data import export_category, export_data, export_data_table
from api_background.export_data import export_form, export_week_level
from meerkat_api.extensions import db, output_csv, output_xls, api
from meerkat_api.authentication import authenticate

# Uncomment to run export data during request
# from meerkat_abacus.tasks import app as celery_app
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
        for form in form_tables():
            results = db.session.query(form_tables()[form]).first()
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
        yaml_config = yaml.dump(abacus_config)
        export_data.delay(
            uid, g.allowed_location, use_loc_ids,
            param_config_yaml=yaml_config
        )
        return uid


class ExportWeekLevel(Resource):
    """
    Exports a variable broken down by week and location level.
    If a variable is not submitted as a get arg it returns a 400 HTTP status code.

    Args:
       download_name: Name of downloaded file
       level: Location level
    Returns:
       uuid: Uuid of download data process
    

    """
    decorators = [authenticate]
    
    def get(self, download_name, level):
        if "variable" in request.args.keys():
            variable = json.loads(request.args["variable"])
        else:
            abort(400, message="No variable were submitted")
        uid = str(uuid.uuid4())
        yaml_config = yaml.dump(abacus_config)
        export_week_level.delay(uid, download_name, level,
                                variable,
                                start_date=request.args.get("start_date", None),
                                end_date=request.args.get("end_date", None),
                                language=request.args.get("language", "en"),
                                wide_data_format=int(request.args.get("wide_data_format", False)),
                                param_config_yaml=yaml_config)
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
            abort(400, message="No variables were submitted")
        if "group_by" in request.args.keys():
            group_by = json.loads(request.args["group_by"])
        else:
            abort(400, message="No Group by variables were submitted")

        location_conditions = []

        if "location_conditions" in request.args.keys():
            location_conditions = json.loads(request.args["location_conditions"])
            
        uid = str(uuid.uuid4())
        yaml_config = yaml.dump(abacus_config)
        export_data_table.delay(uid, download_name,
                                restrict_by, variables, group_by,
                                location_conditions=location_conditions,
                                start_date=request.args.get("start_date", None),
                                end_date=request.args.get("end_date", None),
                                wide_data_format=int(request.args.get("wide_data_format", False)),
                                param_config_yaml=yaml_config)
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
            abort(400, message="No variables were submitted")
        language = request.args.get("language", "en")
        yaml_config = yaml.dump(abacus_config)
        export_category.delay(
            uid, form_name, category, download_name,
            variables, data_type, g.allowed_location,
            start_date=request.args.get("start_date", None),
            end_date=request.args.get("end_date", None),
            language=language,
            param_config_yaml=yaml_config
        )
        return uid


class ExportDataResource(Resource):
    """
    Validates if a resource is available in the system to be downloaded.
    If resource is not found aborts with a http code 404.
    If generation failed aborts with a http code 500.

    Args:
        uuid of download
    Returns:
        a record with matching DownloadDataFiles
    """

    def get_download_data_file(self, uid):
        result = db.session.query(DownloadDataFiles).filter(
            DownloadDataFiles.uuid == uid).first()
        self.__abort_if_resource_not_exists(result, uid)
        return result

    @staticmethod
    def abort_if_resource_generation_failed(download_data_file, uid):
        if download_data_file.status == 1.0 and download_data_file.success != 1:
            abort(500, message="Generation of resource with uid: {} failed. Please try again.".format(uid))

    @staticmethod
    def abort_if_resource_generation_still_in_progress(download_data_file, uid):
        if download_data_file.status != 1.0:
            message_template = "Generation of resource with uid: {} still in progress. Please try again later."
            abort(206, message=(message_template).format(uid))

    @staticmethod
    def __abort_if_resource_not_exists(download_data_file, uid):
        if not download_data_file:
            abort(404, message="Resource with uid:{} doesn't exist".format(uid))


class GetCSVDownload(ExportDataResource):
    """
    serves a pregenerated csv file

    Args:
       uuid: uuid of download
    """
    decorators = [authenticate]
    representations = {'text/csv': output_csv}

    def get(self, uid):
        result = self.get_download_data_file(uid)
        self.abort_if_resource_generation_still_in_progress(result, uid)
        self.abort_if_resource_generation_failed(result, uid)
        return redirect("/exported_data/" + uid + "/" + result.type + ".csv")


class GetXLSDownload(ExportDataResource):
    """
    Serves a pregenerated xls file

    Args:
       uuid: uuid of download
    """
    decorators = [authenticate]
    representations = {('application/vnd.openxmlformats-'
                        'officedocument.spreadsheetml.sheet'): output_xls}

    def get(self, uid):
        result = self.get_download_data_file(uid)
        self.abort_if_resource_generation_still_in_progress(result, uid)
        self.abort_if_resource_generation_failed(result, uid)
        return redirect("/exported_data/" + uid + "/" + result.type + ".xlsx")


class GetStatus(ExportDataResource):
    """
    Checks the current status of the generation

    Args:
       uuid: uuid to check status for
    """
    decorators = [authenticate]

    def get(self, uid):
        result = self.get_download_data_file(uid)
        return {"status": result.status, "success": result.success}


class ExportForm(Resource):
    """
    Export a form. If fields is in the request variable we only include
    those fields.

    Starts background export

    Args:\n
       form: the form to export\n

    """
    decorators = [authenticate]

    def get(self, form):
        uid = str(uuid.uuid4())
        if "fields" in request.args.keys():
            fields = request.args["fields"].split(",")
        else:
            fields = None
        yaml_config = yaml.dump(abacus_config)
        export_form.delay(
            uid, form, g.allowed_location, fields,
            param_config_yaml=yaml_config
        )
        return uid


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
api.add_resource(ExportDataTable,
                 "/export/data_table/<download_name>/<restrict_by>")
api.add_resource(ExportWeekLevel,
                 "/export/week_level/<download_name>/<level>")
