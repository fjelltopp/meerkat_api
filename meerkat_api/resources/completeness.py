"""
Data resource for completeness data
"""
from flask_restful import Resource
from flask import jsonify, request, g
from dateutil.parser import parse
from sqlalchemy import extract, func, Integer, or_
from datetime import datetime, timedelta
import pandas as pd
import json
from meerkat_api.extensions import db, api
from meerkat_api.resources.epi_week import EpiWeek, epi_week_start, epi_year_start
from meerkat_abacus.model import Data, Locations
from meerkat_api.util import get_children, is_child, series_to_json_dict, get_locations
from meerkat_api.authentication import authenticate, is_allowed_location
from pandas.tseries.offsets import CustomBusinessDay


class Completeness(Resource):
    """
    Return completeness data of variable. We calculate both a score based on
    the average of the last two epi weeks and a timeline of the average number
    of records per week. We only allow one record per day.

    We include_case_type data for both the given location and the sublocations.

    Args: \n
        variable: variable_id\n
        location: location id
        number_per_week: expected number per week\n
    argument `weekend`, specify exclude_case_type as a string `None`\n
        weekend: specified weekend days in a comma separated string 0=Mon.
    Returns:\n
        completness data: {score: score, timeline: timeline, clinic_score:
        clinic:score, clinic_yearly_score: clinic:yearly_score,
        dates_not_reported: dated_not_reported, yearly_score: yearly_score}\n
    """
    decorators = [authenticate]

    def get(self, variable, location, number_per_week,
            weekend=None, start_week=1, end_date=None,
            non_reporting_variable=None, sublevel=None):
        inc_case_types = set(
            json.loads(request.args.get('inc_case_types', '[]'))
        )
        exc_case_types = set(
            json.loads(request.args.get('exc_case_types', '[]'))
        )
        if sublevel is None:
            sublevel = request.args.get('sublevel')
        if not is_allowed_location(location, g.allowed_location):
            return {}

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
        if not sublevel:
            zones = db.session.query(func.count(Locations.id)).filter(
                Locations.level == 'zone'
            ).first()
            sublevels = {"country": "region",
                         "region": "district",
                         "district": "clinic",
                         "clinic": None}

            if zones[0] > 0:
                sublevels["country"] = "zone"
                sublevels["zone"] = "region"
            sublevel = sublevels[location_type]
        conditions = [
            Data.variables.has_key(variable), or_(
                loc == location
                for loc in (Data.country, Data.zone,
                            Data.region, Data.district, Data.clinic)
            ),
        ]
        if exc_case_types and exc_case_types != []:
            conditions.append(~Data.case_type.contains(exc_case_types))
        if inc_case_types and inc_case_types != []:
            conditions.append(Data.case_type.overlap(inc_case_types))
        if "tag" in request.args.keys():
            conditions.append(Data.tags.has_key(request.args["tag"]))
        # get the data
        data = pd.read_sql(
            db.session.query(Data.region, Data.zone, Data.district,
                             Data.clinic, Data.date,
                             Data.variables[variable].label(variable)).filter(
                                 *conditions).statement, db.session.bind)
        if len(data) == 0:
            return jsonify({"score": {},
                            "timeline": {},
                            "clinic_score": {},
                            "clinic_yearly_score": {},
                            "dates_not_reported": [],
                            "yearly_score": {}})

        # If end_date is the start of an epi week we do not want to include_case_type the current epi week
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
                if is_child(location, l.id, locs) and l.level == sublevel:
                    sublocations.append(l.id)
            tuples = []
            for name in sublocations:
                for clinic in get_children(name, locs):
                    if locs[clinic].case_report:
                        if inc_case_types and not set(locs[clinic].case_type) & inc_case_types:
                            continue
                        if exc_case_types and set(locs[clinic].case_type) & exc_case_types:
                            continue
                        start_date = locs[clinic].start_date
                        if start_date < begining:
                            start_date = begining
                        if end_d - start_date < timedelta(days=7):
                            start_date = (end_d - timedelta(days=6)).date()
                        for d in pd.date_range(start_date, end_d, freq=freq):
                            tuples.append((name, clinic, d))
            if len(tuples) == 0:
                return jsonify({})
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
            non_reporting_clinics = nr.get(non_reporting_variable, location )["clinics"]
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
            not_reported_dates_begining = begining
            if end_d - begining < timedelta(days=7):
                begining = (end_d - timedelta(days=6)).date()

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
            expected_days = pd.date_range(not_reported_dates_begining, end_d, freq=bdays)

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
        exclude_case_type: Exclude locations with this case_type\n
        num_weeks: number_of_weeks \n


    Returns:\n
        list_of_clinics
    """
    decorators = [authenticate]

    def get(self, variable, location, exclude_case_type=None, num_weeks=0,
            include_case_type=None, include_clinic_type=None, require_case_report=True):


        if not is_allowed_location(location, g.allowed_location):
            return {}

        if require_case_report in [0, "0"]:
            require_case_report = False
        if num_weeks == "0":
            num_weeks = 0

        if exclude_case_type in [0, "0", "None"]:
            exclude_case_type = None
        if include_case_type in [0, "0", "None"]:
            include_case_type = None
        if include_clinic_type in [0, "0", "None"]:
            include_clinic_type = None


        locations = get_locations(db.session)
        location = int(location)
        clinics = get_children(location, locations,
                               require_case_report=require_case_report)
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
        exclude_list = []
        if exclude_case_type and "code:" in exclude_case_type:
            query = db.session.query(Data.clinic).filter(Data.variables.has_key(exclude_case_type.split(":")[1]))
            exclude_list = [r[0] for r in query.all()]

        query = db.session.query(Data.clinic).filter(*conditions)
        clinics_with_variable = [r[0] for r in query.all()]
        non_reporting_clinics = []

        if include_clinic_type:
            if "," in include_clinic_type:
                include_clinic_type = set(include_clinic_type.split(","))
            else:
                include_clinic_type = set([include_clinic_type])
        if include_case_type:
            if "," in include_case_type:
                include_case_type = set(include_case_type.split(","))
            else:
                include_case_type = set([include_case_type])
        if exclude_case_type and "code:" not in exclude_case_type:
            if "," in exclude_case_type:
                exclude_case_type = set(exclude_case_type.split(","))
            else:
                exclude_case_type = set([exclude_case_type])
        for clinic in clinics:
            if include_clinic_type and locations[clinic].clinic_type not in include_clinic_type:
                continue
            if clinic not in clinics_with_variable:
                if len(exclude_list) > 0:
                    if clinic in exclude_list:
                        continue
                if include_case_type:
                    if set(locations[clinic].case_type) & include_case_type:
                        non_reporting_clinics.append(clinic)
                elif exclude_case_type:
                    if not set(locations[clinic].case_type) & exclude_case_type:
                        non_reporting_clinics.append(clinic)

                else:
                    non_reporting_clinics.append(clinic)
        return {"clinics": non_reporting_clinics}



api.add_resource(NonReporting,
                 "/non_reporting/<variable>/<location>",
                 "/non_reporting/<variable>/<location>/<num_weeks>/<exclude_case_type>",
                 "/non_reporting/<variable>/<location>/<num_weeks>/<exclude_case_type>/<include_case_type>",
                 "/non_reporting/<variable>/<location>/<num_weeks>/<exclude_case_type>/<include_case_type>/<include_clinic_type>/<require_case_report>"
)

api.add_resource(Completeness,
                 "/completeness/<variable>/<location>/<number_per_week>",
                 "/completeness/<variable>/<location>/<number_per_week>/<start_week>",
                 "/completeness/<variable>/<location>/<number_per_week>/<start_week>/<weekend>",
                 "/completeness/<variable>/<location>/<number_per_week>/<start_week>/<weekend>/<non_reporting_variable>",
                 "/completeness/<variable>/<location>/<number_per_week>/<start_week>/<weekend>/<non_reporting_variable>/<end_date>")
