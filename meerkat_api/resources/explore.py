"""
Data resource for data exploration
"""
from flask_restful import Resource
from sqlalchemy import or_, extract, func, Integer
from datetime import datetime
from dateutil.parser import parse
from sqlalchemy.sql.expression import cast
from flask import request

from meerkat_api.util import row_to_dict, rows_to_dicts, date_to_epi_week
from meerkat_api import db, app
from meerkat_abacus.model import Data
from meerkat_abacus.util import get_locations, epi_week_start_date
from meerkat_api.resources.variables import Variables
from meerkat_api.authentication import require_api_key

def sort_date(start_date,end_date):
    """ parses start and end date"""
    if end_date:
        end_date = parse(end_date)
    else:
        end_date = datetime.today()
    if start_date:
        start_date = parse(start_date)
    else:
        start_date = datetime(end_date.year,1,1)
    return start_date, end_date


def get_variables(category):
    """ get variables

    Args:
        category
    Returns:
        names
    """
    variables_instance = Variables()
    variables = variables_instance.get(category)
    names = dict((str(v), variables[v]["name"]) for v in variables.keys())
    return names

class QueryVariable(Resource):
    """
    Create a table where all records have variable, and is broken down by
    group_by. Start and end data gives option to specifiy time period

    Args:
        variable: the variable all records need to fulfill
        group_by: category to group by
        start_date: start date
        end_date: end_date
    Returns:
        data: {variable_1: {total: X, weeks: {12:X,13:X}}....}
    """
    decorators = [require_api_key]
    def get(self, variable, group_by, start_date=None, end_date=None, only_loc=None):
        variable = str(variable)
        start_date, end_date = sort_date(start_date, end_date)
        year = start_date.year

        ret = {}
        date_conditions = [Data.date >= start_date, Data.date < end_date]
        if "location" in variable:
            location_id = variable.split(":")[1]
            conditions = date_conditions + [or_(loc == location_id for loc in (
                Data.country, Data.region, Data.district, Data.clinic))]
        else:
            conditions = [Data.variables.has_key(variable)] + date_conditions
            if only_loc:
                conditions += [or_(loc == only_loc for loc in (
                Data.country, Data.region, Data.district, Data.clinic))]
                
        epi_week_start = epi_week_start_date(year)
        columns_to_extract = [func.count(Data.id).label('value'),
                              func.floor(
                                  extract('days', Data.date -
                                          epi_week_start) / 7 + 1
                              ).label("week")]
        if group_by == "locations":
            locations = get_locations(db.session)
            ids = locations.keys()
            names = dict((l.id, l.name) for l in locations.values())


            columns_to_extract += [Data.country, Data.region,
                                   Data.district, Data.clinic]
            group_by_query = "country,region,district,clinic"
        else:
            names = get_variables(group_by)
            ids = names.keys()
            for i in ids:
                columns_to_extract.append(
                    Data.variables.has_key(str(i)).label("id" + str(i)))
            group_by_query = ",".join(["id" + str(i) for i in ids])
            
        for n in names.values():
            ret[n] = {"total": 0, "weeks": {}}


        results = db.session.query(
            *tuple(columns_to_extract)
        ).filter(*conditions).group_by("week," + group_by_query)

        for r in results:
            if group_by == "locations":
                for i_d in ids:
                    if i_d in r[2:]:
                        ret[names[i_d]]["total"] += r[0]
                        ret[names[i_d]]["weeks"][int(r[1])] =int(r[0])
            else:
                for i, i_d in enumerate(ids):
                    if r[i + 2]:
                        ret[names[i_d]]["total"] += r[0]
                        ret[names[i_d]]["weeks"][int(r[1])] = int(r[0])

        return ret
class QueryCategory(Resource):
    """
    Create a table with category1 x category2 and is broken down by
    group_by. Start and end data gives option to specifiy time period

    Args:
        variable: the variable all records need to fulfill
        group_by: category to group by
        start_date: start date
        end_date: end_date
    Returns:
        data: {variable_1: {total: X, weeks: {12:X,13:X}}....}
    """
    decorators = [require_api_key]
    def get(self, group_by1, group_by2, start_date=None, end_date=None):
        start_date, end_date = sort_date(start_date, end_date)
        use_ids = False
        if "use_ids" in request.args.keys():
            use_ids = True
        
        if "locations" == group_by2:
            tmp = group_by1
            group_by1 = group_by2
            group_by2 = tmp

        columns_to_query = [Data.variables]        
        if "locations" == group_by1:
            locations = get_locations(db.session)
            ids1 = locations.keys()
            names1 = dict((l.id, l.name) for l in locations.values())
            columns_to_query += [Data.country, Data.region,
                                 Data.district, Data.clinic]
            conditions = []

        else:
            names1 = get_variables(group_by1)
            if use_ids:
                names1 = {vid: vid for vid in names1.keys()}
            ids1 = names1.keys()
            conditions = [or_(Data.variables.has_key(str(i)) for i in ids1)]
            
        names2 = get_variables(group_by2)
        if use_ids:
            names2 = {vid: vid for vid in names2.keys()}
        ids2 = names2.keys()
        conditions += [or_(Data.variables.has_key(str(i)) for i in ids2)]
        conditions += [Data.date >= start_date, Data.date < end_date]

        results = db.session.query(
            *tuple(columns_to_query)
        ).filter(*conditions)
        ret = {}
        if group_by1 == "locations":
            for r in results.all():
                locs = (r.country, r.region, r.district, r.clinic)
                for i2 in ids2:
                    if i2 in r.variables:
                        for l in locs:
                            ret.setdefault(names1[l], {}).setdefault(
                                names2[i2], 0)
                            ret[names1[l]][names2[i2]] += 1
                    else:
                        for l in locs:
                            ret.setdefault(names1[l], {}).setdefault(
                                names2[i2], 0)
        else:
            for r in results.all():
                for i1 in ids1:
                    if i1 in r.variables:
                        for i2 in ids2:
                            if i2 in r.variables:
                                ret.setdefault(names1[i1], {}).setdefault(
                                    names2[i2], 0)
                                ret[names1[i1]][names2[i2]] += 1
                            else:
                                ret.setdefault(names1[i1], {}).setdefault(
                                    names2[i2], 0)
                    else:
                        for i2 in ids2:
                            ret.setdefault(names1[i1], {}).setdefault(
                                names2[i2], 0)

        return ret
