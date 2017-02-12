import pandas as pd
from flask_restful import Resource
from sqlalchemy import or_
from meerkat_api import db
from meerkat_api.util import get_children
from meerkat_analysis.indicators import count_over_count, count
from meerkat_abacus.model import Data, Locations
from meerkat_abacus.util import get_locations
from meerkat_api.resources.completeness import series_to_json_dict

class Indicators(Resource):
    def get(self, variable, location):
        # end_date = datetime.now()

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
        data = pd.read_sql(
            db.session.query(Data.region, Data.district, Data.clinic,
                             Data.date,
                             Data.variables[variable].label(variable)).filter(
                                 *conditions).statement, db.session.bind)
        print(data.describe())
        print(data.values)
        denominator_id = variable
        whateverItIs = count(data, denominator_id)
        print(type(whateverItIs))
        print(type(whateverItIs[0]))
        print(type(whateverItIs[1]))
        zz = whateverItIs[1]
        print( type(zz) )
        zzz = series_to_json_dict(zz)
        print( type(zzz) )
        return zzz
