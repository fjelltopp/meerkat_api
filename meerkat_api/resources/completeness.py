"""
Data resource for querying data
"""
from flask_restful import Resource
from flask import request
from sqlalchemy import or_, extract, func, Integer
from datetime import datetime, timedelta
from sqlalchemy.sql.expression import cast

from meerkat_api.util import row_to_dict, rows_to_dicts, date_to_epi_week
from meerkat_api.resources.locations import TotClinics
from meerkat_api import db,app
from meerkat_abacus.model import Data
from meerkat_abacus.util import get_locations, epi_week_start_date
from meerkat_api.resources.variables import Variables


class Completeness(Resource):
    """
    Return completenss data

    Args: 
        variable: variable_id
        number_per_week: expected number per week
    Returns:
        completness data: regions gives percentage of clinics with 
                          number_per_week records per week for last year, 
                          last week and last day

                          clinics gives number of records for last day, 
                          last year and last week
    """
    def get(self, variable, number_per_week):
        today = datetime.now()
        year = today.year
        epi_week_start = epi_week_start_date(year)
        epi_week = date_to_epi_week(today)
        number_per_week = int(number_per_week)
        results = db.session.query(
            func.sum(Data.variables[variable].astext.cast(Integer)).label('value'),
            func.floor(
                extract('days', Data.date -
                        epi_week_start) / 7 + 1).label("week"),
            Data.clinic,
            Data.region,
            
        ).filter(Data.variables.has_key(variable),
                 extract('year', Data.date) == year,

        ).group_by("week", "clinic","region")
        last_year = {1: 0}
        last_week = {1: 0}
        last_day = {1: 0}
        clinic_data = {1: {}}
        for r in results.all():
            last_year.setdefault(r[3], 0)
            clinic_data.setdefault(r[3], {})
            clinic_data[r[3]].setdefault(r[2],
                                         {"day": 0, "week": 0, "year": 0})
            clinic_data[1].setdefault(r[2], {"day": 0, "week": 0, "year": 0})
            clinic_data[r[3]][r[2]]["year"] += r[0]
            clinic_data[1][r[2]]["year"] += r[0]
            if r[0] >= number_per_week:
                last_year[r[3]] += number_per_week
                last_year[1] += number_per_week
            else:
                last_year[r[3]] += r[0]
                last_year[1] += r[0]
            if r[1] == epi_week:
                last_week.setdefault(r[3], 0)
                clinic_data[r[3]][r[2]]["week"] += r[0]
                clinic_data[1][r[2]]["week"] += r[0]
                if r[0] >= number_per_week:
                    last_week[r[3]] += number_per_week
                    last_week[1] += number_per_week
                else:
                    last_week[r[3]] += r[0]
                    last_week[1] += r[0]
        results_daily = db.session.query(
            func.sum(Data.variables[variable].astext.cast(Integer)).label('value'),
            Data.clinic,
            Data.region
        ).filter(Data.variables.has_key(variable),
                 Data.date >= today - timedelta(days=1)
        ).group_by("clinic", "region")
        for r in results_daily.all():
            last_day.setdefault(r[2], 0)
            clinic_data[r[2]][r[1]]["day"] += r[0]
            clinic_data[1][r[1]]["day"] += r[0]

            if r[0] >= 1:
                last_day[1] += 1
                last_day[r[2]] += 1

        n_clinics = {}
        first_date = db.session.query(func.min(Data.date)).first()[0]
        if first_date >= datetime(datetime.now().year, 1, 1):
            first_epi_week = date_to_epi_week(first_date)
            n_weeks = epi_week - first_epi_week
        else:
            n_weeks = epi_week
        region_data = {}
        for region in list(last_year.keys()) + [1]:
            n_clinics = len(clinic_data[region].keys())
            region_data[region] = {"last_day": last_day.get(region, 0)
                                   / n_clinics * 100,
                                   "last_week": last_week.get(region, 0)
                                   / (number_per_week * n_clinics) * 100,
                                   "last_year": last_year.get(region, 0)
                                   / (n_weeks * n_clinics * number_per_week) * 100}

        return {"regions": region_data, "clinics": clinic_data}
