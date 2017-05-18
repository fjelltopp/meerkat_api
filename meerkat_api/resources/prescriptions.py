"""
Data resource for completeness data
"""
from flask_restful import Resource
from flask import jsonify, request
from dateutil.parser import parse
from sqlalchemy import extract, func, Integer, or_
from datetime import datetime, timedelta
import pandas as pd

from meerkat_api import db, app
from meerkat_api.resources.epi_week import EpiWeek, epi_week_start, epi_year_start
from meerkat_abacus.model import Data, Locations
from meerkat_api.util import get_children, is_child, fix_dates
from meerkat_abacus.util import get_locations
from meerkat_api.authentication import authenticate

from meerkat_api.resources.explore import QueryVariable, get_variables


kit_contents= {
    "barcode_albe": {
        "total":2,
        "dose":1,
        "tablets_in_kit":200
    },
    "barcode_magn": {
        "total":1,
        "dose":2,
        "tablets_in_kit":1000
    },
    "barcode_amox": {
        "total":30,
        "dose":2,
        "tablets_in_kit":3000
    },
    "barcode_benz": {
        "total":1,
        "dose":10,
        "tablets_in_kit":1
    },
    "barcode_chlo": {
        "total":1,
        "dose":"",
        "tablets_in_kit":""
    },
    "barcode_fefu": {
        "total":2,
        "dose":2,
        "tablets_in_kit":2000
    },
    "barcode_ibup": {
        "total":20,
        "dose":2,
        "tablets_in_kit":200
    },
    "barcode_mico": {
        "total":20,
        "dose":"",
        "tablets_in_kit":""
    },
    "barcode_orsl": {
        "total":2,
        "dose":"",
        "tablets_in_kit":""
    },
    "barcode_par1": {
        "total":10,
        "dose":20,
        "tablets_in_kit":1000
    },
    "barcode_par5": {
        "total":20,
        "dose":1,
        "tablets_in_kit":2000
    },
    "barcode_povi": {
        "total":12,
        "dose":"",
        "tablets_in_kit":""
    },
    "barcode_tetr": {
        "total":50,
        "dose":"",
        "tablets_in_kit":""
    },
    "barcode_zinc": {
        "total":10,
        "dose":2,
        "tablets_in_kit":1000
    }
}


class Prescriptions(Resource):
    """
    Return medicine prescription data based on scanned barcodes

    Args: \n
        location: location id
            Returns:\n
    """
    decorators = [authenticate]

    def get(self, location, start_date = None, end_date = None):

        start_date, end_date = fix_dates(start_date, end_date)

        locs = get_locations(db.session)
        clinics = get_children(parent = location, locations = locs, require_case_report = True)

        barcode_category = 'barcode_prescription'

        barcode_variables = get_variables(barcode_category)

        date_conditions = [Data.date >= start_date, Data.date < end_date]

        conditions = [Data.categories.has_key(barcode_category), Data.clinic.in_(clinics)]
        
        # Get first and last prescription for a clinic and medicine without time constraints
        first_last_prescr_query = db.session.query(Data.clinic,
                             Data.categories[barcode_category].astext,func.count(Data.id),func.min(Data.date),func.max(Data.date)).filter(
                                 *conditions).group_by(Data.clinic, Data.categories[barcode_category].astext)
        
        # Get first and last prescription for a clinic without time constraints
        clinic_info = db.session.query(Data.clinic,
                             func.count(Data.id),func.min(Data.date),func.max(Data.date)).filter(
                                 *conditions).group_by(Data.clinic)

        conditions = [Data.categories.has_key(barcode_category)] + date_conditions

        # Get number of prescriptions within time constraints
        prescription_query = db.session.query(Data.clinic,
                             Data.categories[barcode_category].astext,func.count(Data.id)).filter(
                                 *conditions).group_by(Data.clinic, Data.categories[barcode_category].astext)



        prescriptions = {}

        # Restructure the DB return sets into a JSON
        for item in first_last_prescr_query.all():
            # If clinic is already in JSON 
            if str(item[0]) in prescriptions.keys():
                prescriptions[str(item[0])].update({
                    str(item[1]):{
                        "min_date":item[3].strftime("%Y-%m-%d"),
                        "max_date":item[4].strftime("%Y-%m-%d"),
                        "total_prescriptions":item[2],
                        "inventory":
                            (0 
                                if kit_contents[item[1]]["tablets_in_kit"] == "" 
                                else int(kit_contents[item[1]]["tablets_in_kit"]) - item[2]
                            ) 
                        }
                    })
            # If clinic is not in the JSON object yet    
            else:
                prescriptions.update({
                    str(item[0]):{
                        str(item[1]):
                            {
                            "min_date":item[3].strftime("%Y-%m-%d"),
                            "max_date":item[4].strftime("%Y-%m-%d"),
                            "total_prescriptions":item[2],
                            "inventory":
                                (0 
                                    if kit_contents[item[1]]["tablets_in_kit"] == "" 
                                    else int(kit_contents[item[1]]["tablets_in_kit"]) - item[2]
                                ) 
                            }
                        }
                    })

        # Assign the number of prescriptions to data object
        for item in prescription_query.all():
            prescriptions[str(item[0])][str(item[1])]['prescriptions'] = item[2]

        for item in clinic_info.all():
            prescriptions[str(item[0])].update({
                "min_date":item[2].strftime("%Y-%m-%d"),
                "max_date":item[3].strftime("%Y-%m-%d")
                })


        return prescriptions
        
