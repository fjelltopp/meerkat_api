"""
Data resource for getting Device data
"""
from flask_restful import Resource

from meerkat_api import db
from meerkat_abacus import model

from meerkat_api.util import rows_to_dicts

class Devices(Resource):
    """
    Get devices in the inventory

    Returns:\n
        devices\n
    """
    #decorators = [authenticate]

    def get(self):
        result = db.session.query(model.Devices)
        if result:
        	return rows_to_dicts(result)
        else:
        		return {}