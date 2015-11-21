"""
Data resource for querying data
"""
from flask_restful import Resource
from flask import jsonify, request
from sqlalchemy import or_, extract, func, Integer
from datetime import datetime
from sqlalchemy.sql.expression import cast

from meerkat_api.util import row_to_dict, rows_to_dicts, date_to_epi_week, get_children
from meerkat_api import db, app
from meerkat_abacus import model
from meerkat_abacus.database_util import get_locations
from meerkat_api.resources.variables import Variables



class Alert(Resource):
    """
    Get alert with alert_id
    
    Args:
        alert_id
    Returns:
        alert
    """
    def get(self, alert_id):
        result = db.session.query(model.Alerts, model.Links).outerjoin(
            model.Links, model.Alerts.id == model.Links.link_value).filter(
                model.Alerts.id == alert_id)
        return jsonify(row_to_dict(result.first()))


class Alerts(Resource):
    """
    Get alert with alert_id
    
    Args:
        alert_id
    Returns:
        alert
    """
    def get(self):
        args = request.args
        conditions = []
        if "reason" in args.keys():
            conditions.append(model.Alerts.reason == int(args["reason"]))
        if "location" in args.keys():
            locations = get_locations(db.session)
            children = get_children(int(args["location"]), locations)
            conditions.append(model.Alerts.clinic.in_(children))
#        conditions.append(model.Links.link_def == 1)
        results = db.session.query(model.Alerts, model.Links).outerjoin(
            model.Links,
            model.Alerts.id == model.Links.link_value).filter(*conditions)
        return jsonify(alerts=rows_to_dicts(results.all()))
