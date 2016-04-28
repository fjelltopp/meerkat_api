"""
Variables resource for querying variable data
"""
from flask_restful import Resource
from meerkat_api.util import row_to_dict, rows_to_dicts
from meerkat_api import db, app
from meerkat_abacus import model
from meerkat_api.resources import locations

class Variables(Resource):
    """
    Return variables. If category=all we return all variables.
    If cateogry=locations or locations: we return locations.
    If category=alert we return variables which triggers alerts. 

    Args:\n
        category: category of variables\n
    """
    def get(self, category):
        if category == "locations" or "locations:" in category:
            l = locations.Locations()
            return l.get()
        elif category == "alert":
            results = db.session.query(model.AggregationVariables).filter(
                model.AggregationVariables.alert == 1)
        elif category != "all":
            results = db.session.query(model.AggregationVariables).filter(
                model.AggregationVariables.category.has_key(category))
        else:
            results = db.session.query(model.AggregationVariables)
        return rows_to_dicts(results.all(), dict_id="id")

    
class Variable(Resource):
    """
    Returns a variable
    
    Args:\n
        variable_id: id of variable to be returned\n
    """

    def get(self, variable_id):
        return row_to_dict(db.session.query(model.AggregationVariables).filter(
            model.AggregationVariables.id == variable_id).first())

