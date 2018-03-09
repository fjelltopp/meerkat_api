from datetime import datetime
from flask import g
from sqlalchemy import or_, func, extract
from sqlalchemy.sql import text

import meerkat_abacus.util as abacus_util
import meerkat_abacus.util.epi_week
from meerkat_abacus.model import Data
from meerkat_api.authentication import is_allowed_location

qu = "SELECT sum(CAST(data.variables ->> :variables_1 AS FLOAT)) AS sum_1 extra_columns FROM data WHERE where_clause AND data.date >= :date_1 AND data.date < :date_2 AND (data.country = :country_1 OR data.zone = :zone_1 OR data.region = :region_1 OR data.district = :district_1 OR data.clinic = :clinic_1) group_by_clause"


def query_sum(db, var_ids, start_date, end_date, location,
              group_by_category=None, allowed_location=1,
              level=None, weeks=False, date_variable=None, exclude_variables=None):
    """
    Calculates the total number of records with every variable in var_ids.
    If var_ids is only one variable it can also be used to sum up the numbers
    of var_id.

    If level is not None the data will be broken down by location level.


    Args:
        var_ids: list(or just a string) with variable ids
        start_date: Start date
        end_date: End date
        location: Location to restrict to
        level: Level to brea down the total by
        weeks: True if we want a breakdwon by weeks.
        date_variable: if None we use date from data otherwise we use the variable indicated
        exclude_variables: list with variables to be excluded
    Returns:
       result(dict): Dictionary with results. Always has total key, and if
                     level was given there is a level key with the data
                     breakdown
    

    """
    if allowed_location == 1:
        if g:
            allowed_location = g.allowed_location
    if not is_allowed_location(location, allowed_location):
        return {"weeks": [], "total": 0}
    if not isinstance(var_ids, list):
        var_ids = [var_ids]
    if exclude_variables is None:
        exclude_variables = []
    variables = {
        "date_1": start_date,
        "date_2": end_date,
        "country_1": location,
        "zone_1": location,
        "region_1": location,
        "district_1": location,
        "clinic_1": location,
        "variables_1": var_ids[0]
    }
    extra_columns = ""
    group_by_clause = ""
    group_by = []
    where_clauses = []
    ret = {"total": 0}

    for i, var_id in enumerate(var_ids, 2): # variables_1 already in place
        condition_ = "(data.variables ? :variables_{})".format(i)
        where_clauses.append(condition_)
        variables[f"variables_{i}"] = var_id

    for i, var_id in enumerate(exclude_variables, 1):
        condition_ = f"(data.variables->>:excluded_variables_{i}) is null"
        where_clauses.append(condition_)
        variables[f"excluded_variables_{i}"] = var_id

    if weeks:
        extra_columns = ", epi_week AS week"
        group_by.append("week")
        ret["weeks"] = {}

    if group_by_category and level:
        return {}
    
    if group_by_category:
        extra_columns += ", categories->>:category1 as category"
        where_clauses.append("data.categories ? :category2")
        variables["category1"] = group_by_category
        variables["category2"] = group_by_category
        ret[group_by_category] = {}
        group_by.append("category")
    if level:
        ret[level] = {}
        group_by.append(level)
        extra_columns += ', "' + level + '"'
    if group_by:

        group_by_clause = "group by " + ", ".join(group_by)
        
    query = qu.replace("where_clause", " AND ".join(where_clauses))
    query = query.replace("group_by_clause", group_by_clause)
    query = text(query.replace("extra_columns", extra_columns))
    if date_variable:
        date_string = 'to_date(data->> :date_variable, "YYYY-MM-DDTHH-MI-SS")'
        variables["date_variable"] = date_variable
        query.replace("data.date", date_string)

    conn = db.engine.connect()
    result = conn.execute(query, **variables).fetchall()
    if result:
        if level:
            if weeks:
                for r in result:
                    week = int(r[1])
                    ret[level].setdefault(r[2], {"total": 0, "weeks": {}})
                    ret[level][r[2]]["weeks"][week] = r[0]
                    ret[level][r[2]]["total"] += r[0]
                    ret["weeks"].setdefault(week, 0)
                    ret["weeks"][week] += r[0]
                    ret["total"] += r[0]
            else:
                for r in result:
                    if r[1]:
                        ret[level][r[1]] = r[0]
                        ret["total"] += r[0]
        elif group_by_category:
            if weeks:
                for r in result:
                    week = int(r[1])
                    if r[2]:
                        ret[group_by_category].setdefault(r[2],
                                                          {"total": 0, "weeks": {}})
                        ret[group_by_category][r[2]]["weeks"][week] = r[0]
                        ret[group_by_category][r[2]]["total"] += r[0]
                        ret["weeks"].setdefault(week, 0)
                        ret["weeks"][week] += r[0]
                        ret["total"] += r[0]

            else:
                for r in result:
                    if r[1]:
                        ret[group_by_category][r[1]] = r[0]
                        ret["total"] += r[0]

        else:

            if weeks:
                for r in result:
                    if r[1]:
                        ret["weeks"][int(r[1])] = r[0]
                        ret["total"] += r[0]
            else:
                if result[0][0]:
                    ret["total"] = result[0][0]
                else:
                    ret["total"] = 0

    return ret


def latest_query(db, var_id, identifier_id, start_date, end_date,
                 location, allowed_location=1, level=None,
                 weeks=False, date_variable=None, week_offset=0
                 ):
    """
    To query register like data where we want to get the latest value.

    I.e If the value of the number of beds is updated each week and we want the latest number. 
    We take the latest value per clinic.

    Args:
        var_id: Variable id to get last of
        identifier_id: Id to identify which records we should use
        start_date: Start date
        end_date: End date
        location: Location to restrict to
        date_variable: if None we use date from data otherwise we use the variable indicated
        weeks: True if we want a breakdwon by weeks.
    Returns:
       result(dict): Dictionary with results. Always has total key, and if
                     level was given there is a level key with the data
                     breakdown
    """
    if allowed_location == 1:
        if g:
            allowed_location = g.allowed_location
    if not is_allowed_location(location, allowed_location):
        return {}
    location_condtion = [
                or_(loc == location for loc in (
                    Data.country, Data.zone, Data.region, Data.district, Data.clinic))]
    if date_variable:
        date_conditions = [func.to_date(
            Data.variables[date_variable].astext, "YYYY-MM-DDTHH-MI-SS") >= start_date,
                           func.to_date(
                               Data.variables[date_variable].astext, "YYYY-MM-DDTHH-MI-SS") < end_date]
    else:
        date_conditions = [Data.date >= start_date, Data.date < end_date]
    conditions = location_condtion + date_conditions + [Data.variables.has_key(identifier_id)]

    if weeks:
        epi_year_start = meerkat_abacus.util.epi_week.epi_year_start_date(start_date)
        if date_variable:
            c = func.floor(
                extract('days', func.to_date(Data.variables[date_variable].astext, "YYYY-MM-DDTHH-MI-SS") -
                        epi_year_start) / 7 + 1
            ).label("week")
        else:
            c = func.floor(
                    extract('days', Data.date -
                            epi_year_start) / 7 + 1
                ).label("week")
        # This query selects that latest record for each clinic for each week
        # that has the variable identifier_id   
        query = db.session.query(Data.clinic, c, Data.date, Data.region,
                                 Data.district, Data.variables).distinct(
                                     Data.clinic, c).filter(*conditions).order_by(
                                             Data.clinic).order_by(c).order_by(Data.date.desc())
        ret = {"total": 0,
               "weeks": {},
               "district": {},
               "clinic": {},
               "region": {}}

        for r in query:
            val = r.variables.get(var_id, 0)
            ret["total"] += val
            week = int(r.week) - week_offset
            ret["weeks"].setdefault(week, 0)
            ret["weeks"][week] += val

            ret["clinic"].setdefault(r.clinic,
                                     {"total": 0,
                                      "weeks": {}})
            ret["clinic"][r.clinic]["total"] += val
            ret["clinic"][r.clinic]["weeks"][week] = val
            ret["district"].setdefault(r.district,
                                       {"total": 0,
                                        "weeks": {}})
            ret["district"][r.district]["total"] += val
            ret["district"][r.district]["weeks"][week] = +val
            ret["region"].setdefault(r.region,
                                     {"total": 0,
                                      "weeks": {}})
            ret["region"][r.region]["total"] += val
            ret["region"][r.region]["weeks"][week] = +val
        return ret
    else:
        # This query selects that latest record for each clinic
        # that has the variable identifier_id
        query = db.session.query(Data.clinic, Data.date, Data.region,
                                 Data.district,
                                 Data.variables).distinct(
                                    Data.clinic).filter(*conditions).order_by(
                                        Data.clinic).order_by(Data.date.desc())

        ret = {"total": 0,
               "clinic": {},
               "district": {},
               "region": {}}
        for r in query:
            val = r.variables.get(var_id, 0)
            ret["total"] += val
            ret["clinic"][r.clinic] = val
            ret["district"].setdefault(r.district, 0)
            ret["district"][r.district] += val
            ret["region"].setdefault(r.region, 0)
            ret["region"][r.region] += val
        return ret


if __name__ == '__main__':
    from meerkat_api import db

    print(query_sum(db, "tot_1", datetime(2017, 1, 1), datetime(2017, 12, 31), 1,
                    group_by_category="gender", weeks=True))
    #print(latest_query(db, "ctc_beds", "ctc_1", datetime(2017, 1, 1),
                       #datetime(2017, 12, 31), 1, by_week=True))
