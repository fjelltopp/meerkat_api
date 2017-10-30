"""
Data resource for getting Device data
"""
import logging

from flask import current_app, jsonify
from flask_restful import Resource, abort
from sqlalchemy import or_

from meerkat_api.extensions import db, api
from meerkat_abacus import model
import json

from meerkat_api.authentication import authenticate

from .. import common as c

from meerkat_api.util import rows_to_dicts, row_to_dict


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


class LocationByDeviceId(Resource):
    """
    Location by device_id

    Args:\n
        device_id: id of a device\n
    Returns:\n
       location: location
    """

    def get(self, device_id):
        locations_deviceid = model.Locations.deviceid
        location_filter = or_(locations_deviceid == device_id,
                              locations_deviceid.startswith("{},".format(device_id)),
                              locations_deviceid.contains(",{},".format(device_id)),
                              locations_deviceid.endswith(",{}".format(device_id)),
                              )
        query = db.session.query(model.Locations).filter(location_filter)
        if query.count() == 0:
            abort(404, message="No location matching deviceid: {!r}".format(device_id))
        else:
            return jsonify(row_to_dict(
                query.one()
            ))


api.add_resource(Devices, "/devices")
# endpoint "/device/<device_id>" is deprecated
api.add_resource(LocationByDeviceId, "/device/<device_id>/location", "/device/<device_id>")
