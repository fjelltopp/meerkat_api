"""
Locations resource for querying location data
"""
from flask_restful import Resource
from flask import jsonify

from meerkat_api.util import row_to_dict, rows_to_dicts, is_child
from meerkat_api import db, app
from meerkat_abacus import model
from meerkat_abacus.database_util import get_locations



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

    
class LocationTree(Resource):
    """
    Returns a Location tree

    """
    def get(self):
        locs = get_locations(db.session)
        loc = 1
        ret = {loc: {"id": loc, "text": locs[loc].name, "nodes": []}}
        for l in sorted(locs.keys()):
            if is_child(l, loc, locs):
                ret.setdefault(locs[l].parent_location, {"nodes": []})
            ret.setdefault(l, {"nodes": []})
            ret[l].update({"id": l, "text": locs[l].name})
            ret[locs[l].parent_location]["nodes"].append(ret[l])
        return jsonify(ret[loc])


