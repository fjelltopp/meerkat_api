"""
Resource for frontpage, so that certain data can be accessed without authentication
"""
from flask_restful import Resource
from sqlalchemy import or_, extract, func, Integer
from datetime import datetime
from sqlalchemy.sql.expression import cast
import json

from meerkat_api import db, app
from meerkat_abacus.util import epi_week_start_date
from meerkat_api.resources.data import AggregateCategory
from meerkat_api.resources.map import MapVariable
from meerkat_api.resources.alerts import Alerts


class KeyIndicators(Resource):
    """
    Get key indicators
    """
    def get(self):
        ac = AggregateCategory()
        return ac.get("key_indicators", 1)
        

class TotMap(Resource):
    """
    Get map fro frontpage
    """
    def get(self):
        mv = MapVariable()
        return mv.get("tot_1")
class ConsultationMap(Resource):
    """
    Get map fro frontpage
    """
    def get(self):
        mv = MapVariable()
        return mv.get("reg_1")

class NumAlerts(Resource):
    """
    Get map fro frontpage
    """
    def get(self):
        al = Alerts()
        data = json.loads(al.get().data.decode("utf-8"))
        return {"num_alerts": len(data["alerts"])}

    
