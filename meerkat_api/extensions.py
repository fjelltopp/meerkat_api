from flask_sqlalchemy import SQLAlchemy
from flask import make_response, abort
from flask_restful import Api
import io
from flask import current_app
from meerkat_api import config
import resource
import csv
from raven.contrib.celery import register_signal, register_logger_signal
import celery
import raven

db = SQLAlchemy()
api = Api()

class Celery(celery.Celery):
    def on_configure(self):
        if config.Config.SENTRY_DNS:
            client = raven.Client(config.Config.SENTRY_DNS)
            # register a custom filter to filter out duplicate logs
            register_logger_signal(client)
            # hook into the Celery error handler
            register_signal(client)

            
celery_app = Celery()
celery_app.config_from_object('meerkat_api.config.Config')

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
    current_app.logger.info('Memory usage: %s (kb)' % int(
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
        current_app.logger.info('Memory usage: %s (kb)' % int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        ))
        return resp
    else:
        abort(404)
