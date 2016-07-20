#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the Meerkat API
"""
import json
import unittest
from datetime import datetime
from datetime import timedelta
from sqlalchemy import extract
import meerkat_api
import meerkat_abacus.manage as manage
import meerkat_abacus.config as config
import meerkat_abacus.model as model

from meerkat_api.test.test_alerts import *
from meerkat_api.test.test_reports import *

def need_csv_representation(url):
    """ 
    Checks if the url has a csv_representation.
    
    All urls that need a csv representation needs to be added to
    csv_representations. 

    Args:
       url: the url to check
    Returns:
       is_csv: True has csv representation
    """
    csv_representations = ["export/data", "export/form/", "export/alerts"]
    for r in csv_representations:
        if r in url:
            return True
    return False

def valid_urls(app):
    """ 
    Return all urls with a semi "sensible" subsitutions for arguments.
    
    All arguments need to have a subsitituion in the list in this function.
    
    Args: 
       app: meekrat_app
    Returns:
       urls: list of all urls
    """
    substitutions = {
        "location": "1",
        "location_id": "1",
        "start_date": datetime(2015, 1, 1).isoformat(),
        "end_date": datetime(2015, 12, 31).isoformat(),
        "variable_id": "tot_1",
        "variable": "tot",
        "group_by1": "gender",
        "group_by2": "age",
        "group_by": "gender",
        "only_loc": "2",
        "year": "2016",
        "category": "gender",
        "download_name": "cd",
        "epi_week": "2",
        "number_per_week": "5",
        "clinic_type": "Hospital",
        "form": "case",
        "date": datetime(2015, 1, 1).isoformat(),
        "link_def": "alert_investigation",
        "alert_id": "aaaaaa",
        "link_id": "1",
        "weekend": "5,6",
        "use_loc_ids": "1"
        }
    urls = []
    for url in meerkat_api.app.url_map.iter_rules():
        if "static" not in str(url):
            new_url = str(url)
            for arg in url.arguments:
                new_url = new_url.replace("<" + arg + ">",
                                          substitutions[arg])
            urls.append(new_url)
    return urls


def get_url(app, url):
    """ get a url from the app

    Args: 
        app: flask app
        url: url to get

    Returns: 
       rv: return variable
    """
    if need_csv_representation(url):
        rv = app.get(url, headers={"Accept": "text/csv"})
    else:
        rv = app.get(url)
    return rv

class MeerkatAPITestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        manage.set_up_everything(
            False, False, 500)

        self.app = meerkat_api.app.test_client()
        self.locations = {1: {"name": "Demo"}}
        self.variables = {1: {"name": "Total"}}
    def tearDown(self):
        pass

    def test_index(self):
        """Check the index page loads"""
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'WHO', rv.data)

    def test_all_urls(self):
        urls = valid_urls(meerkat_api.app)
        for url in urls:
            rv = get_url(self.app, url)
            self.assertEqual(rv.status_code, 200)
        
    def test_authentication(self):
        meerkat_api.app.config['API_KEY'] = "test-api"
        # rv = self.app.get("/test-authentication?api_key=test-api")
        # self.assertEqual(rv.status_code, 200)
        # rv = self.app.get("/test-authentication")
        # self.assertEqual(rv.status_code, 401)
        # rv = self.app.get("/test-authentication?api_key=not-real-key")
        # self.assertEqual(rv.status_code, 401)
        urls_without_authentication = ["/key_indicators", "/tot_map", "consultation_map", "num_alerts", "refugee_page", "/epi_week", "/epi_week_start", "/clinics", "/variables", "/variable", "/tot_clinics", "/locationtree", "/locations", "/location", "/num_clinics"]
        urls = valid_urls(meerkat_api.app)
        for url in sorted(urls, reverse=True):
            rv = get_url(self.app, url)

            no_auth = False
            for open_url in urls_without_authentication:
                if open_url in url or url == "/":
                    no_auth = True
                    self.assertEqual(rv.status_code, 200)
            if not no_auth:
                self.assertEqual(rv.status_code, 401)
                url += "?api_key=test-api"
                rv = get_url(self.app, url)
                self.assertEqual(rv.status_code, 200)
                wrong_key = url + "?api_key=wrong-key"
                rv = get_url(self.app, wrong_key)
                self.assertEqual(rv.status_code, 401)

if __name__ == '__main__':
    unittest.main()
