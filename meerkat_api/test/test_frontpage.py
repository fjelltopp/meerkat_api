#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the export_data resource of Meerkat API
"""
import json
import unittest
from datetime import datetime
import csv

import meerkat_api
from meerkat_api.test import db_util


class MeerkatAPITestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = "should-work-even-with-api-key"
        self.app = meerkat_api.app.test_client()
        meerkat_api.db.session.commit()
        db_util.insert_codes(meerkat_api.db.session)
        db_util.insert_locations(meerkat_api.db.session)
        db_util.insert_cases(meerkat_api.db.session, "frontpage")
        db_util.insert_alerts(meerkat_api.db.session, "cd_report")

    def tearDown(self):
        pass

    def test_key_indicators(self):
        """ Test getting key indicators """
        
        rv = self.app.get('/key_indicators')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))

        self.assertEqual(data["reg_1"]["year"], 1)
        self.assertEqual(data["reg_2"]["year"], 15)
        self.assertEqual(data["tot_1"]["year"], 1)

    def test_tot_map(self):
        """ Test getting the map of cases"""
        
        rv = self.app.get('/tot_map')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(data.keys()),
                         sorted(["7", "8",  "10", "11"]))
        self.assertEqual(data["7"]["value"], 1)
        self.assertEqual(data["8"]["value"], 0)
        self.assertEqual(data["10"]["value"], 0)
        self.assertEqual(data["11"]["value"], 0)


    def test_consultation_map(self):
        """ Test getting map of consultations"""
        rv = self.app.get('/consultation_map')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(data.keys()),
                         sorted(["7", "8",  "10", "11"]))
        self.assertEqual(data["7"]["value"], 0)
        self.assertEqual(data["8"]["value"], 15)
        self.assertEqual(data["10"]["value"], 0)
        self.assertEqual(data["11"]["value"], 0)

    def test_num_alerts(self):
        """ Test getting the number of consultations"""
        rv = self.app.get('/num_alerts')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["num_alerts"], 8)

    def test_refugee_page(self):
        """ test the refugee page """
        db_util.insert_cases(meerkat_api.db.session, "refugee_data")
        rv = self.app.get('/refugee_page')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))

        data = sorted(data, key=lambda k: k["location_id"])

        self.assertEqual(data[0]["location_id"], 7)
        self.assertEqual(data[0]["value"], 12)

        self.assertEqual(data[1]["location_id"], 11)
        self.assertEqual(data[1]["value"], 77)


        
        
