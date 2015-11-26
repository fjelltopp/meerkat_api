"""
Variables resource for querying variable data
"""
from flask_restful import Resource
from meerkat_api.util import row_to_dict, rows_to_dicts
from meerkat_api import db
from meerkat_abacus import model


class Variables(Resource):
    """
    Return variables

    Args:
        category: category of variables, category=all gives all variables
    """
    def get(self, category):
        if category != "all":
            results = db.session.query(model.AggregationVariables).filter(
                model.AggregationVariables.category.has_key(category))
        else:
            results = db.session.query(model.AggregationVariables)
        return rows_to_dicts(results.all(), dict_id="id")

    
class Variable(Resource):
    """
    Return variable
    
    Args:
        variable_id: id of variable to be returned
    """

    def get(self, variable_id):
        return row_to_dict(db.session.query(model.AggregationVariables).filter(
            model.AggregationVariables.id == variable_id).first())

