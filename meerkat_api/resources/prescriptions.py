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
from meerkat_api.util import get_children, is_child
from meerkat_abacus.util import get_locations
from meerkat_api.authentication import authenticate
from meerkat_abacus.util import get_locations


class Prescriptions(Resource):
    """
    Return medicine prescription data based on scanned barcodes

    Args: \n
        location: location id
            Returns:\n
\n
    """
    decorators = [authenticate]

    def get(self, location, start_date = None, end_date = None):
        return {"message":"Work in progress"}