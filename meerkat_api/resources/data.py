"""
Resource for aggregating and querying data

"""
from flask_restful import Resource
from sqlalchemy import or_
from datetime import datetime, timedelta
from flask import jsonify, g, request
from meerkat_api.util import rows_to_dicts
from meerkat_api.extensions import db, api
from meerkat_abacus.model import Data
from meerkat_api.resources.variables import Variables
from meerkat_api.authentication import authenticate, is_allowed_location
from meerkat_api.util.data_query import query_sum
from meerkat_api.util.data_query import latest_query
from meerkat_abacus.util import get_locations


class LatestData(Resource):
    """
    Data submitted in the last day
    Args: \n
        location: location_id
    """
    decorators = [authenticate]

    def get(self, location_id):
        if not is_allowed_location(location_id, g.allowed_location):
            return {"records": []}
            
        results = db.session.query(Data).filter(or_(
                loc == location_id for loc in (Data.country,
                                               Data.region,
                                               Data.district,
                                               Data.clinic)),
                                                Data.submission_date >= datetime.now() - timedelta(days=1)).order_by(Data.submission_date.desc()).all()

        return jsonify({"records": rows_to_dicts(results)})

class Aggregate(Resource):
    """
    Count (or add up) all the records with variable and location over all time.

    Args:\n
        variable: variable_id\n
        location: location_id\n

    Returns:\n
        result: {"value": value}\n
    """
    decorators = [authenticate]

    def get(self, variable_id, location_id):

        result = query_sum(
            db,
            [variable_id],
            datetime(1900, 1, 1),
            datetime(2100, 1, 1),
            location_id
        )
        return {"value": result["total"]}


class AggregateLatest(Resource):
    """
    Get total and weekly aggregate for the current year for the given
    variable and location. Can get data for other years by useing the
    year keyword argument.

    Args:\n
        variable: variable_id\n
        location: location_id\n
        year: year (defaults to current year)\n

    Reutrns:\n
       result_dict: {"weeks":{1:0....}, "year":0}\n
    """
    decorators = [authenticate]

    def get(self, variable_id, identifier_id, location_id):
        variable_id = str(variable_id)
        start_date = datetime(1900, 1, 1)
        end_date = datetime(2100, 1, 1)
        result = latest_query(
            db, variable_id, identifier_id, start_date, end_date, location_id
        )
        return{"value":  result["total"]}


    
class AggregateYear(Resource):
    """
    Get total and weekly aggregate for the current year for the given
    variable and location. Can get data for other years by useing the
    year keyword argument.

    Args:\n
        variable: variable_id\n
        location: location_id\n
        year: year (defaults to current year)\n

    Reutrns:\n
       result_dict: {"weeks":{1:0....}, "year":0}\n
    """
    decorators = [authenticate]

    def get(self, variable_id, location_id, year=datetime.today().year,
            lim_variable=""):
        vi = str(variable_id)
        year = int(year)
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)
        variables = [vi]

        req_level= request.args.get('level')

        # We sum over variable grouped by epi_week
        if(lim_variable != ""):
            variables.append(lim_variable)
        result = query_sum(
            db, variables, start_date, end_date, location_id, weeks=True, level=req_level
        )
        if req_level==None:
            return {"weeks": result["weeks"], "year": result["total"]}
        else:
            return result



class AggregateCategory(Resource):
    """
    Get total and weekly aggregate for a year for all variables
    with a given category. Only aggregate over the given location. It is faster than AggregateCategorySum() if each variable in the categories are mutually exclusive (for instance for gender) but gives exactly the same output.
    Args:\n
        category: category\n
        location: location_id\n
        year: year\n
        lim_variable: limit results to those with this variable\n

    Returns:\n
        result_dict: {variable_id: AggregateYear result_dict}\n
    """
    decorators = [authenticate]

    def get(self, category, location_id, lim_variable=None, year=None):
        if year is None:
            year = datetime.today().year
        year = int(year)
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)

        if lim_variable is not None:
            filter_variables = ["data_entry"] + [lim_variable]
        else:
            filter_variables = ["data_entry"]


        result = query_sum(
            db, filter_variables, start_date, end_date, location_id,
            group_by_category=category, weeks=True
        )
        return_data = {}
        variables_instance = Variables()
        variables = variables_instance.get(category)
        for r in variables.keys():
            if r in result[category]:
                return_data[r] = result[category][r]
                return_data[r]["year"] = return_data[r]["total"]
            else:
                return_data[r] = {"year": 0, "weeks": {}}
        return return_data
    
class AggregateCategorySum(Resource):
    """
    This function does the same as AggregateCategory. Get total and weekly aggregate for a year for all variables with a given category. Only aggregate over the given location. It gives the same output as AggregateCategory() and is better suited if variables within a category are overlapping.

    Args:\n
        category: category\n
        location: location_id\n
        year: year\n
        lim_variable: limit results to those with this variable\n

    Returns:\n
        result_dict: {variable_id: AggregateYear result_dict}\n
    """
    decorators = [authenticate]

    def get(self, category, location_id, lim_variable="", year=None):

        
        if year is None:
            year = datetime.today().year
        variables_instance = Variables()
        variables = variables_instance.get(category)
        aggregate_year = AggregateYear()

        return_data = {}
        for variable in variables.keys():
            return_data[variable] = aggregate_year.get(variable,
                                                       location_id,
                                                       year,
                                                       lim_variable)
        return return_data
    
class AggregateLatestYear(Resource):
    """
    Get total and weekly aggregate for the current year for the given
    variable and location. Can get data for other years by useing the
    year keyword argument.

    Args:\n
        variable: variable_id\n
        location: location_id\n
        year: year (defaults to current year)\n

    Reutrns:\n
       result_dict: {"weeks":{1:0....}, "year":0}\n
    """
    decorators = [authenticate]

    def get(self, variable_id, identifier_id, location_id, year=datetime.today().year, weeks=True):
        variable_id = str(variable_id)
        if weeks in [0, "0"]:
            weeks = False
        identifier_id = str(identifier_id)
        year = int(year)
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)
        result = latest_query(
            db, variable_id, identifier_id, start_date, end_date, location_id, weeks=weeks
        )
        if weeks:
            ret = {"weeks": result["weeks"], "year": result["total"]}
        else:
            ret = result
        return ret


class AggregateLatestCategory(Resource):
    """
    Get total and weekly aggregate for a year for all variables
    with a given category. Only aggregate over the given location.

    Args:\n
        category: category\n
        location: location_id\n
        year: year\n
        lim_variable: limit results to those with this variable\n

    Returns:\n
        result_dict: {variable_id: AggregateYear result_dict}\n
    """
    decorators = [authenticate]

    def get(self, category,  identifier_id, location_id, weeks=True, year=None):
        if year is None:
            year = datetime.today().year

        if weeks in ["0", 0]:
            weeks = False
        variables_instance = Variables()
        variables = variables_instance.get(category)
        aggregate_latest_year = AggregateLatestYear()

        return_data = {}
        for variable in variables.keys():
            return_data[variable] = aggregate_latest_year.get(
                variable,
                identifier_id,
                location_id,
                year,
                weeks=weeks)
                
        return return_data

    
class AggregateLatestLevel(Resource):
    """
    Get total and weekly aggregate for the current year for the given
    variable and location. Can get data for other years by useing the
    year keyword argument.

    Args:\n
        variable: variable_id\n
        location: location_id\n
        year: year (defaults to current year)\n

    Reutrns:\n
       result_dict: {"weeks":{1:0....}, "year":0}\n
    """
    decorators = [authenticate]

    def get(self, variable_id, identifier_id, level, weekly=True, location_id=1):
        variable_id = str(variable_id)
        identifier_id = str(identifier_id)
        if weekly == "0":
            weekly = False
        year = datetime.today().year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)
        result = latest_query(
            db, variable_id, identifier_id, start_date, end_date, location_id, weeks=True
        )
        ret = {}
        locs = get_locations(db.session)
        if result: 
            for r in result[level]:
                ret[locs[r].name] = {"total": result[level][r]["total"],
                                     "weeks": result[level][r]["weeks"],
                                     "id": r}
            
        return ret


    
class Records(Resource):
    """
    Return the records with a given variable and location

    Args:\n
       variable: variable_id\n
       location: location\n

    Returns:\n
       list_of_records\n
    """
    decorators = [authenticate]

    def get(self, variable, location_id):
        if not is_allowed_location(location_id, g.allowed_location):
            return {"records": []}
            
        results = db.session.query(Data).filter(
            Data.variables.has_key(str(variable)), or_(
                loc == location_id for loc in (Data.country,
                                               Data.region,
                                               Data.district,
                                               Data.clinic))).all()

        return jsonify({"records": rows_to_dicts(results)})
api.add_resource(Aggregate, "/aggregate/<variable_id>/<location_id>")
api.add_resource(AggregateLatest, "/aggregate_latest/<variable_id>/<identifier_id>/<location_id>")

api.add_resource(AggregateYear,
                 "/aggregate_year/<variable_id>/<location_id>",
                 "/aggregate_year/<variable_id>/<location_id>/<year>")
api.add_resource(AggregateLatestYear,
                 "/aggregate_latest_year/<variable_id>/<identifier_id>/<location_id>",
                 "/aggregate_latest_year/<variable_id>/<identifier_id>/<location_id>/<weeks>",
                 "/aggregate_latest_year/<variable_id>/<identifier_id>/<location_id>/<weeks>/<year>")
api.add_resource(AggregateLatestLevel,
                 "/aggregate_latest_level/<variable_id>/<identifier_id>/<level>",
                 "/aggregate_latest_level/<variable_id>/<identifier_id>/<level>/<weekly>",
                 "/aggregate_latest_level/<variable_id>/<identifier_id>/<level>/<weekly>/<location_id>")
api.add_resource(AggregateLatestCategory,
                 "/aggregate_latest_category/<category>/<identifier_id>/<location_id>",
                 "/aggregate_latest_category/<category>/<identifier_id>/<location_id>/<weeks>",
                 "/aggregate_latest_category/<category>/<identifier_id>/<location_id>/<weeks>/<year>"

                )

api.add_resource(AggregateCategory,
                 "/aggregate_category/<category>/<location_id>",
                 "/aggregate_category/<category>/<location_id>/<year>",
                 "/aggregate_category/<category>/<location_id>/<year>/<lim_variable>")
api.add_resource(AggregateCategorySum,
                 "/aggregate_category_sum/<category>/<location_id>",
                 "/aggregate_category_sum/<category>/<location_id>/<year>",
                 "/aggregate_category_sum/<category>/<location_id>/<year>/<lim_variable>")
api.add_resource(Records, "/records/<variable>/<location_id>")
