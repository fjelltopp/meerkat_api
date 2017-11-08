"""
Resource to deal with epi-weeks
"""
import datetime
from dateutil.parser import parse
from flask import jsonify
from flask_restful import Resource

import meerkat_abacus.util as abacus_util
from meerkat_api.extensions import api


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

        start_date = abacus_util.epi_year_start_date(date=date)
        if date < start_date:
            start_date = start_date.replace(year=start_date.year - 1)
        year = start_date.year

        if date < start_date:
            year = start_date.year + 1

        return {"epi_week": (date - start_date).days // 7 + 1,
                "year": year,
                "offset": abacus_util.epi_week_start_date(date.year, 1).weekday()}


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
        return jsonify(start_date=abacus_util.epi_week_start_date(year, epi_week))


api.add_resource(EpiWeek, "/epi_week",
                 "/epi_week/<date>")
api.add_resource(EpiWeekStart, "/epi_week_start/<year>/<epi_week>")
