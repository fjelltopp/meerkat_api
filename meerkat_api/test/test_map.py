#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the location resource in Meerkat API
"""
import json
import unittest
from freezegun import freeze_time
    
import meerkat_api
from meerkat_api.test import db_util
from meerkat_api.test import settings
from meerkat_api.resources.map import MapVariable



class MeerkatAPIMapTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        self.app = meerkat_api.app.test_client()
        session = db_util.session
        
        db_util.insert_codes(session)
        db_util.insert_locations(session)
        db_util.insert_cases(session, "map_test", date="2016-07-02")

        
    def tearDown(self):
        pass
        
    def test_clinics(self):
        """ Test get clinics """
        rv = self.app.get('/clinics/1', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["features"]), 4)
        found = False
        for feature in data["features"]:
            if feature["properties"]["name"] == "Clinic 5":
                found = True
                self.assertEqual(feature["geometry"]["coordinates"], [-0.1, 0.4])                
            
        self.assertTrue(found)

        # Note the order is lat long for geojson
        rv = self.app.get('/clinics/3', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["features"]), 1)

        rv = self.app.get('/clinics/1/SARI', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["features"]), 2)


    @freeze_time("2016-07-02")
    def test_map(self):
        """ Test map variable """
        rv = self.app.get('/map/tot_1', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data), 3)
        self.assertEqual(data["11"]["value"], 4)
        self.assertEqual(data["7"]["value"], 4)
        self.assertEqual(data["8"]["value"], 2)

        rv = self.app.get('/map/gen_2', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data), 3)
        self.assertEqual(data["11"]["value"], 4)
        self.assertEqual(data["7"]["value"], 1)
        self.assertEqual(data["8"]["value"], 2)

        rv = self.app.get('/map/gen_1', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data), 1)
        self.assertEqual(data["7"]["value"], 3)

        mv = MapVariable()

        data = mv.get("gen_2", include_all_clinics=True)
        self.assertEqual(len(data), 4)

        data = mv.get("gen_2", location=3)
        self.assertEqual(len(data), 1)
