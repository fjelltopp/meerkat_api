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
from meerkat_abacus.util import get_locations
from meerkat_api.resources.variables import Variables
from meerkat_api.authentication import require_api_key



class Alert(Resource):
    """
    Get alert with alert_id
    
    Args:
        alert_id
    Returns:
        alert
    """
    decorators = [require_api_key]
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
    decorators = [require_api_key]
    def get(self):
        args = request.args
        return jsonify({"alerts":get_alerts(args).values()})


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
        conditions.append(model.Alerts.reason == args["reason"])
    if "location" in args.keys():
        locations = get_locations(db.session)
        children = get_children(int(args["location"]), locations)
        conditions.append(model.Alerts.clinic.in_(children))
    results = db.session.query(model.Alerts, model.Links).outerjoin(
        model.Links,
        model.Alerts.id == model.Links.link_value).filter(*conditions)
    alerts = {}
    for r in results.all():
        if r[0].id not in alerts.keys():
            alerts[r[0].id] = {"alerts": row_to_dict(r[0])}
            if r[1]:
                alerts[r[0].id]["links"] = {r[1].link_def: row_to_dict(r[1])}
        else:
            alerts[r[0].id]["links"][r[1].link_def] = row_to_dict(r[1])
    return alerts
    
class AggregateAlerts(Resource):
    """
    Get alert all alerts
    Returns:
        alerts
    """
    decorators = [require_api_key]
    def get(self):
        args = request.args
        all_alerts = get_alerts(args)
        ret = {}
        for a in all_alerts.values():
            reason = a["alerts"]["reason"]
            if "links" in a:
                if "alert_investigation" in a["links"]:
                    status = a["links"]["alert_investigation"]["data"]["status"]
                else:
                    status = "Pending"
                if "central_review" in a["links"]:
                    status = a["links"]["central_review"]["data"]["status"]
            else:
                status = "Pending"    
            r = ret.setdefault(str(reason), {})
            r.setdefault(status, 0)
            r[status] += 1
        ret["total"] = len(all_alerts)
        return jsonify(ret)
