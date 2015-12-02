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
    Get alert all alerts
    Returns:
        alerts
    """
    def get(self):
        args = request.args
        return jsonify(alerts=rows_to_dicts(get_alerts(args)))


def get_alerts(args):
    """
    Gets all alerts where reason and location are satisified

    Args:
        args: request args
    Returns:
       alerts(list)
    """
    conditions = []
    if "reason" in args.keys():
        conditions.append(model.Alerts.reason == int(args["reason"]))
    if "location" in args.keys():
        locations = get_locations(db.session)
        children = get_children(int(args["location"]), locations)
        conditions.append(model.Alerts.clinic.in_(children))
    results = db.session.query(model.Alerts, model.Links).outerjoin(
        model.Links,
        model.Alerts.id == model.Links.link_value).filter(*conditions)
    return results.all()
    
class AggregateAlerts(Resource):
    """
    Get alert all alerts
    Returns:
        alerts
    """
    def get(self):
        args = request.args
        all_alerts = get_alerts(args)
        ret = {}
        for a in all_alerts:
            reason = a[0].reason
            if a[1]:
                status = a[1].data["status"]
            else:
                status = "Pending"
            r = ret.setdefault(str(reason), {})
            r.setdefault(status, 0)
            r[status] += 1
        ret["total"] = len(all_alerts)
        return jsonify(ret)
