"""
Data resource for getting Device data
"""

import json
import logging
from collections import defaultdict

from flask import current_app
from flask.json import jsonify
from flask_restful import Resource, abort, reqparse
from sqlalchemy import and_

from meerkat_abacus import model
from meerkat_api.authentication import authenticate
from meerkat_api.extensions import db, api
from meerkat_api.resources.locations import Location
from meerkat_api.util import rows_to_dicts, get_children
from meerkat_abacus.util import get_locations
from .. import common as c


class Devices(Resource):
    """
    Get devices in the inventory

    Returns:\n
        devices\n
    """
    decorators = [authenticate]

    def get(self):
        if current_app.config['PRODUCTION']:
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

def not_implemented_operator():
    raise NotImplementedError


sql_alchemy_comparators_dict = defaultdict(not_implemented_operator)
sql_alchemy_comparators_dict.update({
    "eq": "__eq__",
    "ge": "__ge__",
    "le": "__le__",
    "ne": "__ne__",
    "lt": "__lt__",
    "gt": "__gt__",
})


class DeviceResourceBase(Resource):
    def get_sql_alchemy_filters(self, filters):
        sql_alchemy_filters = []
        if filters:
            for a_filter in filters:
                if len(a_filter.split(':')) != 3:
                    abort(404, message="Incorrect filter: {}".format(a_filter))
                else:
                    sql_alchemy_filter = self.create_filter_from_parameter(a_filter)
                    sql_alchemy_filters.append(sql_alchemy_filter)
        return sql_alchemy_filters

    @classmethod
    def parse_filter(cls, filter_parameter):
        column_name, comparator, value = filter_parameter.split(':')
        parsed_comparator = sql_alchemy_comparators_dict[comparator]
        return column_name, parsed_comparator, value

    @classmethod
    def create_filter_from_parameter(cls, filter_parameter):
        column_name, comparator, value = cls.parse_filter(filter_parameter)
        sql_alch_column = getattr(model.Data, column_name)
        sql_alch_comparator = getattr(sql_alch_column, comparator)
        return sql_alch_comparator(value)

    @classmethod
    def _get_variable_count_for_deivce_id(cls, device_id, variable, sql_alchemy_filters):
        count = db.session.query(model.Data.device_id, model.Data.date, model.Data.variables) \
            .filter(and_(model.Data.variables.has_key(variable), model.Data.device_id == device_id)) \
            .filter(and_(*sql_alchemy_filters)) \
            .count()
        result = {"deviceId": device_id, "variable": variable, "submissionsCount": count}
        return result


class DeviceSubmissions(DeviceResourceBase):
    decorators = [authenticate]

    def get(self, device_id, variable_id):
        parser = reqparse.RequestParser()
        parser.add_argument('filter', action='append')
        args = parser.parse_args()
        filters = args['filter']

        sql_alchemy_filters = self.get_sql_alchemy_filters(filters)
        result = self._get_variable_count_for_deivce_id(device_id, variable_id, sql_alchemy_filters)
        return jsonify(result)


class DeviceSubmissionsForLocation(DeviceResourceBase):
    decorators = [authenticate]

    def get(self, variable_id):
        parser = reqparse.RequestParser()
        parser.add_argument('filter', action='append')
        parser.add_argument('location', required=True, help="Please, provide a location parameter.")
        args = parser.parse_args()
        filters = args['filter']
        parent_id = int(args['location'])
        all_locations_dict = get_locations(db.session)
        children_location_ids = get_children(parent_id, all_locations_dict)
        results_by_location = []
        for location_id in children_location_ids:
            result = []
            location = Location.get_location_by_id(location_id)
            sql_alchemy_filters = self.get_sql_alchemy_filters(filters)

            if location.deviceid:
                device_ids = location.deviceid.split(',')
                for device_id in device_ids:
                    result.append(self._get_variable_count_for_deivce_id(device_id, variable_id, sql_alchemy_filters))
            results_by_location.append({
                "clinicId": location_id,
                "deviceSubmissions": result
            })
        return jsonify({
            "parentLocationId": parent_id,
            "clinicCount": len(children_location_ids),
            "clinicSubmissions": results_by_location
        })


api.add_resource(Devices, "/devices")

api.add_resource(DeviceSubmissions, "/device/<device_id>/submissions/<variable_id>")
api.add_resource(DeviceSubmissionsForLocation, "/devices/submissions/<variable_id>")
