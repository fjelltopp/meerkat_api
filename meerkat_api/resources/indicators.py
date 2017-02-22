import pandas as pd
from flask_restful import Resource
from sqlalchemy import or_
from meerkat_api import db
from meerkat_api.util import get_children
from meerkat_analysis.indicators import count_over_count, count
from meerkat_abacus.model import Data, Locations
from meerkat_abacus.util import get_locations
from meerkat_api.resources.completeness import series_to_json_dict
from meerkat_api.authentication import authenticate


class Indicators(Resource):
    """
    Return a value and a timeline of an indicator specified by a list of variables and flags. 

    Args: \n
        flags: A list containings char flags defining operations on variables. `d` - denominator of an indicator, `n` - nominator, `v` - additional variable to restrict query. `r` - restrict `count_over_count` query if set to `1`\n
        variables: A list of variables id to which flags correspond\n
        location: location id
    Returns:\n
        indicator_data: {cummulative: cummulative, timeline: timeline, current: current}\n
    """
    decorators = [authenticate]
    def get(self, flags, variables, location):
        bRestrict = False
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
                nominator = op[1]
            if op[0] == "v":
                restricted_var.append(op[1])
            if op[0] == "r" and op[1] == "1":
                bRestrict = True

        #Limit to location and nominator variable
        conditions = [Data.variables.has_key(nominator), or_(
            loc == location
            for loc in (Data.country, Data.region, Data.district, Data.clinic))
                     ]


        #Limit to given restrict variables
        for res_var in restricted_var:
            conditions.append(Data.variables.has_key(res_var))

        # Add denominator
        if(count_over):
            conditions.append(Data.variables.has_key(denominator))

        #Database query
        data = pd.read_sql(
            db.session.query(Data.region, Data.district, Data.clinic,
                             Data.date,
                             Data.variables[nominator].label(nominator)).filter(
                                 *conditions).statement, db.session.bind)
        print("debug data")
        print(data.describe())
        print(data.values)
        print("data.count")
        print("end debug data")

        # Prepare dummy data:
        indicator_data = dict()
        indicator_data["cummulative"] = -99
        indicator_data["timeline"] = {"w1":-99,"w2":99}
        #current value is the latest week:
        indicator_data["current"] = 999
        indicator_data["name"] = "Dummy Data"

        if data.empty:
            print("No records")
            return indicator_data


        #Call meerkat_analysis
        if(count_over):
            analysis_output = count_over_count(data, nominator, denominator, restrict=bRestrict)
        else:
            analysis_output = count(data, nominator)

        #Limit to location
        indicator_data = dict()
        # numpy.int64 needs to be cast to int (https://bugs.python.org/issue24313)
        indicator_data["cummulative"] = int(analysis_output[0])
        indicator_data["timeline"] = series_to_json_dict(analysis_output[1])
        #current value is the latest week:
        indicator_data["current"] = int(indicator_data["timeline"][max(
            indicator_data["timeline"].keys())])
        indicator_data["name"] = "Name is not passed to the API!"

        return indicator_data
