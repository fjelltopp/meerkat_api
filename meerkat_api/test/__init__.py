#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the Meerkat API
"""
import json, os
import unittest
from datetime import datetime
import meerkat_api
import meerkat_abacus.data_management as manage
from meerkat_abacus.task_queue import app as celery_app
from meerkat_api.test import db_util

#Check if auth requirements have been installed
try:
    #Test by importing package that will only ever be required in auth (touch wood). 
    __import__('passlib')
    print( "Authentication requirements installed." )
except ImportError:
    print( "Authentication requirements not installed.  Installing them now." )
    os.system('pip install -r /var/www/meerkat_auth/requirements.txt') 

from . import settings

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
    csv_representations = ["export/get"]
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
        "end_date": datetime.now().isoformat(),
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
        "form": "demo_case",
        "date": datetime(2015, 1, 1).isoformat(),
        "link_def": "alert_investigation",
        "alert_id": "aaaaaa",
        "link_id": "1",
        "use_loc_ids": "1",
        "form_name": "demo_case",
        "weekend": "5,6",
        "use_loc_ids": "1",
        "lim_variable": "tot_1",
        "central_review": "crl_1",
        "mult_factor": "1000",
        "loc_id": "1",
        "level": "district",
        "uid": "1",
        "start_week": "1",
        "exclude": "mental",
        "non_reporting_variable": "reg_1"
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
        h = {**settings.header,**{"Accept": "text/csv"}}
        rv = app.get(url, headers=h)
    else:
        rv = app.get(url, headers=settings.header)
    return rv

class MeerkatAPITestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        celery_app.conf.CELERY_ALWAYS_EAGER = True

        BROKER_BACKEND = 'memory'
        # manage.set_up_everything(False, False, 500)
        db_util.insert_codes(meerkat_api.db.session)
        db_util.insert_locations(meerkat_api.db.session)
        db_util.insert_cases(meerkat_api.db.session, "public_health_report",
                             delete=True)
        db_util.insert_cases(meerkat_api.db.session,
                             "ncd_public_health_report", delete=False)
        db_util.insert_cases(meerkat_api.db.session, "ncd_report",
                             delete=False)
        db_util.insert_cases(meerkat_api.db.session, "pip_report",
                             delete=False)
        db_util.insert_cases(meerkat_api.db.session, "refugee_data",
                             delete=False)
        db_util.insert_cases(meerkat_api.db.session, "frontpage", delete=False)
        db_util.insert_cases(meerkat_api.db.session, "map_test", delete=False)
        db_util.insert_cases(meerkat_api.db.session, "epi_monitoring",
                             delete=False)
        db_util.insert_cases(meerkat_api.db.session, "malaria", delete=False)
        db_util.insert_cases(meerkat_api.db.session, "alerts", delete=False)
        db_util.insert_cases(meerkat_api.db.session, "cd_report", delete=False)
        db_util.insert_cases(meerkat_api.db.session, "vaccination_report",
                             delete=False)
        db_util.insert_cases(meerkat_api.db.session, "completeness",
                             delete=False)
        db_util.insert_cases(meerkat_api.db.session, "afro_report",
                             delete=False)
        
        self.app = meerkat_api.app.test_client()
        self.locations = {1: {"name": "Demo"}}
        self.variables = {1: {"name": "Total"}}

    def tearDown(self):
        pass

    def test_index(self):
        """Check the index page loads"""
        rv = self.app.get('/', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'WHO', rv.data)

    def test_all_urls(self):
        urls = valid_urls(meerkat_api.app)
        for url in urls:
            print(url)
            rv = get_url(self.app, url)
            isOK = rv.status_code == 200
            if not isOK:
                print( "URL NOT OK: " + str(url) )                
            self.assertEqual(rv.status_code, 200)   
    
        
    def test_authentication(self):
        #TODO: Test new authentication.
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
