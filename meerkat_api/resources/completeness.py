"""
Data resource for completeness data
"""
import json

import pandas as pd
import meerkat_abacus.util as abacus_util
from datetime import datetime, timedelta
from dateutil.parser import parse
from flask import jsonify, request, g
from flask_restful import Resource, abort
from pandas.tseries.offsets import CustomBusinessDay
from sqlalchemy import func, or_

from meerkat_abacus.model import Data, Locations
from meerkat_api.authentication import authenticate, is_allowed_location
from meerkat_api.extensions import db, api
from meerkat_api.resources.epi_week import EpiWeek
from meerkat_api.util import get_children, series_to_json_dict


class CompletenessIndicator(Resource):
    """ 
    Return completeness data in indicator format 
    {"timeline": timeline,
     "cumulative": yearly_score,
    "current: "last_week_score", 
    "previous": "next_to_last_score"
    }
    """
    decorators = [authenticate]

    def get(self, variable, location, number_per_week, start_week=1, exclude=None):
        c = Completeness()

        completeness_data = json.loads(c.get(variable, location,
                                             number_per_week,
                                             start_week=start_week,
                                             exclude=exclude).data)
        cumulative = completeness_data["yearly_score"].get(location, 0)
        current = completeness_data["score"].get(location, 0)
        timeline = completeness_data["timeline"].get(location, {"values": [], "weeks": []})

        if timeline["values"]:
            factor = current / timeline["values"][-1]
            previous = timeline["values"][-2] * factor
        else:
            factor = 1
            previous = 0
        new_timeline = {}

        for i in range(len(timeline["values"])):
            new_timeline[timeline["weeks"][i]] = timeline["values"][i] * factor
        return {
            "cumulative": cumulative,
            "current": current,
            "previous": previous,
            "timeline": new_timeline
        }


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
        if not is_allowed_location(location, g.allowed_location):
            return {}

        if not non_reporting_variable:
            non_reporting_variable = variable

        number_per_week = int(number_per_week)
        locs = abacus_util.get_locations(db.session)
        location = int(location)
        location_type = locs[location].level

        parsed_sublevel = self._get_sublevel(location_type, sublevel)

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
            return jsonify(self.__empty_response)
        # We drop duplicates so each clinic can only have one record per day
        data = data.drop_duplicates(
            subset=["region", "district", "clinic", "date", variable])
        shifted_end_date, timeseries_freq = self._get_shifted_end_date_and_timeseries_frequency(end_date)

        beginning_of_epi_start_week = self._get_epi_week_start(shifted_end_date, start_week)

        if parsed_sublevel:
            # We first create an index with sublevel, clinic, dates
            # Where dates are the dates after the clinic started reporting
            sublocations = []
            for l in locs.values():
                if abacus_util.is_child(location, l.id, locs) and l.level == parsed_sublevel:
                    sublocations.append(l.id)
            tuples = []
            for name in sublocations:
                for clinic in get_children(name, locs):
                    if locs[clinic].case_report:
                        if inc_case_types and not set(locs[clinic].case_type) & inc_case_types:
                            continue
                        if exc_case_types and set(locs[clinic].case_type) >= exc_case_types:
                            continue
                        start_date = locs[clinic].start_date
                        if start_date < beginning_of_epi_start_week:
                            start_date = beginning_of_epi_start_week
                        if shifted_end_date - start_date < timedelta(days=7):
                            start_date = (shifted_end_date - timedelta(days=6)).date()

                        for date in pd.date_range(start_date, shifted_end_date, freq=timeseries_freq):
                            tuples.append((name, clinic, date))
            if len(tuples) == 0:
                return jsonify(self.__empty_response)

            new_index = pd.MultiIndex.from_tuples(
                tuples, names=[parsed_sublevel, "clinic", "date"])
            completeness = data.groupby([
                parsed_sublevel, "clinic", pd.TimeGrouper(
                    key="date", freq=timeseries_freq, label="left")
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
                    parsed_sublevel):
                sl_time = sublocations_completeness_per_week.iloc[
                    sublocations_completeness_per_week.index.get_level_values(
                        parsed_sublevel) == sl]
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
            if locs[location].start_date > beginning_of_epi_start_week:
                beginning_of_epi_start_week = locs[location].start_date
            not_reported_dates_begining = beginning_of_epi_start_week
            if shifted_end_date - beginning_of_epi_start_week < timedelta(days=7):
                beginning_of_epi_start_week = (shifted_end_date - timedelta(days=6)).date()

            dates = pd.date_range(beginning_of_epi_start_week, shifted_end_date, freq=timeseries_freq)
            completeness = data.groupby(
                pd.TimeGrouper(
                    key="date", freq=timeseries_freq, label="left")).sum().fillna(0)[
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

            bdays = self._get_business_days(weekend_days=weekend)

            expected_days = pd.date_range(not_reported_dates_begining, shifted_end_date, freq=bdays)

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

    def _get_sublevel(self, location_type, raw_sublevel):
        sublevels = self._get_sublevels_dict()
        result = raw_sublevel
        if raw_sublevel is None:
            result = request.args.get('sublevel')
        if result not in sublevels.values():
            abort(404, message='Unsupported sublevel: "{}" provided.'.format(result))
        if not result:
            result = sublevels[location_type]
        return result

    def _get_sublevels_dict(self):
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
        return sublevels

    def _get_epi_week_start(self, shifted_end_date, start_week):
        beginning = abacus_util.epi_week_start(shifted_end_date.year, start_week)
        ew = EpiWeek()
        if ew.get(shifted_end_date.isoformat())["epi_week"] == 53:
            beginning = beginning.replace(year=beginning.year - 1)

        return beginning

    def _get_shifted_end_date_and_timeseries_frequency(self, raw_end_date):
        # If end_date is the start of an epi week we do not want to include_case_type the current epi week
        # We only calculate completeness for whole epi-weeks so we want to set end_date to the
        # the end of the previous epi_week.
        end_date = self._parse_end_date(raw_end_date)
        epi_year_start_weekday = abacus_util.epi_year_start_date_by_year(year=end_date.year).weekday()
        timeseries_freq = ["W-MON", "W-TUE", "W-WED", "W-THU", "W-FRI", "W-SAT", "W-SUN"][epi_year_start_weekday]
        offset = (end_date.weekday() - epi_year_start_weekday) % 7
        shifted_end_date = end_date - timedelta(days=offset + 1)
        return shifted_end_date, timeseries_freq

    def _parse_end_date(self, end_date):
        if not end_date:
            end_date = datetime.now()
        else:
            if isinstance(end_date, str):
                end_date = parse(end_date)
        return end_date

    def _get_business_days(self, weekend_days):
        if not weekend_days:
            weekday_mask = "Mon Tue Wed Thu Fri"
        else:
            weekend_days = weekend_days.split(",")
            weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            weekday_mask = ""
            for i, w in enumerate(weekdays):
                if i not in weekend_days and str(i) not in weekend_days:
                    weekday_mask = weekday_mask + weekdays[i] + " "
        bdays = CustomBusinessDay(weekmask=weekday_mask)
        return bdays

    __empty_response = {
        "score": {},
        "timeline": {},
        "clinic_score": {},
        "clinic_yearly_score": {},
        "dates_not_reported": [],
        "yearly_score": {}
    }


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

        inc_case_types = set(
            json.loads(request.args.get('inc_case_types', '[]'))
        )
        exc_case_types = set(
            json.loads(request.args.get('exc_case_types', '[]'))
        )

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

        locations = abacus_util.get_locations(db.session)
        location = int(location)
        clinics = get_children(location, locations,
                               require_case_report=require_case_report)
        conditions = [Data.variables.has_key(variable)]
        if num_weeks:
            ew = EpiWeek()
            epi_week = ew.get()
            start_date = abacus_util.epi_week_start(epi_week["year"],
                                        int(epi_week["epi_week"]) - int(num_weeks))
            end_date = abacus_util.epi_week_start(epi_week["year"],
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
            if inc_case_types:
                include_case_type = inc_case_types.union(include_case_type)
        elif inc_case_types:
            include_case_type = inc_case_types

        if exclude_case_type and "code:" not in exclude_case_type:
            if "," in exclude_case_type:
                exclude_case_type = set(exclude_case_type.split(","))
            else:
                exclude_case_type = set([exclude_case_type])
            if exc_case_types:
                exclude_case_type = exc_case_types.union(exclude_case_type)
        elif exc_case_types:
            exclude_case_type = exc_case_types

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
                elif exclude_case_type and "code:" not in exclude_case_type:
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
