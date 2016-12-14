from meerkat_api.resources.epi_week import epi_year_start
from meerkat_api.resources.variables import Variables
from sqlalchemy.sql import text
from datetime import datetime

qu = "SELECT sum(CAST(data.variables ->> :variables_1 AS FLOAT)) AS sum_1 extra_columns FROM data WHERE where_clause AND data.date >= :date_1 AND data.date < :date_2 AND (data.country = :country_1 OR data.region = :region_1 OR data.district = :district_1 OR data.clinic = :clinic_1) group_by_clause"


def query_sum(db, var_ids, start_date, end_date, location, level=None, weeks=False):
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
