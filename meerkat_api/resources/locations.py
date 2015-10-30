"""
Locations resource for querying location data
"""
from flask_restful import Resource
from meerkat_api.util import row_to_dict, rows_to_dicts
from meerkat_api import db
from meerkat_abacus import model


class Locations(Resource):
    """
    list of all locations
    """
    def get(self):
        return rows_to_dicts(db.session.query(model.Locations).all())

class Location(Resource):
    """
    Location by location_id

    Args:
        location_id: id of location
    """
    def get(self, location_id):
        return row_to_dict(db.session.query(model.Locations).filter(
            model.Locations.id == location_id).first())

class GeoJSON(Resource):
    """
    GEOJSON for 
    """
