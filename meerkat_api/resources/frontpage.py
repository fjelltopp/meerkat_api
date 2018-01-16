"""
Resource for frontpage, so that certain data can be accessed without authentication
"""
from flask_restful import Resource
from flask import g
from datetime import datetime
from geoalchemy2.shape import to_shape

from meerkat_api.extensions import db, api
from meerkat_abacus.util import get_locations
from meerkat_api.util import get_children
from meerkat_api.resources.data import Aggregate
from meerkat_api.resources.map import MapVariable
from meerkat_api.resources.variables import Variables
from meerkat_api.resources.alerts import get_alerts
from meerkat_api.resources.reports import get_latest_category
from meerkat_api.resources.locations import TotClinics


class KeyIndicators(Resource):
    """
    Get the aggregation for all time of the variables with
    the key_indicators category.
    """

    def get(self, location=1):
        g.allowed_locations = location
        variables_instance = Variables()
        variables = variables_instance.get("key_indicators")
        aggregate = Aggregate()

        return_data = {}
        for variable in variables.keys():
            return_data[variable] = aggregate.get(variable, location)
        return return_data


class TotMap(Resource):
    """
    We map the total number of cases
    """

    def get(self, location=1):
        mv = MapVariable()
        g.allowed_locations = location
        return mv.get("tot_1", location=location, include_all_clinics=True)


class ConsultationMap(Resource):
    """
    Map the total number of consultations
    """

    def get(self, location=1):
        g.allowed_locations = location
        mv = MapVariable()
        return mv.get("reg_2", location=location, include_all_clinics=True)


class NumAlerts(Resource):
    """
    Total Number of Alerts
    """

    def get(self, location=1):
        g.allowed_locations = location
        alerts = get_alerts({"location": location}, allowed_location=location)
        return {"num_alerts": len(alerts)}


class NumClinics(Resource):
    """
    Return the total number of clinics for the country

    """

    def get(self, location=1):
        g.allowed_locations = location
        tc = TotClinics()
        return {"total": tc.get(location)["total"]}


class RefugeePage(Resource):
    """
    Map and key indicators for the Refugee page
    """

    def get(self):
        # First get clinics and total population
        locs = get_locations(db.session)
        refugee_clinics = get_children(1, locs, clinic_type="Refugee")
        tot_pop = 0
        clinic_map = []
        for clinic in refugee_clinics:
            result = get_latest_category("population", clinic,
                                         datetime(2015, 1, 1), datetime.now())
            clinic_pop = 0
            if (result):
                clinic_pop = sum(
                    [sum(result[x].values()) for x in result.keys()])

                tot_pop += clinic_pop
            geo = to_shape(locs[clinic].point_location)
            clinic_map.append({"value": clinic_pop,
                               "geolocation": [geo.y, geo.x],
                               "clinic": locs[clinic].name,
                               "location_id": clinic})
        return clinic_map


api.add_resource(KeyIndicators, "/key_indicators",
                 "/key_indicators/<int:location>")
api.add_resource(TotMap, "/tot_map",
                 "/tot_map/<int:location>")
api.add_resource(ConsultationMap, "/consultation_map",
                 "/consultation_map/<int:location>")
api.add_resource(NumAlerts, "/num_alerts",
                 "/num_alerts/<int:location>")
api.add_resource(NumClinics, "/num_clinics",
                 "/num_clinics/<int:location>")
api.add_resource(RefugeePage, "/refugee_page")
