"""
Resource for aggregating and querying data

"""
from flask_restful import Resource
from sqlalchemy import or_
from datetime import datetime
from flask import jsonify
from meerkat_api.util import rows_to_dicts
from meerkat_api import db
from meerkat_abacus.model import Data
from meerkat_api.resources.variables import Variables
from meerkat_api.authentication import authenticate
from meerkat_api.util.data_query import query_sum


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
        # We sum over variable grouped by epi_week
        if(lim_variable != ""):
            variables.append(lim_variable)
        result = query_sum(
            db, variables, start_date, end_date, location_id, weeks=True
        )
        return {"weeks": result["weeks"], "year": result["total"]}


class AggregateCategory(Resource):
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
        results = db.session.query(Data).filter(
            Data.variables.has_key(str(variable)), or_(
                loc == location_id for loc in (Data.country,
                                               Data.region,
                                               Data.district,
                                               Data.clinic))).all()

        return jsonify({"records": rows_to_dicts(results)})
