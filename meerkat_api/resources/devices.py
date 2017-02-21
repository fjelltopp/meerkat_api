"""
Data resource for getting Device data
"""
from flask_restful import Resource

from meerkat_api import db, app
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


        
        devices = db.session.query(model.Devices)
        devices_dict=rows_to_dicts(devices)
        if devices_dict:
            device_ids=[]
            for item in devices_dict:
                device_ids.append(item["device_id"])
            return_data = c.device_api(url='/mob', data=json.dumps(device_ids))
            return return_data
        else:
            return {"message":"No devices registered"}
