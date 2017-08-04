"""
Locations resource for querying location data
"""
from flask_restful import Resource
from flask import jsonify, g, request
from sqlalchemy import func
from meerkat_api.authentication import authenticate
from meerkat_api.util import row_to_dict, rows_to_dicts, is_child, get_children
from meerkat_api import db, app
from meerkat_abacus import model
from meerkat_abacus.util import get_locations


class Locations(Resource):
    """
    List all Locations

    Returns:\n
       locations: Locations indexed by location_id
    """
    def get(self):
        return jsonify(
            rows_to_dicts(db.session.query(model.Locations).all(), dict_id="id")
        )


class Location(Resource):
    """
    Location by location_id

    Args:\n
        location_id: id of location\n
    Returns:\n
       location: location
    """
    def get(self, location_id):

        return jsonify(row_to_dict(db.session.query(model.Locations).filter(
            model.Locations.id == location_id).first()))


class DeviceID(Resource):
    """
    Location by device_id

    Args:\n
        location_id: id of location\n
    Returns:\n
       location: location
    """
    def get(self, device_id):

        return jsonify(row_to_dict(db.session.query(model.Locations).filter(
            model.Locations.deviceid == device_id).first()
        ))


class LocationTree(Resource):
    """
    Location Tree

    Args:
       only_case_reports: Only include clinics that submitt case reports
    Returns:
       Returns a location Tree
    """
    decorators = [authenticate]

    def get(self, only_case_reports=True):
        case_type = request.args.get('case_type')
        locs = get_locations(db.session)
        loc = g.allowed_location


        ret = {loc: {"id": loc, "text": locs[loc].name, "nodes": []}}
        for l in sorted(locs.keys()):
            if l >= loc and is_child(loc, l, locs):
                if not only_case_reports or (locs[l].case_report == 1 or not locs[l].deviceid):
                    if is_child(l, loc, locs):
                        ret.setdefault(locs[l].parent_location, {"nodes": []})
                    # Filter by case type, if case type is specified.
                    if (not case_type or not locs[l].level == 'clinic' or
                       str(locs[l].case_type).strip() == case_type):
                        ret.setdefault(l, {"nodes": []})
                        ret[l].update({"id": l, "text": locs[l].name})
                        ret[locs[l].parent_location]["nodes"].append(ret[l])

        # Recursively clean any branches without clinics in them.
        def clean(tree):
            for child in reversed(tree['nodes']):
                clean(child)
                if not (child['nodes'] or locs[child['id']].level == 'clinic'):
                    tree['nodes'].remove(child)
        clean(ret[loc])

        return jsonify(ret[loc])


class TotClinics(Resource):
    """
    Returns the number of clinics below location_id in the location tree
    Args:
        location_id
    Returns:
        number of clinics
    """
    def get(self, location_id, clinic_type=None):
        locs = get_locations(db.session)
        children = get_children(location_id, locs)
        if clinic_type:
            res = db.session.query(func.count(model.Locations.id)).filter(
                model.Locations.id.in_(children),
                model.Locations.case_report == 1,
                model.Locations.clinic_type==clinic_type).first()
        else:
            res = db.session.query(func.count(model.Locations.id)).filter(
                model.Locations.id.in_(children),
                model.Locations.case_report == 1).first()

        return {"total": res[0]}
