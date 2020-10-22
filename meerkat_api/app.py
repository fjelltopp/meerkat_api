"""
meerkat_api.py

Root Flask app for the Meerkat API.
"""
from flask import Flask
from flask.json import JSONEncoder
from datetime import datetime
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from raven.contrib.flask import Sentry
from werkzeug.middleware.proxy_fix import ProxyFix
from meerkat_libs.logger_client import FlaskActivityLogger
import os

from meerkat_api.extensions import db, api


# Set the default values of the g object
class FlaskG(Flask.app_ctx_globals_class):
    allowed_location = 1


# app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=(30,))
class CustomJSONEncoder(JSONEncoder):
    """
    Custom JSON encoder to encode all datetime objects as ISO fromat
    """

    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, WKBElement):
                shp_obj = to_shape(obj)
                if shp_obj.geom_type == "Point":
                    return shp_obj.coords
                if shp_obj.geom_type == "Polygon":
                    return shp_obj.exterior.coords
                else:
                    return None
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


def create_app():
    app = Flask(__name__)
    app.config.from_object(os.getenv('CONFIG_OBJECT', 'meerkat_api.config.Development'))
    app.config.from_envvar('MEERKAT_API_SETTINGS', silent=True)
    if os.environ.get("MEERKAT_API_DB_SETTINGS"):
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
            "MEERKAT_API_DB_URL"
        )
    register_extensions(app)
    app.app_ctx_globals_class = FlaskG
    app.json_encoder = CustomJSONEncoder
    return app


def register_extensions(app):
    db.init_app(app)
    api.init_app(app)
    FlaskActivityLogger(app)
    if app.config["SENTRY_DNS"]:
        sentry = Sentry(app, dsn=app.config["SENTRY_DNS"])
    app.wsgi_app = ProxyFix(app.wsgi_app)
