"""
Data resource for data exploration
"""
from flask_restful import Resource
from sqlalchemy import or_, extract, func, Integer
from datetime import datetime, timedelta
from dateutil.parser import parse
from sqlalchemy.sql.expression import cast
from flask import request



from meerkat_api.util import row_to_dict, rows_to_dicts, is_child
from meerkat_api.resources.epi_week import epi_year_start
from meerkat_api import db, app
from meerkat_abacus.model import Data
from meerkat_abacus.util import get_locations, epi_week_start_date
from meerkat_api.resources.variables import Variables
from meerkat_api.resources.epi_week import EpiWeek
from meerkat_api.authentication import authenticate

def sort_date(start_date, end_date):
    """
    parses start and end date and remoces any timezone info

    Args: 
       start_date: start date
       end_date: end date
    
    Returns: 
       (start_date, end_date)
    """
    if end_date:
        end_date = parse(end_date).replace(tzinfo=None)
    else:
        end_date = datetime.today()
    if start_date:
        start_date = parse(start_date).replace(tzinfo=None)
        if start_date < epi_year_start(year=start_date.year):
            start_date = epi_year_start(year=start_date.year)
    else:
        start_date = epi_year_start(year=end_date.year) #datetime(end_date.year,1,1)

    return start_date, end_date


def get_variables(category):
    """ 
    Get variables with category

    Args:
        category: category of variables to get
    Returns:
        names(dict): {key: variable}
    """
    variables_instance = Variables()
    variables = variables_instance.get(category)
    names = dict((str(v), variables[v]["name"]) for v in variables.keys())
    return names

def query_ids(variables, start_date, end_date, only_loc=None):
    """
    Finds the number of records that has all the variable ids in variables

    Args:
        variables: list of variable ids the records should have
        start_date: start date
        end_date: end date
        only_loc: If given it restricts to that location

    Returns:
       The number of records that have all variables
    """
    conditions = [Data.date >= start_date, Data.date < end_date]
    for variable in variables:
        conditions.append(Data.variables.has_key(variable))
    if only_loc:
        conditions += [or_(loc == only_loc for loc in (
            Data.country, Data.region, Data.district, Data.clinic))]
    res = db.session.query(func.count(Data.id)).filter(*conditions).one()
    return res[0]



def get_locations_by_level(level, only_loc):
    """
    Returns all the locations with the given level. If only_loc is
    given we only include children of only_loc.If we ask for the clinic 
    level we also require that the clinic sends case reports

    Args:
        level: clinic, district or region
        only_loc: location to restrict wich locations are included

    Returns:
        names: {id: name}
    """
    locations = get_locations(db.session)
    names = {}
    for l in locations.values():
        if (l.level == level
            and (not only_loc or is_child(only_loc, l.id, locations))
            and (level != "clinic" or l.case_report)
        ):
            names[l.id] = l.name 
    return names


class QueryVariable(Resource):
    """
    Create a table where all records have the variable, and is broken down by
    group_by. Start and end data gives option to specifiy time period

    Args:\n
        variable: the variable all records need to fulfill\n
        group_by: category to group by\n
        start_date: start date\n
        end_date: end_date\n
        only_loc: If given retricts the data to that location\n
        use_ids: If use_ids is true we use variable_ids and not the name as keys for the return\n

    Returns:\n
        data: {variable_1: {total: X, weeks: {12:X,13:X}}....}\n
    """
    decorators = [authenticate]

    def get(self, variable, group_by, start_date=None, end_date=None, only_loc=None, use_ids=None):
        # We first construct the conditions for our database query. Need to take special care if the 
        # variable or the group_by is given in terms of locations as they need to be handeld differently. 
        # We then do the db-query and then assemble the return dictionary
        variable = str(variable)
        start_date, end_date = sort_date(start_date, end_date)
        year = start_date.year
        if "use_ids" in request.args.keys() or use_ids:
            use_ids = True
        else:
            use_ids = False

        date_conditions = [Data.date >= start_date, Data.date < end_date]

        if "location" in variable:
            location_id = variable.split(":")[1]
            conditions = date_conditions + [or_(loc == location_id for loc in (
                Data.country, Data.region, Data.district, Data.clinic))]
        else:
            conditions = [Data.variables.has_key(variable)] + date_conditions
            if only_loc or "only_loc" in request.args:
                if not only_loc:
                    #only loc is in request variables
                    only_loc = request.args["only_loc"]
                conditions += [or_(loc == only_loc for loc in (
                    Data.country, Data.region, Data.district, Data.clinic))]
        epi_week_start = epi_year_start(year)
        # Determine which columns we want to extract from the Data table
        columns_to_extract = [func.count(Data.id).label('value'),
                              func.floor(
                                  extract('days', Data.date -
                                          epi_week_start) / 7 + 1
                              ).label("week")]

        # We want to add the columns to extract based on the group_by value
        # in addition we create a names dict that translates ids to names
        
        if "locations" in group_by:
            # If we have locations in group_by we also specify the level at which
            # we want to group the locations, clinic, district or region
            if ":" in group_by:
                level = group_by.split(":")[1]
            else:
                level = "clinic"
                
            locations = get_locations(db.session)
            ids = locations.keys()
            names = get_locations_by_level(level, only_loc)

            columns_to_extract += [getattr(Data, level, None)]
            group_by_query = level
        else:
            names = get_variables(group_by)
            if len(names) == 0:
                return {}
            ids = names.keys()
            for i in ids:
                columns_to_extract.append(
                    Data.variables.has_key(str(i)).label("id" + str(i)))
            group_by_query = ",".join(["id" + str(i) for i in ids])

        if use_ids:
            names = {vid: vid for vid in names.keys()}

        ew = EpiWeek()
        start_week = ew.get(start_date.isoformat())["epi_week"]
        end_week = ew.get(end_date.isoformat())["epi_week"]
        
        # How we deal with start and end dates in different years
        if start_date.year != end_date.year:
            end_week += 53 * (end_date.year - start_date.year)
        if start_week == 0:
            start_week = 1
        # DB Query
        results = db.session.query(
            *tuple(columns_to_extract)
        ).filter(*conditions).group_by("week," + group_by_query)

        # Assemble return dict
        ret = {}
        for n in names.values():
            ret[n] = {"total": 0,
                      "weeks": {i: 0 for i in range(start_week, end_week + 1)}}
        for r in results:
            # r = (number, week, other_columns_to_extract
            if "locations" in group_by:
                # r[2] = location
                ret[names[r[2]]]["total"] += r[0]
                ret[names[r[2]]]["weeks"][int(r[1])] =int(r[0])
            else:
                # r[2:] are the ids that the record has
                for i, i_d in enumerate(ids):
                    if r[i + 2]:
                        ret[names[i_d]]["total"] += r[0]
                        ret[names[i_d]]["weeks"][int(r[1])] = int(r[0])

        return ret



class QueryCategory(Resource):
    """
    Create a contingency table with category1 x category2. 
    Start and end data gives option to specifiy time period. 

    Args:\n
        variable: the variable all records need to fulfill\n
        group_by: category to group by\n
        start_date: start date\n
        end_date: end_date\n
        only_loc: restrict data to only this location\n
    Returns:\n
        data: {variable_11: {variable_21: number, variable_22: number ...}, 
               variable_12: {....\n
    """
    decorators = [authenticate]
    def get(self, group_by1, group_by2, start_date=None, end_date=None, only_loc=None):
        # We first construct the conditions for our database query. Need to take special care if any of the categories are locations
        # locations as they need to be handeld differently. 
        # We then do the db-query and then assemble the return dictionary
        
        start_date, end_date = sort_date(start_date, end_date)
        use_ids = False
        if "use_ids" in request.args.keys():
            use_ids = True

        # Assemble conditions and columns to query
        conditions = []
        if only_loc or "only_loc" in request.args:
            if not only_loc:
                only_loc = request.args["only_loc"]
                conditions += [or_(loc == only_loc for loc in (
                    Data.country, Data.region, Data.district, Data.clinic))]

        columns_to_query = [Data.variables]
        if "locations" in group_by1:
            if ":" in group_by1:
                level = group_by1.split(":")[-1]
            else:
                level = "clinic"
            names1 = get_locations_by_level(level, only_loc)
            ids1 = list(names1.keys())
            columns_to_query += [getattr(Data, level)]
            names2 = get_variables(group_by2)
            ids2 = names2.keys()
            conditions += [or_(Data.variables.has_key(str(i)) for i in ids2)]            

        elif "locations" in group_by2:
            if ":" in group_by2:
                level = group_by2.split(":")[-1]
            else:
                level = "clinic"
            names2 = get_locations_by_level(level, only_loc)
            ids2 = list(names2.keys())
            columns_to_query += [getattr(Data, level)]
            names1 = get_variables(group_by1)
            ids1 = names1.keys()
            conditions += [or_(Data.variables.has_key(str(i)) for i in ids1)]

        else:
            names1 = get_variables(group_by1)
            ids1 = names1.keys()
            conditions += [or_(Data.variables.has_key(str(i)) for i in ids1)]
            names2 = get_variables(group_by2)
            ids2 = names2.keys()
            conditions += [or_(Data.variables.has_key(str(i)) for i in ids2)]            

        if use_ids:
            names1 = {vid: vid for vid in names1.keys()}
            names2 = {vid: vid for vid in names2.keys()}
        conditions += [Data.date >= start_date, Data.date < end_date]
        
        # DB query
        results = db.session.query(
            *tuple(columns_to_query)
        ).filter(*conditions)
        ret = {}

        # Assemble return dict
        for r in results.all():
            list_of_vars = r.variables
            if "locations" in group_by1 or "locations" in group_by2:
                list_of_vars[getattr(r, level, 1)] = 1
            for i1 in list_of_vars.keys():
                for i2 in list_of_vars.keys():
                    if i1 in ids1 and i2 in ids2:
                        ret.setdefault(names1[i1], {}).setdefault(
                            names2[i2], 0)
                        ret[names1[i1]][names2[i2]] += 1
                        
        # We also add rows and columns with zeros
        for n1 in names1.values():
            for n2 in names2.values():
                if n1 in ret:
                    if n2 not in ret[n1]:
                        ret[n1][n2] = 0
                else:
                    ret.setdefault(n1, {})
                    ret[n1][n2] = 0
        return ret
