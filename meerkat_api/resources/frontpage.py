"""
Resource for frontpage, so that certain data can be accessed without authentication
"""
from flask_restful import Resource
from sqlalchemy import or_
from datetime import datetime
import json

from meerkat_api import db, app
from meerkat_abacus.util import epi_week_start_date, get_locations
from meerkat_abacus.model import Data
from meerkat_api.util import get_children
from meerkat_api.resources.data import AggregateCategory, Aggregate
from meerkat_api.resources.map import MapVariable
from meerkat_api.resources.reports import get_variables_category
from meerkat_api.resources.alerts import Alerts
from meerkat_api.resources.reports import get_latest_category
from meerkat_api.resources.locations import TotClinics


class KeyIndicators(Resource):
    """
    Get the aggregation for this year of the variables with the key_indicators category.
    """
    def get(self):
        ac = AggregateCategory()
        return ac.get("key_indicators", 1)

class TotMap(Resource):
    """
    We map the total number of cases
    """
    def get(self):
        mv = MapVariable()
        return mv.get("tot_1", include_all_clinics=True)
    
class ConsultationMap(Resource):
    """
    Map the total number of consultations
    """
    def get(self):
        mv = MapVariable()
        return mv.get("reg_2", include_all_clinics=True)

class NumAlerts(Resource):
    """
    Total Number of Alerts
    """
    def get(self):
        al = Alerts()
        data = json.loads(al.get().data.decode("utf-8"))
        return {"num_alerts": len(data["alerts"])}
class NumClinics(Resource):
    """
    Return the total number of clinics for the country

    """
    def get(self):
        tc = TotClinics()
        return {"total": tc.get(1)["total"]}
    
class RefugeePage(Resource):
    """
    Map and key indicators for the Refugee page
    """
    def get(self):
        # First get clinics and total population
        ret = {}
        locs = get_locations(db.session)
        refugee_clinics = get_children(1, locs, clinic_type="Refugee")
        tot_pop = 0
        clinic_map = []
        for clinic in refugee_clinics:
            result = get_latest_category("population", clinic, datetime(2015, 1, 1),
                                         datetime.now())
            clinic_pop = 0
            if(result):
                clinic_pop = sum([sum(result[x].values()) for x in result.keys() ])

                tot_pop += clinic_pop
            clinic_map.append({"value": clinic_pop,
                               "geolocation": locs[clinic].geolocation.split(","),
                               "clinic": locs[clinic].name,
                               "location_id": clinic
                               })
        return clinic_map
