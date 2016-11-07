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
            if pops[row[0]]:
                key = row[0]
                if location_names:
                    key = names[key]
                ret[key] = row[1] / pops[row[0]] * mult_factor
        return ret
