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
from meerkat_api.util import get_children
from meerkat_abacus.util import get_locations
from meerkat_api.authentication import authenticate
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
        return dict((str(key), value)
                    for key, value in series.to_dict().items())
    else:
        return {}


class Completeness(Resource):
    """
    Return completeness data of variable. We calculate both a score based on
    the average of the last two epi weeks and a timeline of the average number
    of records per week. We only allow one record per day.

    We include data for both the given location and the sublocations.

    Args: \n
        variable: variable_id\n
        location: location id
        number_per_week: expected number per week\n
        exclude: Exclude locations with this case_type. In order to provide
    argument `weekend`, specify exclude as a string `None`\n
        weekend: specified weekend days in a comma separated string 0=Mon.
    Returns:\n
        completness data: {score: score, timeline: timeline, clinic_score: clinic:score, 
        clinic_yearly_score: clinic:yearly_score, dates_not_reported: dated_not_reported,
        yearly_score: yearly_score}\n
    """
    decorators = [authenticate]

    def get(self, variable, location, number_per_week, exclude=None,
            weekend=None, start_week=1, end_date=None, non_reporting_variable=None):
        if not end_date:
            end_date = datetime.now()
        else:
            if isinstance(end_date, str):
                end_date = parse(end_date)
        if not non_reporting_variable:
            non_reporting_variable = variable
        epi_year_weekday = epi_year_start(end_date.year).weekday()
        freq = ["W-MON", "W-TUE", "W-WED", "W-THU", "W-FRI", "W-SAT",
                "W-SUN"][epi_year_weekday]

        number_per_week = int(number_per_week)
        locs = get_locations(db.session)
        location = int(location)
        location_type = locs[location].level
        sublevels = {"country": "region",
                     "region": "district",
                     "district": "clinic",
                     "clinic": None}
        sublevel = sublevels[location_type]

        conditions = [Data.variables.has_key(variable), or_(
            loc == location
            for loc in (Data.country, Data.region, Data.district, Data.clinic))
                      ]
        if exclude and exclude != "None":
            conditions.append(or_(Data.case_type is not None,
                                  Data.case_type != exclude))
        if "tag" in request.args.keys():
            conditions.append(Data.tags.has_key(request.args["tag"]))
        # get the data

        data = pd.read_sql(
            db.session.query(Data.region, Data.district, Data.clinic,
                             Data.date,
                             Data.variables[variable].label(variable)).filter(
                                 *conditions).statement, db.session.bind)
        if len(data) == 0:
            return jsonify({"score": {},
                            "timeline": {},
                            "clinic_score": {},
                            "clinic_yearly_score": {},
                            "dates_not_reported": [],
                            "yearly_score": {}})

        # If end_date is the start of an epi week we do not want to include the current epi week
        # We only calculate completeness for whole epi-weeks so we want to set end_d to the
        # the end of the previous epi_week.
        offset = end_date.weekday() - epi_year_weekday
        if offset < 0:
            offset = 7 + offset
        end_d = end_date - timedelta(days=offset + 1)


        begining = epi_week_start(end_date.year, start_week)
        ew = EpiWeek()
        week = ew.get(end_d.isoformat())
        if ew.get(end_d.isoformat())["epi_week"] == 53:
            begining = begining.replace(year=begining.year -1)
            
        # We drop duplicates so each clinic can only have one record per day
        data = data.drop_duplicates(
            subset=["region", "district", "clinic", "date", variable])

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
                    if locs[clinic].case_report:
                        start_date = locs[clinic].start_date
                        if start_date < begining:
                            start_date = begining
                        for d in pd.date_range(start_date, end_d, freq=freq):
                            tuples.append((name, clinic, d))
            if len(tuples) == 0:
                return {}
            new_index = pd.MultiIndex.from_tuples(
                tuples, names=[sublevel, "clinic", "date"])

            completeness = data.groupby([
                sublevel, "clinic", pd.TimeGrouper(
                    key="date", freq=freq, label="left")
            ]).sum().reindex(new_index)[variable].fillna(0).sort_index()

            # Drop clinics with no submissions

            clinic_sums = completeness.groupby(level=1).sum()
            zero_clinics = clinic_sums[clinic_sums == 0].index

            nr = NonReporting()
            non_reporting_clinics = nr.get(non_reporting_variable, location)["clinics"]
            completeness = completeness.drop(non_reporting_clinics, level=1)
            completeness.reindex()

            # We only want to count a maximum of number per week per week
            completeness[completeness > number_per_week] = number_per_week

            location_completeness_per_week = completeness.groupby(
                level=2).mean()
            sublocations_completeness_per_week = completeness.groupby(
                level=[0, 2]).mean()

            # Find last two weeks
            idx = pd.IndexSlice
            last_two_weeks = location_completeness_per_week.index[-1:]
            last_year = location_completeness_per_week.index[:]

            # Get sublocation completeness for last two weeks as a percentage
            completeness_last_two_weeks = sublocations_completeness_per_week.loc[
                idx[:, last_two_weeks]]
            score = completeness_last_two_weeks.groupby(
                level=0).mean() / number_per_week * 100
            completeness_last_year = sublocations_completeness_per_week.loc[
                idx[:, last_year]]
            yearly_score = completeness_last_year.groupby(
                level=0).mean() / number_per_week * 100

            # Add current location
            score[location] = location_completeness_per_week[
                last_two_weeks].mean() / number_per_week * 100
            yearly_score[location] = location_completeness_per_week.mean(
            ) / number_per_week * 100

            # Sort the timeline data
            timeline = {}
            for sl in sublocations_completeness_per_week.index.get_level_values(
                    sublevel):
                sl_time = sublocations_completeness_per_week.iloc[
                    sublocations_completeness_per_week.index.get_level_values(
                        sublevel) == sl]
                timeline[str(sl)] = {
                    "weeks": sl_time.index.get_level_values("date"),
                    "values": sl_time
                }
            # Add current location
            timeline[str(location)] = {
                "weeks": location_completeness_per_week.index,
                "values": location_completeness_per_week
            }
            # Calculate completness score for each clinic
            clinic_completeness_last_two_weeks = completeness.loc[
                idx[:, :, last_two_weeks]]
            clinic_scores = clinic_completeness_last_two_weeks.groupby(
                level=1).mean() / number_per_week * 100
            clinic_completeness_last_year = completeness.loc[idx[:, :, :]]
            clinic_yearly_scores = clinic_completeness_last_year.groupby(
                level=1).mean() / number_per_week * 100
            dates_not_reported = []  # Not needed for this level

        else:
            # Take into account clinic start_date
            if locs[location].start_date > begining:
                begining = locs[location].start_date
            dates = pd.date_range(begining, end_d, freq=freq)
            completeness = data.groupby(
                pd.TimeGrouper(
                    key="date", freq=freq, label="left")).sum().fillna(0)[
                        variable].reindex(dates).sort_index().fillna(0)

            # We only want to count a maximum of number per week per week
            completeness[completeness > number_per_week] = number_per_week

            timeline = {str(location): {
                "weeks":
                [d.isoformat() for d in completeness.index.to_pydatetime()],
                "values": [float(v) for v in completeness.values]
            }}
            last_two_weeks = completeness.index[-1:]
            score = pd.Series()
            score.loc[location] = completeness[last_two_weeks].mean(
            ) / number_per_week * 100
            yearly_score = pd.Series()
            yearly_score.loc[location] = completeness.mean(
            ) / number_per_week * 100

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
                found_dates.values, errors="ignore").to_pydatetime()
            dates_not_reported = [d.isoformat() for d in dates_not_reported]
            clinic_scores = None  # Not needed for this level
            clinic_yearly_scores = None  # Not needed for this level

        return jsonify({"score": series_to_json_dict(score),
                        "timeline": timeline,
                        "clinic_score": series_to_json_dict(clinic_scores),
                        "clinic_yearly_score":
                        series_to_json_dict(clinic_yearly_scores),
                        "dates_not_reported": dates_not_reported,
                        "yearly_score": series_to_json_dict(yearly_score)})


class NonReporting(Resource):
    """
    Returns all non-reporting clinics for the last num_weeks complete epi weeks.

    Args: \n
        variable: variable_id\n
        location: location\n
        exclude: Exclude locations with this case_type\n
        num_weeks: number_of_weeks \n
   

    Returns:\n
        list_of_clinics
    """
    decorators = [authenticate]

    def get(self, variable, location, exclude=None, num_weeks=0,
            include=None, require_case_report=True):
        if require_case_report in [0, "0"]:
            require_case_report = False
        locations = get_locations(db.session)
        location = int(location)
        clinics = get_children(location, locations, require_case_report=require_case_report)
        #clinics = [l for l in locations.keys() if locations[l].level == "clinic"]
        conditions = [Data.variables.has_key(variable)]

        if num_weeks:
            ew = EpiWeek()
            epi_week = ew.get()
            start_date = epi_week_start(epi_week["year"],
                                        int(epi_week["epi_week"]) - int(num_weeks))
            end_date = epi_week_start(epi_week["year"],
                                        epi_week["epi_week"])
            conditions.append(Data.date >= start_date)
            conditions.append(Data.date < end_date)
        
        query = db.session.query(Data.clinic).filter(*conditions)
        
        clinics_with_variable = [r[0] for r in query.all()]
        non_reporting_clinics = []
        for clinic in clinics:
            if clinic not in clinics_with_variable:
                if include:
                    if locations[clinic].clinic_type == include:
                        non_reporting_clinics.append(clinic)
                elif exclude:
                    if locations[clinic].case_type != exclude:
                        non_reporting_clinics.append(clinic)
                else:
                    non_reporting_clinics.append(clinic)

        return {"clinics": non_reporting_clinics}


    
