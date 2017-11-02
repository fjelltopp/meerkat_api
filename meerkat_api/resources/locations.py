"""
Locations resource for querying location data
"""
import json

from flask import jsonify, g, request
from flask_restful import Resource, abort, reqparse
from sqlalchemy import func, or_

from meerkat_abacus import model
from meerkat_abacus.util import get_locations
from meerkat_api.authentication import authenticate
from meerkat_api.extensions import db, api
from meerkat_api.util import row_to_dict, rows_to_dicts, is_child, get_children


class Locations(Resource):
    """
    List all Locations

    Params:\n
        deviceId: return locations for a given deviceId

    Returns:\n
       locations: Locations indexed by location_id
    """

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('deviceId')
        args = parser.parse_args()
        device_id = args.get('deviceId')

        location_query = db.session.query(model.Locations)

        filter_conditions = []
        if device_id:
            filter_conditions.append(_get_by_device_id_filter(device_id))

        return jsonify(rows_to_dicts(
            location_query.filter(*filter_conditions).all(),
            dict_id="id"
        ))


class Location(Resource):
    """
    Location by location_id

    Args:\n
        location_id: id of location\n
    Returns:\n
       location: location
    """

    def get(self, location_id):
        return jsonify(row_to_dict(
            db.session.query(model.Locations).filter(
                model.Locations.id == location_id
            ).first()
        ))


class LocationTree(Resource):
    """
    Location Tree

    Accepts optional GET args:
        inc_case_types - A JSON list of case types to filter the location Tree
            by. A location is only included in the tree if there is an
            intersection between this list and the locations case_type list.
            Used when viewing e.g. PIP data - the user is only interested in
            viewing clinics/locations that are actually submitting PIP data.
        exc_case_types - A JSON list of case types to filter the location tree
            by.  In a similar, but opposite, way to inc_case_types, a location
            is only included in the tree if there is NO intersection between
            this list and the location's case_type list.

    Args:
       only_case_reports: Only include clinics that submit case reports

    Returns:
       Returns a location Tree
    """
    decorators = [authenticate]

    def get(self, only_case_reports=True):
        # Load filters supplied in GET args
        inc_case_types = json.loads(request.args.get('inc_case_types', '[]'))
        exc_case_types = json.loads(request.args.get('exc_case_types', '[]'))

        # Get location data from db and any access restrictions set by auth
        locs = get_locations(db.session)
        loc = g.allowed_location

        # Start drawing the tree
        ret = {loc: {"id": loc, "text": locs[loc].name, "nodes": []}}
        for l in sorted(locs.keys()):
            if l >= loc and is_child(loc, l, locs):
                if not only_case_reports or (locs[l].case_report == 1 or
                                                 not locs[l].deviceid):
                    if is_child(l, loc, locs):
                        ret.setdefault(locs[l].parent_location, {"nodes": []})

                    # Factor out the process of adding a location to the tree
                    def add_loc():
                        ret.setdefault(l, {"nodes": []})
                        ret[l].update({"id": l, "text": locs[l].name})
                        ret[locs[l].parent_location]["nodes"].append(ret[l])

                    # Determine if the location matches incl and excl criteria
                    loc_case_types = set()
                    if locs[l].case_type:
                        loc_case_types = set(locs[l].case_type)
                    inc = bool(set(inc_case_types) & loc_case_types)
                    exc = set(exc_case_types) >= loc_case_types

                    # Add the location if it is not a clinic
                    if not locs[l].level == 'clinic':
                        add_loc()
                    # Otherwise add the location if no filters provided at all
                    elif not inc_case_types and not exc_case_types:
                        add_loc()
                    # Otherwise if both filters are provided, only add loc if
                    # ...inclusion criteria is met but not exclusion criteria
                    elif inc_case_types and exc_case_types:
                        if inc and not exc:
                            add_loc()
                    # Otherwise add loc if incl criteria specified and met
                    elif inc_case_types and inc:
                        add_loc()
                    # Otherwise add loc if excl criteria specified and not met
                    elif exc_case_types and not exc:
                        add_loc()

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
                model.Locations.clinic_type == clinic_type).first()
        else:
            res = db.session.query(func.count(model.Locations.id)).filter(
                model.Locations.id.in_(children),
                model.Locations.case_report == 1).first()

        return {"total": res[0]}


class LocationByDeviceId(Resource):
    """
    === Deprecated ===
    Use Locations with "/locations?deviceId=<device_id> instead.
    Location by device_id

    Args:\n
        device_id: id of a device\n
    Returns:\n
       location: location
    """

    def get(self, device_id):
        location_filter = _get_by_device_id_filter(device_id)
        query = db.session.query(model.Locations).filter(location_filter)
        if query.count() == 0:
            abort(404, message="No location matching deviceid: {!r}".format(device_id))
        else:
            return jsonify(row_to_dict(
                query.one()
            ))


def _get_by_device_id_filter(device_id):
    locations_deviceid = model.Locations.deviceid
    location_filter = or_(locations_deviceid == device_id,
                          locations_deviceid.startswith("{},".format(device_id)),
                          locations_deviceid.contains(",{},".format(device_id)),
                          locations_deviceid.endswith(",{}".format(device_id)))
    return location_filter


api.add_resource(Locations, "/locations")
api.add_resource(LocationTree, "/locationtree")
api.add_resource(Location, "/location/<location_id>")
# endpoint "/device/<device_id>" is deprecated use /locations?deviceId=<device_id> instead
api.add_resource(LocationByDeviceId, "/device/<device_id>")
api.add_resource(TotClinics, "/tot_clinics/<location_id>")
