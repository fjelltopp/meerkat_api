"""
meerkat_api.py

Root Flask app for the Meerkat API.
"""
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask_restful import Api

from meerkat_abacus import config
from meerkat_abacus import model

# Create the Flask app
app = Flask(__name__)
app.config.from_object('config.Development')
app.config.from_envvar('MEERKAT_API_SETTINGS', silent=True)
db = SQLAlchemy(app)
api = Api(app)

from meerkat_api.resources.locations import Location, Locations

api.add_resource(Locations, "/locations")
api.add_resource(Location, "/location/<location_id>")


@app.route('/')
def hello_world():
    return 'Hello WHO 2!'
