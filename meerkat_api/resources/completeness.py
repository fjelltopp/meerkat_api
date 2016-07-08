"""
Data resource for completeness data
"""
from flask_restful import Resource
from flask import jsonify
from sqlalchemy import extract, func, Integer, or_
from datetime import datetime, timedelta
import pandas as pd

from meerkat_api import db, app
from meerkat_api.resources.epi_week import EpiWeek, epi_week_start
from meerkat_abacus.model import Data, Locations
from meerkat_api.util import get_children
from meerkat_abacus.util import get_locations, epi_week_start_date
from meerkat_api.authentication import require_api_key
from meerkat_abacus.util import get_locations
from pandas.tseries.offsets import CustomBusinessDay

def series_to_json_dict(series):
    """
    Takes pandas series and turns into a dict with string keys

    Args: 
        series: pandas series
    
    Returns: 
       dict: dict
    """
    if series is not None:
        return dict( (str(key), value) for key, value in series.to_dict().items())
    else:
        return {}

class NewCompleteness(Resource):
    """
    Return completeness data of variable. We calculate both a score based on the average of the last two epi weeks 
    and a timeline of the average number of records per week. We only allow one record per day. 

    We include data for both the given location and the sublocations. 

    Args: \n
        variable: variable_id\n
        location: location id
        number_per_week: expected number per week\n
        weekend: specified weekend days in a comma separated string 0=Mon
    Returns:\n
        completness data: {score: score, timeline: timeline, clinic_score: clinic:score, dates_not_reported: dated_not_reported}\n
    """
    def get(self, variable, location, number_per_week, weekend=None):
        today = datetime.now()
        epi_year_weekday = epi_week_start_date(today.year).weekday()
        freq = ["W-MON", "W-TUE", "W-WED",
                "W-THU", "W-FRI", "W-SAT", "W-SUN"][epi_year_weekday]

        number_per_week = int(number_per_week)
        locs = get_locations(db.session)
        location = int(location)
        location_type = locs[location].level
        sublevels = {"country": "region",
                    "region": "district",
                    "district": "clinic",
                    "clinic": None}
        sublevel = sublevels[location_type]

        # get the data
        data = pd.read_sql(
            db.session.query(Data.region,
                             Data.district,
                             Data.clinic,
                             Data.date,
                             Data.variables[variable].label(variable)
            ).filter(Data.variables.has_key(variable),
                     or_(loc == location for loc in (Data.country,
                                                     Data.region,
                                                     Data.district,
                                                     Data.clinic))).statement,
            db.session.bind)

        if len(data) == 0:
            return {}

        # If today is the start of an epi week we do not want to include the current epi week
        if today.weekday() == epi_year_weekday:
            end_d = today - timedelta(days=1)
        else:
            end_d = today
            
        begining = epi_week_start_date(today.year)
        # We drop duplicates so each clinic can only have one record per day
        data = data.drop_duplicates(subset=["region", "district", "clinic", "date", variable])

        if sublevel:
            # We first create an index with sublevel, clinic, dates
            # Where dates are the dates after the clinic started reporting
            sublocations = []
            for l in locs.values():
                if l.parent_location == location and l.level == sublevel:
                    sublocations.append(l.id)
            tuples = []
            for name in sublocations:
                for clinic in get_children(name, locs):
                    start_date = locs[clinic].start_date
                    if start_date < begining:
                        start_date = begining
                    for d in pd.date_range(start_date, end_d, freq=freq):
                        tuples.append((name, clinic, d))

            new_index = pd.MultiIndex.from_tuples(tuples,
                                                  names=[sublevel, "clinic", "date"])

            completeness = data.groupby(
                [sublevel ,
                 "clinic",
                 pd.TimeGrouper(key="date", freq=freq, label="left")]
            ).sum().reindex(new_index)[variable].fillna(0).sort_index()

            # We only want to count a maximum of number per week per week
            completeness[completeness > number_per_week] = number_per_week
            
            location_completeness_per_week = completeness.groupby(level=2).mean()
            sublocations_completeness_per_week = completeness.groupby(level=[0,2]).mean()

            # Find last two weeks 
            idx = pd.IndexSlice
            last_two_weeks = location_completeness_per_week.index[-2:]

            # Get sublocation completeness for last two weeks as a percentage
            completeness_last_two_weeks = sublocations_completeness_per_week.loc[idx[:, last_two_weeks]]
            score = completeness_last_two_weeks.groupby(level=0).mean() / number_per_week * 100
            
            # Add current location 
            score[location] = location_completeness_per_week[last_two_weeks].mean() / number_per_week * 100

            # Sort the timeline data 
            timeline = {}
            for sl in sublocations_completeness_per_week.index.get_level_values(sublevel):
                sl_time = sublocations_completeness_per_week.iloc[
                sublocations_completeness_per_week.index.get_level_values(sublevel) == sl]
                timeline[str(sl)] = {
                    "weeks": sl_time.index.get_level_values("date"),
                    "values": sl_time}
            # Add current location 
            timeline[str(location)] = {
                "weeks": location_completeness_per_week.index,
                "values": location_completeness_per_week
            }
            # Calculate completness score for each clinic
            clinic_completeness_last_two_weeks = completeness.loc[idx[:,:,last_two_weeks]]
            clinic_scores = clinic_completeness_last_two_weeks.groupby(level=1).mean() / number_per_week * 100
            dates_not_reported = [] # Not needed for this level
            
        else:
            # Take into account clinic start_date 
            if locs[location].start_date > begining:
                begining = locs[location].start_date
            dates = pd.date_range(begining, end_d, freq=freq)
            completeness = data.groupby(
                pd.TimeGrouper(key="date", freq=freq, label="left")
            ).sum().fillna(0)[variable].reindex(dates).sort_index().fillna(0)
            
            timeline = {str(location): {
                "weeks": completeness.index.to_pydatetime(),
                "values": completeness.values}
            }
            last_two_weeks = completeness.index[-2:]
            score = pd.Series() 
            score.loc[location] = completeness[last_two_weeks].mean() / number_per_week * 100

            # Sort out the dates on which nothing was reported
            # Can specify on which weekdays we expect a record
            
            if not weekend:
                weekday_mask = "Mon Tue Wed Thu Fri"
            else:
                weekend = weekend.split(",")
                weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                weekday_mask = ""
                for i, w in enumerate(weekdays):
                    if i not in weekend and str(i) not in weekend:
                        weekday_mask = weekday_mask + weekdays[i] + " "
            
            bdays = CustomBusinessDay(weekmask=weekday_mask)
            expected_days = pd.date_range(begining, end_d, freq=bdays)

            found_dates = data["date"]
            dates_not_reported = expected_days.drop(
                found_dates.values,
                errors="ignore"
            ).to_pydatetime()
            clinic_scores = None # Not needed for this level

        return jsonify({"score": series_to_json_dict(score),
                        "timeline": timeline,
                        "clinic_score": series_to_json_dict(clinic_scores),
                        "dates_not_reported": dates_not_reported})

class NonReporting(Resource):
    """
    Returns all non-reporting clinics for the last num_weeks complete epi weeks .

    Args: \n
        variable: variable_id\n
        location: location\n
        num_weeks: number_of_weeks \n
   

    Returns:\n
        list_of_clinics
    """
    def get(self, variable, location, num_weeks=2):
        locations = get_locations(db.session)
        location = int(location)
        clinics = get_children(location, locations)
        ew = EpiWeek()
        epi_week = ew.get()
        start_date = epi_week_start(epi_week["year"],
                                    epi_week["epi_week"]) - timedelta(days=7 * num_weeks)
        clinics_with_variable = [ r[0] for r in db.session.query(Data.clinic).filter(
            Data.variables.has_key(variable), Data.date > start_date).all()]
        non_reporting_clinics = []
        for clinic in clinics:
            if clinic not in clinics_with_variable:
                non_reporting_clinics.append(clinic)

        return {"clinics": non_reporting_clinics}















    
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
        epi_year = epi_week_start_date(year)
        epi_week = ew.get(today.isoformat())["epi_week"]
        number_per_week = int(number_per_week)

        # SQL query that extracts the number of records with variable in the current year, grouped by epi_week
        # clinic and region.
        results = db.session.query(
            func.sum(Data.variables[variable].astext.cast(Integer)).label('value'),
            func.floor(
                extract('days', Data.date -
                        epi_year) / 7 + 1).label("week"),
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
                
            if r[1] == epi_week - 1:
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
        # days_in_current_week = (today - epi_week_start(today.year, epi_week)).days + 1
        # if number_per_week > days_in_current_week:
        #     number_per_week_for_epi = days_in_current_week
        # else:
        #     number_per_week_for_epi = number_per_week
        for region in list(last_year.keys()) + [1]:
            # For each region we find the number of clinics and calculate
            # the sum of the number of records / time_frame * n_clinics.
            n_clinics = len(clinic_data[region].keys())
            if n_clinics == 0:
                n_clinics = 1
                app.logger.info(variable)
            app.logger.info(region)
            app.logger.info(last_week.get(region, 0))
            app.logger.info(n_clinics)
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
