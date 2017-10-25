"""
Data resource for getting Device data
"""
import logging

from flask import current_app
from flask_restful import Resource, abort

from meerkat_api.extensions import db, api
from meerkat_abacus import model
import json

from meerkat_api.authentication import authenticate

from .. import common as c

from meerkat_api.util import rows_to_dicts


class Devices(Resource):
    """
    Get devices in the inventory

    Returns:\n
        devices\n
    """
    decorators = [authenticate]

    def get(self):
        if not current_app.config['DEBUG']:
            logging.warning("api/devices call not implemented for production")
            abort(501, message="Api method not implemented.")
        devices = db.session.query(model.Devices)
        devices_dict = rows_to_dicts(devices)
        if devices_dict:
            device_ids = []
            for item in devices_dict:
                device_ids.append(item["device_id"])
            return_data = c.device_api(url='/device',
                                       data=json.dumps(device_ids))
            return return_data
        else:
            return {"message": "No devices registered"}
api.add_resource(Devices, "/devices")
