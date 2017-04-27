from meerkat_api.resources.epi_week import epi_year_start
from meerkat_api.resources.variables import Variables
from sqlalchemy.sql import text, distinct
from datetime import datetime
from meerkat_abacus.model import Data
from sqlalchemy import or_, func, extract
from meerkat_api.resources.epi_week import epi_year_start

qu = "SELECT sum(CAST(data.variables ->> :variables_1 AS FLOAT)) AS sum_1 extra_columns FROM data WHERE where_clause AND data.date >= :date_1 AND data.date < :date_2 AND (data.country = :country_1 OR data.region = :region_1 OR data.district = :district_1 OR data.clinic = :clinic_1) group_by_clause"


def query_sum(db, var_ids, start_date, end_date, location, level=None, weeks=False, date_variable=None):
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
    Returns:
       result(dict): Dictionary with results. Always has total key, and if
                     level was given there is a level key with the data
                     breakdown
    

    """
    if not isinstance(var_ids, list):
        var_ids = [var_ids]
    variables = {
        "date_1": start_date,
        "date_2": end_date,
        "country_1": location,
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

    for i, var_id in enumerate(var_ids):
        where_clauses.append("(data.variables ? :variables_{})".format(i + 2))
        variables["variables_" + str(i + 2)] = var_id

    if weeks:
        extra_columns = ", floor(EXTRACT(days FROM data.date - :date_3) / 7 + 1) AS week"
        year = start_date.year
        epi_week_start = epi_year_start(year)
        variables["date_3"] = epi_week_start
        group_by.append("week")
        ret["weeks"] = {}
        
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
        if level and weeks:
            for r in result:
                week = int(r[1])
                ret[level].setdefault(r[2], {"total": 0, "weeks": {}})
                ret[level][r[2]]["weeks"][week] = r[0]
                ret[level][r[2]]["total"] += r[0]
                ret["weeks"].setdefault(week, 0)
                ret["weeks"][week] += r[0]
                ret["total"] += r[0]
        elif level:
            for r in result:
                if r[1]:
                    ret[level][r[1]] = r[0]
                    ret["total"] += r[0]

        elif weeks:
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
                 location, level=None, weeks=False, date_variable=None, week_offset=0
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
    location_condtion = [
                or_(loc == location for loc in (
                    Data.country, Data.region, Data.district, Data.clinic))]
    if date_variable:
        date_conditions = [func.to_date(
            Data.variables[date_variable].astext, "YYYY-MM-DDTHH-MI-SS") >= start_date,
                           func.to_date(
                               Data.variables[date_variable].astext, "YYYY-MM-DDTHH-MI-SS") < end_date]
    else:
        date_conditions = [Data.date >= start_date, Data.date < end_date]
    conditions = location_condtion + date_conditions + [Data.variables.has_key(identifier_id)]

    if weeks:
        year = start_date.year
        epi_week_start = epi_year_start(year)
        if date_variable:
            c = func.floor(
                extract('days', func.to_date(Data.variables[date_variable].astext, "YYYY-MM-DDTHH-MI-SS") -
                        epi_week_start) / 7 + 1
            ).label("week")
        else:
            c = func.floor(
                    extract('days', Data.date -
                            epi_week_start) / 7 + 1
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
    print(latest_query(db, "ctc_beds", "ctc_1", datetime(2017, 1, 1),
                       datetime(2017, 12, 31), 1, by_week=True))
