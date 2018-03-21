"""
Data resource for getting Alert data
"""
from flask_restful import Resource
from flask import jsonify, request, g
from sqlalchemy import or_
from dateutil.parser import parse

from meerkat_api.util import row_to_dict, rows_to_dicts
from meerkat_api.extensions import db, api
from meerkat_abacus import model
from meerkat_api.authentication import authenticate, is_allowed_location


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
            if not is_allowed_location(result.clinic, g.allowed_location):
                return {}

            if result.variables.get("alert_type", None) == "threshold":
                other_data = rows_to_dicts(
                    db.session.query(model.Data)
                    .filter(model.Data.variables["master_alert"].astext ==
                            result.uuid).all())
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


    Takes url arguments to restrict the returned alerts \n
       reason: restricts by variable \n
       location: restricts by location \n
       only_latest: returns only the latest alerts \n

    Returns:\n
        alerts\n
    """
    decorators = [authenticate]

    def get(self):
        args = request.args.to_dict()

        if "start_date" in args:
            args["start_date"] = parse(args["start_date"])
        return jsonify({"alerts": get_alerts(args,
                                             allowed_location=g.allowed_location)})


def get_alerts(args, allowed_location=1):
    """
    Gets all alerts where if reason is a key in args we only get alerts with a matching reason. 
    If "location" is in the key we get all alerts from the location or any child clinics. 

    Returns a list of alerts where each element is a dict with {"alerts": alert_info, "links": link_info}
    The link info is the alert investigation

    Args:\n
        args: request args that can include "only_latest", "reason" and "location" as keys to restrict the returned alerts. \n

    Returns:\n
       alerts(list): a list of alerts. \n
    """
    conditions = [model.Data.variables.has_key("alert")]
    disregarded_conditions = [model.DisregardedData.variables.has_key("alert")]

    only_latest = int(args.get("only_latest", 0))
    
    if "reason" in args.keys():
        conditions.append(
            model.Data.variables["alert_reason"].astext == args["reason"])
        disregarded_conditions.append(
            model.DisregardedData.variables["alert_reason"].astext ==
            args["reason"])
       
    if "location" in args.keys():
        if not is_allowed_location(args["location"], allowed_location):
            return {}
        cond = or_(loc == args["location"] for loc in (
            model.Data.country,
            model.Data.zone,
            model.Data.region,
            model.Data.district,
            model.Data.clinic))
        disregarded_cond = or_(loc == args["location"] for loc in (
            model.DisregardedData.country,
            model.DisregardedData.zone,
            model.DisregardedData.region,
            model.DisregardedData.district,
            model.DisregardedData.clinic)
        )
        conditions.append(cond)
        disregarded_conditions.append(disregarded_cond)
    else:
        cond = or_(loc == allowed_location for loc in (
            model.Data.country,
            model.Data.zone,
            model.Data.region,
            model.Data.district,
            model.Data.clinic))
        disregarded_cond = or_(loc == allowed_location for loc in (
            model.DisregardedData.country,
            model.DisregardedData.zone,
            model.DisregardedData.region,
            model.DisregardedData.district,
            model.DisregardedData.clinic)
        )
        conditions.append(cond)
        disregarded_conditions.append(disregarded_cond)
    if "start_date" in args.keys():
        conditions.append(model.Data.date >= args["start_date"])
        disregarded_conditions.append(
            model.DisregardedData.date >= args["start_date"])
    if "end_date" in args.keys():
        conditions.append(model.Data.date < args["end_date"])
        disregarded_conditions.append(model.DisregardedData.date < args["end_date"])
    data_query = db.session.query(model.Data).filter(
        *conditions).order_by(model.Data.date.desc())
    disregarded_query = db.session.query(model.DisregardedData).filter(
            *disregarded_conditions)

    if only_latest:
        results = data_query.limit(only_latest).all()
        results += disregarded_query.limit(only_latest).all()
        results = sorted(results, key=lambda r: r.date,
                         reverse=True)[:only_latest]
    else:
        results = data_query.all()
        results += disregarded_query.all()

    return rows_to_dicts(results)


class AggregateAlerts(Resource):
    """
    Aggregates all alerts based on reason and status in the following format:

    {reason: {status_1: Number, status_2: Number}, reason2: .... , total: total_alerts} 

    Returns:\n
        alerts(dict): Aggregagated alerts by reason and status\n
    """
    decorators = [authenticate]

    def get(self, central_review=False, hard_date_limit=None):
        args = request.args
        all_alerts = get_alerts(args, allowed_location=g.allowed_location)
        ret = {}
        if central_review == "0":
            central_review = False
        total = 0
        if hard_date_limit:
            hard_date_limit = parse(hard_date_limit)
            print(hard_date_limit)
        for a in all_alerts:
            if hard_date_limit and a["date"] < hard_date_limit:
                pass
            else:
                reason = a["variables"]["alert_reason"]
                if central_review:
                    status = "Pending"
                    if "ale_1" in a["variables"]:
                        if "ale_2" in a["variables"]:
                            status = "Ongoing"
                        elif ( "ale_3" in a["variables"] ) or ( "ale_10" in a["variables"] ):
                            status = "Disregarded"
                        elif "ale_4" in a["variables"]:
                            status = "Ongoing"
                        else:
                            status = "Ongoing"

                    if "cre_1" in a["variables"]:
                        if "cre_2" in a["variables"]:
                            status = "Confirmed"
                        elif "cre_3" in a["variables"]:
                            status = "Disregarded"
                        elif "cre_4" in a["variables"]:
                            status = "Ongoing"
                        else:
                            status = "Ongoing"

                else:
                    if "ale_1" in a["variables"]:
                        if "ale_2" in a["variables"]:
                            status = "Confirmed"
                        elif ( "ale_3" in a["variables"] ) or ( "ale_10" in a["variables"] ):
                            status = "Disregarded"
                        elif "ale_4" in a["variables"]:
                            status = "Ongoing"
                        else:
                            status = "Ongoing"
                    else:
                        # We set all  without an investigation to Pending
                        status = "Pending"
                r = ret.setdefault(str(reason), {})
                r.setdefault(status, 0)
                r[status] += 1
                total += 1

        ret["total"] = total
        return jsonify(ret)
api.add_resource(AggregateAlerts, "/aggregate_alerts",
                 "/aggregate_alerts/<central_review>",
                 "/aggregate_alerts/<central_review>/<hard_date_limit>")
api.add_resource(Alert, "/alert/<alert_id>")
api.add_resource(Alerts, "/alerts")
