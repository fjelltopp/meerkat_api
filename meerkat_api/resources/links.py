"""
Data resource for getting link data
"""
from flask_restful import Resource
from flask import jsonify, request, current_app
from sqlalchemy import or_, extract, func, Integer
from datetime import datetime
from sqlalchemy.sql.expression import cast

from meerkat_api.util import row_to_dict, rows_to_dicts, date_to_epi_week, get_children
from meerkat_api import app, db
from meerkat_abacus import model
from meerkat_abacus.util import get_locations
from meerkat_api.resources.variables import Variables
from meerkat_api.authentication import require_api_key



class Link(Resource):
    """
    Get links with id
    
    Args:
        link_id
    Returns:
        link
    """
    decorators = [require_api_key]
    def get(self, link_id):
        result = db.session.query(model.Links).filter(
            model.Links.id == link_id).one()
        return jsonify({"link": row_to_dict(result)})


class Links(Resource):
    """
    Get links with certain type
    
    Args:
        links_id
    Returns:
        link
    """
    decorators = [require_api_key]
    def get(self, links_id):
        result = db.session.query(model.Links).filter(
            model.Links.link_def == links_id).all()
        return jsonify({"links": rows_to_dicts(result, dict_id="link_value")})
