"""
Data resource for completeness data
"""
from flask_restful import Resource
from sqlalchemy import extract, func, Integer
from datetime import datetime, timedelta

from meerkat_api import db, app
from meerkat_api.resources.epi_week import EpiWeek
from meerkat_abacus.model import Data, Locations
from meerkat_abacus.util import get_locations, epi_week_start_date
from meerkat_api.authentication import require_api_key


class Completeness(Resource):
    """
    Return completenss data on region and clinic level.

    On the regional level we gives percentage of clinics with at least number_per_week records with variable per week for the last year, 
    the last week and the last day. Clinics gives number of records for last day, last year and last week. For the regional data we only 
    count clinics with at least 1 record this year. 

    Args: \n
        variable: variable_id\n
        number_per_week: expected number per week\n

    Returns:\n
        completness data: {regions: region_data, clinics: clinic_data}\n
    """
    decorators = [require_api_key]

    def get(self, variable, number_per_week):
        today = datetime.now()
        year = today.year
        ew = EpiWeek()
        epi_week_start = epi_week_start_date(year)
        epi_week = ew.get(today.isoformat())["epi_week"]
        number_per_week = int(number_per_week)

        # SQL query that extracts the number of records with variable in the current year, grouped by epi_week
        # clinic and region.
        results = db.session.query(
            func.sum(Data.variables[variable].astext.cast(Integer)).label('value'),
            func.floor(
                extract('days', Data.date -
                        epi_week_start) / 7 + 1).label("week"),
            Data.clinic,
            Data.region,
        ).filter(Data.variables.has_key(variable),
                 extract('year', Data.date) == year
        ).group_by("week", "clinic","region")

        # We index all th results arrays by region_id
        last_year = {1: 0} # 1 is the location id for the whole country
        last_week = {1: 0}
        last_day = {1: 0}
        clinic_data = {1: {}}

        for r in results.all():
            # r[0]: is the number of records per week
            # r[1] is th epi_week
            # r[2] is the clinic
            # r[3] is th region
            
            last_year.setdefault(r[3], 0)
            clinic_data.setdefault(r[3], {})
            clinic_data[r[3]].setdefault(r[2],
                                         {"day": 0, "week": 0, "year": 0})
            clinic_data[1].setdefault(r[2], {"day": 0, "week": 0, "year": 0})
            clinic_data[r[3]][r[2]]["year"] += r[0]
            clinic_data[1][r[2]]["year"] += r[0]
            
            if r[0] >= number_per_week:
                # We count number_per_week + X as number_per week, to get an accurate percentage
                last_year[r[3]] += number_per_week
                last_year[1] += number_per_week
            else:
                last_year[r[3]] += r[0]
                last_year[1] += r[0]
                
            if r[1] == epi_week:
                # Last week
                last_week.setdefault(r[3], 0)
                clinic_data[r[3]][r[2]]["week"] += r[0]
                clinic_data[1][r[2]]["week"] += r[0]
                if r[0] >= number_per_week:
                    last_week[r[3]] += number_per_week
                    last_week[1] += number_per_week
                else:
                    last_week[r[3]] += r[0]
                    last_week[1] += r[0]

        # Query the number of records in the last 24 hours
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
                # For percentages we count > 1 as 1. 
                last_day[1] += 1
                last_day[r[2]] += 1



        # We find the date of the earliest Data record, to use a start date if
        # it is before the 1st of the January of the current year.
        # We then calculate n_weeks as the number of epi_weeks since then

        first_date = db.session.query(func.min(Data.date)).first()[0]
        if first_date >= datetime(datetime.now().year, 1, 1):
            first_epi_week = ew.get(first_date.isoformat())["epi_week"]
            n_weeks = epi_week - first_epi_week
        else:
            n_weeks = epi_week
        region_data = {}
        n_clinics = {}
        for region in list(last_year.keys()) + [1]:
            # For each region we find the number of clinics and calculate
            # the sum of the number of records / time_frame * n_clinics.
            n_clinics = len(clinic_data[region].keys())
            if n_clinics == 0:
                n_clinics = 1
            region_data[region] = {"last_day": last_day.get(region, 0)
                                   / n_clinics * 100,
                                   "last_week": last_week.get(region, 0)
                                   / (number_per_week * n_clinics) * 100,
                                   "last_year": last_year.get(region, 0)
                                   / (n_weeks * n_clinics * number_per_week) * 100}

        # Get all clinics that send should send case_reports. As the above code will not
        # find clinics with 0 records. 

        results = db.session.query(Locations).filter(Locations.case_report == 1)
        locations = get_locations(db.session)
        for row in results.all():
            if row.case_report and row.id not in clinic_data[1].keys():
                clinic_data[1][row.id] = {"day": 0, "week": 0, "year": 0}
                parent_loc = row.parent_location
                while parent_loc not in clinic_data.keys():
                    parent_loc = locations[parent_loc].parent_location
                clinic_data[parent_loc][row.id] = {"day": 0, "week": 0, "year": 0}

        return {"regions": region_data, "clinics": clinic_data}
