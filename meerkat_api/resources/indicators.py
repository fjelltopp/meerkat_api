import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from flask_restful import Resource
from flask import request
from sqlalchemy import or_, Float
from meerkat_api.extensions import db, api
from meerkat_api.util import series_to_json_dict
from meerkat_analysis.indicators import count_over_count, count, grouped_indicator
from meerkat_abacus.model import Data
from meerkat_api.authentication import authenticate
import meerkat_abacus.util.epi_week as ew
import time
import datetime
import logging


def prepare_indicator_output(analysis_output, mult_factor):
    """
    Takes the output from the analysis and constructs the correct output
    """
    indicator_data = dict()
    cummulative = analysis_output[0]
    if np.isnan(cummulative):
        cummulative = 0
    elif isinstance(cummulative, np.generic) or isinstance(cummulative, np.ndarray):
        cummulative = np.asscalar(cummulative)

    timeline = analysis_output[1] * mult_factor
    indicator_data["cummulative"] = cummulative * mult_factor
    indicator_data["timeline"] = series_to_json_dict(timeline)
    indicator_data["current"] = float(np.asscalar(timeline.iloc[-1]))
    indicator_data["previous"] = float(np.asscalar(timeline.iloc[-2]))
    indicator_data["name"] = "Name is not passed to the API!"
    return indicator_data


class Indicators(Resource):
    """
    Return a value and a timeline of an indicator specified by a list of
    variables and flags.

    Args: \n
        flags: A list containings char flags defining operations on variables.
            `d` - denominator of an indicator, `n` - numerator, `v` -
            additional variable to restrict query. `r` - restrict `
            count_over_count` query if set to `1`\n
        variables: A list of variables id to which flags correspond\n
        location: location id
    Returns:\n
        indicator_data:
            {cummulative: cummulative, timeline: timeline, current: current}\n
    """
    decorators = [authenticate]

    def get(self, flags, variables, location, start_date=None,
            end_date=None, current_year=None):
        current_year = request.args.get('current_year')
        group_by_level = request.args.get('group_by_level')
        if not start_date:
            if current_year == "1":
                this_year = datetime.datetime.now().year
                start_date = ew.epi_year_start_date_by_year(this_year).isoformat()
            else:
                one_year_ago = datetime.datetime.now().date() - relativedelta(years=1)
                start_date = one_year_ago.isoformat()
        s = time.time()
        mult_factor = 1
        count_over = False
        restricted_var = []
        variablesList = variables.split(',')
        flagsList = flags.split(',')

        operations = list(zip(flagsList, variablesList))

        for op in operations:
            if op[0] == "d":
                count_over = True
                denominator = op[1]
            if op[0] == "n":
                numerator = op[1]
            if op[0] == "v":
                restricted_var.append(op[1])
            if op[0] == "m":
                mult_factor = int(op[1])

        # Limit to location and numerator variable
        conditions = [or_(
            loc == location
            for loc in (Data.country, Data.zone,
                        Data.region, Data.district,
                        Data.clinic))
        ]
        conditions += [Data.date >= start_date]

        # Limit to given restrict variables
        for res_var in restricted_var:
            conditions.append(Data.variables.has_key(res_var))
        # Add denominator
        try:
            if count_over:
                if denominator is None or numerator is None:
                    return "Need both denominator and numerator"
                conditions.append(Data.variables.has_key(denominator))
                # Database query
                data = pd.read_sql(
                    db.session.query(Data.region, Data.district, Data.clinic,
                                     Data.date,
                                     Data.variables[numerator].astext.cast(Float).label(numerator),
                                     Data.variables[denominator].astext.cast(Float).label(denominator)
                                    ).filter(
                                        *conditions).statement, db.engine)
            else:
                conditions.append(Data.variables.has_key(numerator))
                data = pd.read_sql(
                    db.session.query(
                        Data.region, Data.district, Data.clinic,
                        Data.date, Data.variables[numerator].label(numerator)
                    ).filter(*conditions).statement, db.session.bind)
            data = data.fillna(0)

            if data.empty:
                logging.warning("Indicators: No records!!!")
                return {
                    "timeline": {},
                    "cummulative": 0,
                    "current": 0,
                    "previous": 0
                }
            # Call meerkat_analysis
            if group_by_level:
                if count_over:
                    analysis_output = grouped_indicator(
                        data, count_over_count, group_by_level,
                        numerator, denominator, start_date, end_date
                    )
                else:
                    analysis_output = grouped_indicator(
                        data, count, group_by_level, numerator,
                        start_date, end_date
                    )
                indicator_data = {}
                for key in analysis_output:
                    indicator_data[str(key)] = prepare_indicator_output(
                        analysis_output[key], mult_factor
                    )
                return indicator_data

            else:
                if count_over:
                    analysis_output = count_over_count(
                        data, numerator, denominator, start_date, end_date
                    )
                else:
                    analysis_output = count(
                        data, numerator, start_date, end_date
                    )
                return prepare_indicator_output(analysis_output, mult_factor)

        except (RuntimeError, TypeError, NameError, IndexError) as err:
            logging.error(err)
            logging.error("Not enough data avaliable to show the indicator")
            return {
                "timeline": [],
                "cummulative": 0,
                "current": 0,
                "previous": 0
            }


api.add_resource(
    Indicators, "/indicators/<flags>/<variables>/<location>",
    "/indicators/<flags>/<variables>/<location>/<start_date>/<end_date>"
)
