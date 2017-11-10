"""
meerkat_api.py

Root Flask app for the Meerkat API.
"""
from meerkat_api.app import create_app

from meerkat_api.resources import alerts
from meerkat_api.resources import locations
from meerkat_api.resources import frontpage
from meerkat_api.resources import data
from meerkat_api.resources import export_data
from meerkat_api.resources import prescriptions
from meerkat_api.resources import explore
from meerkat_api.resources import variables
from meerkat_api.resources import reports
from meerkat_api.resources import map
from meerkat_api.resources import incidence
from meerkat_api.resources import indicators
from meerkat_api.resources import devices
from meerkat_api.resources import completeness
from meerkat_api.resources import epi_week

app = create_app()


@app.route('/')
def hello_world():
    return "WHO"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
