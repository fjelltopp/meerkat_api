"""
Data resource for querying data
"""
from flask_restful import Resource
from sqlalchemy import or_, extract, func, Integer
from datetime import datetime
from sqlalchemy.sql.expression import cast

from meerkat_api.util import row_to_dict, rows_to_dicts, date_to_epi_week
from meerkat_api import db, app
from meerkat_abacus.model import Data
from meerkat_abacus.util import epi_week_start_date
from meerkat_api.resources.variables import Variables
from meerkat_api.authentication import require_api_key


class Aggregate(Resource):
    """
    Get total Aggregate over all time
    
    Args:
        variable: variable_id
        location: location_id
    Returns:
        {"value": value}
    """
    decorators = [require_api_key]
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
    Get total and weekly aggregate for a year
    
    Args:
        variable: variable_id
        location: location_id
        year: year
    Reutrns:
    result_dict: {"weeks":{1:0....}, "year":0}
    """
    decorators = [require_api_key]
    def get(self, variable_id, location_id, year=datetime.today().year):
        year = int(year)
        vi = str(variable_id)
        epi_week_start = epi_week_start_date(year)
        results = db.session.query(
            func.sum(Data.variables[vi].astext.cast(Integer)).label('value'),
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
    with category
    
    Args:
        category: category
        location: location_id
        year: year
    Returns:
        result_dict: {variable_id: AggregateYear result_dict}
    """
    decorators = [require_api_key]
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
