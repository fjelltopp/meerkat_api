"""
Resource to deal with epi-weeks
"""
from flask_restful import Resource
from dateutil.parser import parse
import datetime
from flask import jsonify

# The epi_week start date is defined in the meerkat_abacus configs
from meerkat_abacus.util import epi_week_start_date

class EpiWeek(Resource):
    """
    Get epi week of date(defaults to today)
    
    Args:\n
        date: date to get epi-week\n
    Returns:\n
        epi-week: epi-week\n
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
        
        return {"epi_week":(date - start_date).days // 7 + 1,
                "year": year,
                "offset": start_date.weekday()}
class EpiWeekStart(Resource):
    """
    Return the start date of an epi week in the given year

    Args:\n
        epi-week: epi week\n
        year: year\n
    Returns:
        start-date: start-date\n
    """
    def get(self, year, epi_week):
        return jsonify(start_date=epi_week_start(year, epi_week))

def epi_week_start(year, epi_week):
    """
    Calculates the start of an epi week:

    Args:
        epi-week: epi week
        year: year
    Returns:
        start-date: start-date
    """

    start_date = epi_week_start_date(int(year))
    start_date =  start_date + datetime.timedelta(weeks=int(epi_week) - 1)
    return start_date
