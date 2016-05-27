"""
Data resource for getting Alert data
"""
from flask_restful import Resource
from flask import jsonify, request, current_app

from meerkat_api.util import row_to_dict, get_children
from meerkat_api import db
from meerkat_abacus import model
from meerkat_abacus.util import get_locations
from meerkat_api.authentication import require_api_key


class Alert(Resource):
    """
    Get alert with alert_id
    
    Args:\n
        alert_id\n

    Returns:\n
        alert\n
    """
    decorators = [require_api_key]

    def get(self, alert_id):
        result = db.session.query(model.Alerts, model.Links).outerjoin(
            model.Links, model.Alerts.id == model.Links.link_value
        ).filter(model.Alerts.id == alert_id).first()
        if result: 
            return jsonify(row_to_dict(result))
        else:
            return {}


class Alerts(Resource):
    """
    Get alert all alerts

    Returns:\n
        alerts\n
    """
    decorators = [require_api_key]
    
    def get(self):
        args = request.args
        return jsonify({"alerts": get_alerts(args).values()})


def get_alerts(args):
    """
    Gets all alerts where if reason is a key in args we only get alerts with a matching reason. 
    If "location" is in the key we get all alerts from the location or any child clinics. 

    Returns a list of alerts where each element is a dict with {"alerts": alert_info, "links": link_info}
    The link info is the alert investigation

    Args:\n
        args: request args that can include "reason" and "location" as keys. \n

    Returns:\n
       alerts(list): a list of alerts. \n
    """
    conditions = []
    if "reason" in args.keys():
        conditions.append(model.Alerts.reason == args["reason"])
    if "location" in args.keys():
        locations = get_locations(db.session)
        children = get_children(int(args["location"]), locations)
        conditions.append(model.Alerts.clinic.in_(children))
    if "start_date" in args.keys():
        conditions.append( model.Alerts.date >= args["start_date"] )
    if "end_date" in args.keys():
        conditions.append( model.Alerts.date < args["end_date"] )



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
    Aggregates all alerts based on reason and status in the following format:

    {reason: {status_1: Number, status_2: Number}, reason2: .... , total: total_alerts} 

    Returns:\n
        alerts(dict): Aggregagated alerts by reason and status\n
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
                    # We set all alerts without a link to Pending
                    status = "Pending"
                if "central_review" in a["links"]:
                    # For the countries that have a central_review we overwrite the status from the alert_investigation
                    status = a["links"]["central_review"]["data"]["status"]
            else:
                # We set all alerts without a link to Pending
                status = "Pending"
            r = ret.setdefault(str(reason), {})
            r.setdefault(status, 0)
            r[status] += 1
            
        ret["total"] = len(all_alerts)
        return jsonify(ret)
