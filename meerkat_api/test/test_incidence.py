#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the location resource in Meerkat API
"""
import json
import unittest
import meerkat_api
from meerkat_api.test import db_util
from . import settings


class MeerkatAPIIncidenceTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        self.app = meerkat_api.app.test_client()
        db_util.insert_codes(meerkat_api.db.session)
        db_util.insert_locations(meerkat_api.db.session)
        db_util.insert_cases(meerkat_api.db.session, "public_health_report")

    def tearDown(self):
        pass

    def test_incidence(self):
        rv = self.app.get('/incidence_rate/tot_1/region',
                          headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data['2'], 6 / 7000 * 1000)
        self.assertEqual(data['3'], 5 / 3000 * 1000)

        rv = self.app.get('/incidence_rate/tot_1/region/5000',
                          headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data['2'], 6 / 7000 * 5000)
        self.assertEqual(data['3'], 5 / 3000 * 5000)

        rv = self.app.get('/incidence_rate/gen_1/region',
                          headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data['2'], 3 / 7000 * 1000)
        self.assertTrue("3" not in data)
        rv = self.app.get('/incidence_rate/tot_1/clinic',
                          headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data['7'], 4 / 3000 * 1000)
        self.assertEqual(data['8'], 2 / 1000 * 1000)
        self.assertEqual(data['11'], 5 / 3000 * 1000)
        
    def test_incidence_weeks(self):
        rv = self.app.get('/weekly_incidence/tot_1/1/2015',
                          headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data['year'], 10 / 10000 * 1000)
        self.assertEqual(data['weeks']['18'], 9 / 10000 * 1000)
        self.assertEqual(data['weeks']['22'], 1 / 10000 * 1000)
        rv = self.app.get('/weekly_incidence/tot_1/1/2015/5000',
                          headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data['year'], 10 / 10000 * 5000)
        self.assertEqual(data['weeks']['18'], 9 / 10000 * 5000)
        self.assertEqual(data['weeks']['22'], 1 / 10000 * 5000)
        rv = self.app.get('/weekly_incidence/gen_1/1/2015',
                          headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data['year'], 3 / 10000 * 1000)
        self.assertEqual(data['weeks']['18'], 3 / 10000 * 1000)
        self.assertTrue("22" not in data["weeks"])
        rv = self.app.get('/weekly_incidence/tot_1/7/2015',
                          headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data['year'], 4 / 3000 * 1000)
        self.assertEqual(data['weeks']['18'], 4 / 3000 * 1000)
        self.assertTrue("22" not in data["weeks"])
