"""
Resource for aggregating and querying data

"""
from flask_restful import Resource
from sqlalchemy import or_, extract, func, Integer, Float
from datetime import datetime
from flask import jsonify

from meerkat_api.util import rows_to_dicts
from meerkat_api import db, app
from meerkat_api.resources.epi_week import epi_year_start
from meerkat_abacus.model import Data
from meerkat_api.resources.variables import Variables
from meerkat_api.authentication import authenticate


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
        results = db.session.query(Data.variables).filter(
            Data.variables.has_key(variable_id), or_(
                loc == location_id for loc in (Data.country,
                                               Data.region,
                                               Data.district,
                                               Data.clinic)))
        total = 0
        for row in results:
            total += row.variables[variable_id]
        return {"value": total}


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
    
    def get(self, variable_id, location_id, year=datetime.today().year):
        year = int(year)
        vi = str(variable_id)
        epi_week_start = epi_year_start(year)

        # We sum over variable grouped by epi_week
        results = db.session.query(
            func.sum(Data.variables[vi].astext.cast(Float)).label('value'),
            func.floor(
                extract('days', Data.date -
                        epi_week_start) / 7 + 1).label("week")
        ).filter(Data.variables.has_key(vi),
                 extract('year', Data.date) == year,
                 or_(loc == location_id for loc in (Data.country,
                                                    Data.region,
                                                    Data.district,
                                                    Data.clinic))
        ).group_by("week")
        weeks = dict((int(el[1]), el[0]) for el in results.all())
        return {"weeks": weeks, "year": sum(weeks.values())}


class AggregateCategory(Resource):
    """
    Get total and weekly aggregate for a year for all variables
    with a given category. Only aggregate over the given location.
    
    Args:\n
        category: category\n
        location: location_id\n
        year: year (defaults to the current year)\n

    Returns:\n
        result_dict: {variable_id: AggregateYear result_dict}\n
    """
    decorators = [authenticate]
    
    def get(self, category, location_id, year=datetime.today().year):
        variables_instance = Variables()
        variables = variables_instance.get(category)
        aggregate_year = AggregateYear()

        return_data = {}
        for variable in variables.keys():
            return_data[variable] = aggregate_year.get(variable,
                                                       location_id,
                                                       year)
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
        
            
        
