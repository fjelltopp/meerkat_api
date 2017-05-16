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

        conditions = [Data.categories.has_key(barcode_category)] + date_conditions

        
        prescription_query = db.session.query(Data.clinic,
                             Data.categories[barcode_category].astext,func.count(Data.id)).filter(
                                 *conditions).group_by(Data.clinic, Data.categories[barcode_category].astext)

        prescriptions = {}


        #115,
        #"barcode_fefu",
        #5


        for item in prescription_query.all():
            if str(item[0]) in prescriptions.keys():
                prescriptions[str(item[0])].update({
                    item[1]:item[2]})
            else:
                prescriptions.update({
                    str(item[0]):{
                            item[1]:item[2]
                        }
                    })



        return prescriptions
        

        #select clinic, categories->>'barcode_prescription', count(*) 
        # from data where categories->>'barcode_prescription' is not null group by clinic, categories->>'barcode_prescription';
