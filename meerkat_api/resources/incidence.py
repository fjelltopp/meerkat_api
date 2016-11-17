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
from meerkat_abacus.model import Data, Locations
from meerkat_api.authentication import authenticate
import logging

class IncidenceRate(Resource):
    """
    Calculate the incidence rate for level and variable id
    
    Args:\n
        variable: variable_id\nX
        level: clinic,district or region\n

    Returns:\n
        result: {"value": value}\n
    """
    
    decorators = [authenticate]
    
    def get(self, variable_id, level, mult_factor=1000, location_names=False):
        mult_factor = int(mult_factor)
        if level not in ["region", "district", "clinic"]:
            return {}
        results = db.session.query(getattr(Data, level),
                                   func.count(Data.id)).filter(
                                       Data.variables.has_key(variable_id)
                                   ).group_by(getattr(Data, level)).all()
        ret = {}
        
        locations = db.session.query(Locations).filter(Locations.level == level)
        pops = {}
        names = {}
        for l in locations:
            pops[l.id] = l.population
            names[l.id] = l.name
        for row in results:
            if row[0]:
                if pops[row[0]]:
                    key = row[0]
                    if location_names:
                        key = names[key]
                    ret[key] = row[1] / pops[row[0]] * mult_factor
        return ret

class WeeklyIncidenceRate(Resource):
    """
    Calculate the incidence rate for level and variable id
    
    Args:\n
        variable: variable_id\nX
        level: clinic,district or region\n

    Returns:\n
        result: {"value": value}\n
    """
    
    decorators = [authenticate]
    
    def get(self, variable_id, loc_id, mult_factor=1000, year=datetime.today().year):

        #Ensure stuff initialised properly.
        mult_factor = int(mult_factor)
        vi = str(variable_id)
        location_id = int(loc_id)
        year = int(year)
        epi_week_start = epi_year_start(year)

        #Get the variable data from the database aggregated over a year.
        results = db.session.query( 
            func.sum( Data.variables[vi].astext.cast(Float) ).label('value'),
            func.floor( extract('days', Data.date - epi_week_start) / 7 + 1).label("week") 
        ).filter(
            Data.variables.has_key(vi),
            extract('year', Data.date) == year,
            or_( loc == location_id for loc in ( Data.country, 
                                                 Data.region, 
                                                 Data.district, 
                                                 Data.clinic ) )
        ).group_by("week")

        #Structure the return data.
        weeks = dict((int(el[1]), el[0]) for el in results.all())
        ret = {"weeks": weeks, "year": sum(weeks.values())}

        #Get population for specified location.
        location = db.session.query(Locations).filter_by( id = location_id ).all()
        population = location[0].population

        #For each week and year value in ret, incidence = val/pop * mult_factor. 
        for week in ret["weeks"]:
            ret["weeks"][week] = ret["weeks"][week] / population * mult_factor
        ret["year"] = ret["year"] / population * mult_factor

        return ret

