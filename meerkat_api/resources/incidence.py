"""
Resource for aggregating and querying data

"""
from flask_restful import Resource
from datetime import datetime
from flask import g
from meerkat_api import db
from meerkat_abacus.model import Locations
from meerkat_api.authentication import authenticate, is_allowed_location
from meerkat_api.util.data_query import query_sum


class IncidenceRate(Resource):
    """
    Calculate the incidence rate for level and variable id
    
    Args:\n
        variable: variable_id\n
        level: clinic,district or region\n

    Returns:\n
        result: {"value": value}\n
    """

    decorators = [authenticate]

    def get(self, variable_id, level, mult_factor=1000,
            location_names=False, year=None, monthly=False,
            start_date=datetime(2010, 1, 1),
            end_date=datetime(2100, 1, 1)):
        mult_factor = int(mult_factor)
        if level not in ["zone", "region", "district", "clinic"]:
            return {}
        if year:
            year = datetime.now().year
            start_date = datetime(year, 1, 1)
            end_date = datetime(year + 1, 1, 1)
        if monthly:
            months = (datetime.now() - datetime(datetime.now().year, 1, 1)).days / 30.5
            mult_factor = mult_factor / months
        results = query_sum(
            db, [variable_id],
            start_date,
            end_date,
            g.allowed_location,
            level=level)
        locations = db.session.query(Locations).filter(
            Locations.level == level)
        pops = {}
        names = {}
        for l in locations:
            pops[l.id] = l.population
            names[l.id] = l.name
        ret = {}
        for loc in results[level].keys():
            if is_allowed_location(loc, g.allowed_location):
                if pops[loc]:
                    key = loc
                    if location_names:
                        key = names[key]
                    ret[key] = results[level][loc] / pops[loc] * mult_factor
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

    def get(self,
            variable_id,
            loc_id,
            mult_factor=1000,
            year=datetime.today().year):

        #Ensure stuff initialised properly.
        mult_factor = int(mult_factor)
        vi = str(variable_id)
        location_id = int(loc_id)
        year = int(year)

        results = query_sum(
            db, [vi],
            datetime(year, 1, 1),
            datetime(year + 1, 1, 1),
            location_id,
            weeks=True)

        #Structure the return data.
        ret = {"weeks": results["weeks"], "year": results["total"]}

        #Get population for specified location.
        location = db.session.query(Locations).filter_by(id=location_id).all()
        population = location[0].population

        #For each week and year value in ret, incidence = val/pop * mult_factor.
        for week in ret["weeks"]:
            ret["weeks"][week] = ret["weeks"][week] / population * mult_factor
        ret["year"] = ret["year"] / population * mult_factor

        return ret
