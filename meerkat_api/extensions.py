from flask_sqlalchemy import SQLAlchemy
from flask import make_response, abort
from flask_restful import Api
import io
from flask import current_app
import resource
import csv
db = SQLAlchemy()
api = Api()


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
