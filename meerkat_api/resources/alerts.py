"""
Data resource for getting Alert data
"""
from flask_restful import Resource
from flask import jsonify, request, current_app

from meerkat_api.util import row_to_dict, rows_to_dicts, get_children
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
        result = db.session.query(model.Data).filter(model.Data.variables["alert_id"].astext == alert_id).first()
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
        return jsonify({"alerts": get_alerts(args)})


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
    conditions = [model.Data.variables.has_key("alert")]
    if "reason" in args.keys():
        conditions.append(model.Data.variables["alert_reason"] == args["reason"])
    if "location" in args.keys():
        locations = get_locations(db.session)
        children = get_children(int(args["location"]), locations)
        conditions.append(model.Data.clinic.in_(children))
    if "start_date" in args.keys():
        conditions.append( model.Data.date >= args["start_date"] )
    if "end_date" in args.keys():
        conditions.append( model.Data.date < args["end_date"] )



    results = db.session.query(model.Data).filter(*conditions)
    alerts = {}

    return rows_to_dicts(results.all())
    
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
        for a in all_alerts:
            reason = a["variables"]["alert_reason"]
            if "ale_1" in a["variables"]:
                if "ale_2" in a["variables"]:
                    status = "Confirmed"
                elif "ale_3" in a["variables"]:
                    status = "Disregarded"
                elif "ale_4" in a["variables"]:
                    status = "Ongoing"
                    
            else:
                # We set all  without an investigation to Pending
                status = "Pending"
            if "cre_1" in a["variables"]:
                # For the countries that have a central_review we overwrite the status from the alert_investigation
                if "cre_2" in a["variables"]:
                    status = "Confirmed"
                elif "cre_3" in a["variables"]:
                    status = "Disregarded"
                elif "cre_4" in a["variables"]:
                    status = "Ongoing"
            r = ret.setdefault(str(reason), {})
            r.setdefault(status, 0)
            r[status] += 1
            
        ret["total"] = len(all_alerts)
        return jsonify(ret)
