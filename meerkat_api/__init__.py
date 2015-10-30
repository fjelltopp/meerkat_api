"""
meerkat_api.py

Root Flask app for the Meerkat API.
"""
from flask import Flask

# Create the Flask app
app = Flask(__name__)
app.config.from_object('config.Development')
app.config.from_envvar('MEERKAT_API_SETTINGS', silent=True)


@app.route('/')
def hello_world():
    return 'Hello WHO!'
