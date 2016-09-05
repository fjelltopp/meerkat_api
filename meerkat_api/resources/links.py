"""
Data resource for getting link data
"""
from flask_restful import Resource
from flask import jsonify, request

from meerkat_api.util import row_to_dict, rows_to_dicts
from meerkat_api import app, db
from meerkat_abacus import model
from meerkat_abacus.util import get_locations
from meerkat_api.authentication import authenticate

class Link(Resource):
    """
    Get link by id

    Args:\n
        link_id\n

    Returns:\n
        link\n
    """
    decorators = [authenticate]
    def get(self, link_id):
        result = db.session.query(model.Links).filter(
            model.Links.id == link_id).one()
        return jsonify({"link": row_to_dict(result)})

class Links(Resource):
    """
    Get links by the link_definition id.

    Args:\n
        links_id\n

    Returns:\n
        link\n
    """
    decorators = [authenticate]

    def get(self, link_def):
        result = db.session.query(model.Links).filter(
            model.Links.link_def == link_def).all()
        return jsonify({"links": rows_to_dicts(result, dict_id="link_value")})
