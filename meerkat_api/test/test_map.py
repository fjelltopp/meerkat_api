#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the location resource in Meerkat API
"""
import json
import unittest
import meerkat_api
from meerkat_api.test import db_util
from meerkat_api.resources.map import MapVariable
from . import settings

class MeerkatAPIMapTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        self.app = meerkat_api.app.test_client()
        db_util.insert_codes(meerkat_api.db.session)
        db_util.insert_locations(meerkat_api.db.session)
        db_util.insert_cases(meerkat_api.db.session, "map_test")

        
    def tearDown(self):
        pass
        
    def test_clinics(self):
        """ Test get clinics """
        rv = self.app.get('/clinics/1', headers=headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["features"]), 4)
        self.assertEqual(data["features"][0]["properties"]["name"], "Clinic 1")
        self.assertEqual(data["features"][3]["geometry"]["coordinates"], [0.4, -0.1])
        # Note the order is lat long for geojson
        rv = self.app.get('/clinics/3', headers=headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["features"]), 1)

        rv = self.app.get('/clinics/1/SARI', headers=headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["features"]), 2)


        
    def test_map(self):
        """ Test map variable """
        rv = self.app.get('/map/tot_1', headers=headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data), 3)
        self.assertEqual(data["11"]["value"], 4)
        self.assertEqual(data["7"]["value"], 4)
        self.assertEqual(data["8"]["value"], 2)

        rv = self.app.get('/map/gen_2', headers=headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data), 3)
        self.assertEqual(data["11"]["value"], 4)
        self.assertEqual(data["7"]["value"], 1)
        self.assertEqual(data["8"]["value"], 2)

        rv = self.app.get('/map/gen_1', headers=headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data), 1)
        self.assertEqual(data["7"]["value"], 3)

        mv = MapVariable()

        data = mv.get("gen_2", include_all_clinics=True)
        self.assertEqual(len(data), 4)

        data = mv.get("gen_2", location=3)
        self.assertEqual(len(data), 1)
