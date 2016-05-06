#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the varibles resource in Meerkat API
"""
import json
import unittest
import meerkat_api
from meerkat_api.test import db_util
from meerkat_api.test.test_data.codes import codes

class MeerkatAPIVariablesTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        self.app = meerkat_api.app.test_client()
        db_util.insert_codes(meerkat_api.db.session)
        db_util.insert_locations(meerkat_api.db.session)

    def tearDown(self):
        pass


    def test_variable(self):
        """Check locations"""
        rv = self.app.get('/variable/tot_1')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["name"], "Total")
        rv = self.app.get('/variable/gen_2')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["name"], "Female")
        rv = self.app.get('/variable/prc_6')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["name"], "Injury")
        
    def test_variables(self):
        """Check locations"""
        rv = self.app.get('/variables/gender')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(sorted(data.keys()),
                         ["gen_1", "gen_2"])
        self.assertEqual(data["gen_2"]["name"], "Female")

        rv = self.app.get('/variables/locations')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(data), 11)
        self.assertEqual(data["11"]["name"], "Clinic 5")


        rv = self.app.get('/variables/alert')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(data), 36)
        self.assertEqual(data["cmd_1"]["name"], "Cholera")

        
        rv = self.app.get('/variables/all')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(data), len(codes))
        self.assertEqual(data["cmd_1"]["name"], "Cholera")
