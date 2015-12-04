"""
Epi-week resource for querying variable data
"""
from flask_restful import Resource
from dateutil.parser import parse
import datetime
from flask import jsonify

from meerkat_abacus.util import epi_week_start_date

class EpiWeek(Resource):
    """
    Get the epi week of data
    
    Args:
        date: date to get epi-week
    Returns:
        epi-week: epi-week
    """
    def get(self, date=None):
        if date:
            date = parse(date)
        else:
            date = datetime.datetime.today()
        start_date = epi_week_start_date(date.year)
        if date < start_date:
            start_date = start_date.replace(year=start_date.year-1)
        year = start_date.year
        
        return {"epi-week":(date - start_date).days // 7 + 1,
                "year": year}


class EpiWeekStart(Resource):
    """
    Return the start date of an epi week"

    Args:
        epi-week: epi week
    Returns:
        start-date: start-date
    """
    def get(self, year, epi_week):
        start_date = epi_week_start_date(int(year))
        start_date =  start_date + datetime.timedelta(weeks=int(epi_week) - 1)
        return jsonify(start_date=start_date)

