"""
Resources for creating maps
"""
from flask_restful import Resource
from flask import abort
from geojson import Point, FeatureCollection, Feature
from sqlalchemy import extract, func, Integer, or_
from datetime import datetime

from meerkat_api.util import is_child, fix_dates
from meerkat_api import db, app
from meerkat_abacus import model
from meerkat_abacus.model import Data
from meerkat_abacus.util import get_locations
from meerkat_api.authentication import require_api_key

class Clinics(Resource):
    """
    Geojson for all clinics that are sublocation of location.

    Args:\n
        location_id: location that all other locations should be under\n
        clinic_type: If we should only get a specific clinic type (default=None)\n

    Returns:\n
        points: A geojson FeatureCollection of points\n
    """
    def get(self, location_id, clinic_type=None):
        locations = get_locations(db.session)
        points = []
        for l in locations:
            if (locations[l].case_report and is_child(
                    location_id, l, locations) and locations[l].geolocation
                and (not clinic_type or locations[l].clinic_type == clinic_type)):
                lat, lng = locations[l].geolocation.split(",")
                p = Point((float(lng), float(lat))) # Note that this is the specified order for geojson
                points.append(Feature(geometry=p,
                                      properties={"name":
                                                  locations[l].name}))
        return FeatureCollection(points)

class MapVariable(Resource):
    """
    Want to map a variable id by clinic (only include case reporting clinics)

    Args:\n
       variable_id: variable to map\n
       interval: the time interval to aggregate over (default=year)\n
       location: If we should restrict on location\n
       include_all_clinics: If true we include all clinics even with no cases\n

    Returns:\n
        map_data: [{value:0, geolocation: .., clinic:name},...]\n
    """
    decorators = [require_api_key]
    
    def get(self, variable_id, location=1, 
            start_date=None, end_date=None, include_all_clinics=False):

        start_date, end_date = fix_dates(start_date, end_date)
        location = int(location)
        vi = str(variable_id)
        year = datetime.now().year

        results = db.session.query(
            func.sum( Data.variables[vi].astext.cast(Integer) ).label('value'),
            Data.geolocation,
            Data.clinic
        ).filter( 
            Data.variables.has_key(variable_id ),
            Data.date >= start_date, 
            Data.date < end_date,
            or_(
                loc == location for loc in ( Data.country,
                                             Data.region,
                                             Data.district,
                                             Data.clinic)  
            )
        ).group_by("clinic", "geolocation")

        locations = get_locations(db.session)
        ret = {}
        for r in results.all():
            if r[1]:
                ret[r[2]] = {"value": r[0], "geolocation": r[1].split(","),
                             "clinic": locations[r[2]].name}

        if include_all_clinics:
            results = db.session.query(model.Locations)
            for row in results.all():
                if row.case_report and row.geolocation and row.id not in ret.keys():
                    ret[row.id] = {"value": 0,
                                   "geolocation": row.geolocation.split(","),
                                   "clinic": row.name}
        return ret

