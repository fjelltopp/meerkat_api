"""
Data resource for getting Alert data
"""
from flask_restful import Resource
from flask import jsonify, request, current_app

from meerkat_api.util import row_to_dict, rows_to_dicts, get_children
from meerkat_api import db
from meerkat_abacus import model
from meerkat_abacus.util import get_locations
from meerkat_api.authentication import authenticate


class Alert(Resource):
    """
    Get alert with alert_id
    
    Args:\n
        alert_id\n

    Returns:\n
        alert\n
    """
    decorators = [authenticate]

    def get(self, alert_id):
        result = db.session.query(model.Data).filter(
            model.Data.variables["alert_id"].astext == alert_id).first()
        if result:
            if result.variables.get("alert_type", None) == "threshold":
                alert_links = result.variables.get("linked_alerts", [])
                if alert_links:
                    other_data = rows_to_dicts(
                        db.session.query(model.Data)
                        .filter(model.Data.variables["master_alert"].astext ==
                                result.uuid).all())
                else:
                    other_data = {}
            else:
                other_data = {}
            return jsonify({"alert": row_to_dict(result),
                            "linked_alerts": other_data})
        else:
            result = db.session.query(model.DisregardedData).filter(
                model.DisregardedData.variables["alert_id"].astext ==
                alert_id).first()
            if result:
                return jsonify({"alert": row_to_dict(result),
                                "linked_alerts": {}})
            return {}


class Alerts(Resource):
    """
    Get alert all alerts

    Returns:\n
        alerts\n
    """
    decorators = [authenticate]

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
    disregarded_conditions = [model.DisregardedData.variables.has_key("alert")]
    if "reason" in args.keys():
        conditions.append(
            model.Data.variables["alert_reason"].astext == args["reason"])
        disregarded_conditions.append(
            model.DisregardedData.variables["alert_reason"].astext ==
            args["reason"])
    if "location" in args.keys():
        locations = get_locations(db.session)
        children = get_children(int(args["location"]), locations)
        conditions.append(model.Data.clinic.in_(children))
        disregarded_conditions.append(
            model.DisregardedData.clinic.in_(children))
    if "start_date" in args.keys():
        conditions.append(model.Data.date >= args["start_date"])
        disregarded_conditions.append(
            model.DisregardedData.date >= args["start_date"])
    if "end_date" in args.keys():
        conditions.append(model.Data.date < args["end_date"])
        disregarded_conditions.append(
            model.DisregardedData.date < args["end_date"])

    results = db.session.query(model.Data).filter(*conditions).all()
    results += db.session.query(model.DisregardedData).filter(
        *disregarded_conditions).all()

    return rows_to_dicts(results)


class AggregateAlerts(Resource):
    """
    Aggregates all alerts based on reason and status in the following format:

    {reason: {status_1: Number, status_2: Number}, reason2: .... , total: total_alerts} 

    Returns:\n
        alerts(dict): Aggregagated alerts by reason and status\n
    """
    decorators = [authenticate]

    def get(self, central_review=False):
        args = request.args
        all_alerts = get_alerts(args)
        ret = {}
        for a in all_alerts:
            reason = a["variables"]["alert_reason"]

            if central_review:
                if "ale_1" in a["variables"]:
                    if "ale_2" in a["variables"]:
                        status = "Ongoing"
                    elif "ale_3" in a["variables"]:
                        status = "Disregarded"
                    elif "ale_4" in a["variables"]:
                        status = "Ongoing"

                    if "cre_1" in a["variables"]:
                        if "cre_2" in a["variables"]:
                            status = "Confirmed"
                        elif "cre_3" in a["variables"]:
                            status = "Disregarded"
                        elif "cre_4" in a["variables"]:
                            status = "Ongoing"
                else:
                    # We set all  without an investigation to Pending
                    status = "Pending"
            else:
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
            r = ret.setdefault(str(reason), {})
            r.setdefault(status, 0)
            r[status] += 1

        ret["total"] = len(all_alerts)
        return jsonify(ret)
