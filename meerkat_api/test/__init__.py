#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the Meerkat API
"""
import os
import unittest
from unittest.mock import patch

from datetime import datetime

import meerkat_api
from meerkat_abacus.task_queue import app as celery_app
from meerkat_api.test import db_util

# Check if auth requirements have been installed
try:
    # HACK: Test by importing package that will only ever be required in auth
    __import__('passlib')
    print("Authentication requirements installed.")
except ImportError:
    print("Authentication requirements not installed.  Installing them now.")
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
        "device_id": "4",
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
        "non_reporting_variable": "reg_1",
        "data_type": "case",
        "weekly": "1",
        "identifier_id": 'tot_1',
        "include": "CTC",
        "num_weeks": "2",
        "require_case_report": "0",
        "restrict_by": "tot_1",
        "weeks": "1",
        "hard_date_limit": "2017-01-01",
        "monthly": "1",
        "flags": "n",
        "variables": "gen_1",
        "include_case_type": "mh",
        "exclude_case_type": "mh",
        "include_clinic_type": "Refugee"
    }
    excluded_urls = [
        '/devices/submissions/<variable_id>'
    ]
    urls = []
    for url in meerkat_api.app.url_map.iter_rules():
        str_url = str(url)
        if "static" not in str_url and str_url not in excluded_urls:
            new_url = str_url
            for arg in url.arguments:
                new_url = new_url.replace("<" + arg + ">",
                                          substitutions[arg])
                new_url = new_url.replace("<int:" + arg + ">",
                                          substitutions[arg])
            urls.append(new_url)
    return urls


def get_url(app, url, header):
    """ get a url from the app

    Args:
        app: flask app
        url: url to get

    Returns:
       rv: return variable
    """
    if need_csv_representation(url):
        h = {**header, **{"Accept": "text/csv"}}
        rv = app.get(url, headers=h)
    else:
        rv = app.get(url, headers=header)
    return rv


def _epi_year_by_year_side_effect(year):
    return datetime(year, 1, 1)


def _epi_year_by_date_side_effect(date):
    return datetime(date.year, 1, 1)


class TestCase(unittest.TestCase):
    meerkat_api.app.config.from_object('meerkat_api.config.Testing')
    meerkat_api.app.app_context().push()
    app = meerkat_api.app.test_client()
    db_session = db_util.session

    def _mock_epi_week_abacus_logic(self):
        epi_year_patch = patch('meerkat_abacus.util.epi_year_start_date')
        self.addCleanup(epi_year_patch.stop)
        self.epi_year_mock = epi_year_patch.start()
        self.epi_year_mock.side_effect = _epi_year_by_date_side_effect
        epi_year_by_year_patch = patch('meerkat_abacus.util.epi_year_start_date_by_year')
        self.addCleanup(epi_year_by_year_patch.stop)
        self.epi_year_by_year_mock = epi_year_by_year_patch.start()
        self.epi_year_by_year_mock.side_effect = _epi_year_by_year_side_effect


class MeerkatAPITestCase(TestCase):
    def setUp(self):
        """Setup for testing"""
        celery_app.conf.CELERY_ALWAYS_EAGER = True

        db_util.insert_calculation_parameters(self.db_session)
        db_util.insert_codes(self.db_session)
        db_util.insert_locations(self.db_session)
        db_util.insert_cases(self.db_session, "public_health_report",
                             delete=True)
        db_util.insert_cases(self.db_session,
                             "ncd_public_health_report", delete=False)
        db_util.insert_cases(self.db_session, "ncd_report",
                             delete=False)
        db_util.insert_cases(self.db_session, "pip_report",
                             delete=False)
        db_util.insert_cases(self.db_session, "refugee_data",
                             delete=False)
        db_util.insert_cases(self.db_session, "frontpage", delete=False)
        db_util.insert_cases(self.db_session, "map_test", delete=False)
        db_util.insert_cases(self.db_session, "epi_monitoring",
                             delete=False)
        db_util.insert_cases(self.db_session, "malaria", delete=False)
        db_util.insert_cases(self.db_session, "alerts", delete=False)
        db_util.insert_cases(self.db_session, "cd_report", delete=False)
        db_util.insert_cases(self.db_session, "vaccination_report",
                             delete=False)
        db_util.insert_cases(self.db_session, "completeness",
                             delete=False)
        db_util.insert_cases(self.db_session, "afro_report",
                             delete=False)
        db_util.insert_cases(self.db_session, "mental_health",
                             delete=False)
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
        db_util.insert_statuses(self.db_session)
        urls = valid_urls(meerkat_api.app)
        for url in urls:
            print(url)
            rv = get_url(self.app, url, settings.header)
            isOK = rv.status_code in [200, 302]
            if not isOK:
                print("URL NOT OK: " + str(url))
            self.assertIn(rv.status_code, [200, 302])

    def test_authentication(self):
        db_util.insert_statuses(self.db_session)
        urls = valid_urls(meerkat_api.app)
        no_authentication = ["key_indicators",
                             "tot_map",
                             "consultation_map",
                             "num_alerts",
                             "num_clinics",
                             "refugee_page",
                             "locations",
                             "location/",
                             "clinics",
                             "epi_week",
                             "geo_shapes",
                             "variables",
                             "variable/tot_1"]
        no_authentication_full_paths = ["/device/4"]

        for url in urls:
            needs_auth = True
            for na in no_authentication:
                if na in url:
                    needs_auth = False
            if url in no_authentication_full_paths:
                needs_auth = False
            if url == "/" or url == "":
                needs_auth = False
            print(url + " needs auth? " + str(needs_auth))
            if needs_auth:
                rv = get_url(self.app, url, settings.header_non_authorised)
                self.assertEqual(rv.status_code, 401)
                rv = get_url(self.app, url, settings.header)
                self.assertIn(rv.status_code, [200, 302])
            else:
                rv = get_url(self.app, url, settings.header_non_authorised)
                self.assertEqual(rv.status_code, 200)
                rv = get_url(self.app, url, settings.header)
                self.assertEqual(rv.status_code, 200)


if __name__ == '__main__':
    unittest.main()
