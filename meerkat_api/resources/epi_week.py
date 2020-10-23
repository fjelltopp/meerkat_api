"""
Resource to deal with epi-weeks
"""
import datetime
from dateutil.parser import parse, isoparse
from flask import jsonify
from flask_restful import Resource

from meerkat_api.extensions import api
import meerkat_abacus.util.epi_week as epi_week_util


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
            try:
                date = isoparse(date)
            except ValueError:
                date = parse(date, dayfirst=True)
        else:
            date = datetime.datetime.today()

        _epi_year, _epi_week_number = epi_week_util.epi_week_for_date(date)
        _epi_year_start_day_weekday = epi_week_util.epi_year_start_date(date).weekday()
        return jsonify(epi_week=_epi_week_number,
                       year=_epi_year,
                       offset=_epi_year_start_day_weekday)


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
        _epi_week_start_date = epi_week_util.epi_week_start_date(year, epi_week)
        return jsonify(start_date=_epi_week_start_date)


api.add_resource(EpiWeek, "/epi_week", "/epi_week/<date>")
api.add_resource(EpiWeekStart, "/epi_week_start/<year>/<epi_week>")
