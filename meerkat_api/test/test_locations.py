#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the location resource in Meerkat API
"""
import json
import unittest
import meerkat_api
from meerkat_api.test import db_util
from meerkat_api.resources import locations
from . import settings

class MeerkatAPILocationTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        self.app = meerkat_api.app.test_client()
        db_util.insert_codes(meerkat_api.db.session)
        db_util.insert_locations(meerkat_api.db.session)

    def tearDown(self):
        pass

    def test_locations(self):
        """Check locations"""
        rv = self.app.get('/locations', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data), 11)
        self.assertEqual(sorted(data.keys()),
                         sorted(["1", "2", "3","4" ,"5" ,"6" ,"7" ,"8" ,"9" ,"10", "11"]))

        self.assertEqual(data["11"]["name"], "Clinic 5")
        self.assertEqual(data["11"]["parent_location"], [6])
        self.assertEqual(data["5"]["name"], "District 2")


    def test_location(self):
        """Check location"""
        rv = self.app.get('/location/11', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["name"], "Clinic 5")
        self.assertEqual(data["parent_location"], [6])
        rv = self.app.get('/location/7', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["name"], "Clinic 1")
        self.assertEqual(data["parent_location"], [4])

        
    def test_tot_clinics(self):
        """Check tot_clinics"""
        rv = self.app.get('/tot_clinics/1', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["total"], 4)
        rv = self.app.get('/tot_clinics/2', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["total"], 3)
        rv = self.app.get('/tot_clinics/3', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["total"], 1)

        # With clinic type
        tot_clinic = locations.TotClinics()
        data = tot_clinic.get(1, "SARI")
        self.assertEqual(data["total"], 2)
        data = tot_clinic.get(1, "Refugee")
        self.assertEqual(data["total"], 2)

    def test_location_tree(self):
        """ Test the location tree """
        rv = self.app.get('/locationtree', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["text"], "Demo")
        nodes = data["nodes"]
        ids = []
        for n in nodes:
            ids.append(n["id"])
        self.assertIn(2, ids)
        self.assertIn(3, ids)
        self.assertNotIn(4, ids)
        self.assertNotIn(5, ids)

        district_level = nodes[0]["nodes"]
        ids = []
        for n in district_level:
            ids.append(n["id"])

        self.assertIn(4, ids)
        self.assertIn(5, ids)
        self.assertNotIn(6, ids)

        clinic_level = district_level[0]["nodes"]
        ids = []
        for n in clinic_level:
            ids.append(n["id"])
        self.assertIn(7, ids)
        self.assertIn(8, ids)
        self.assertNotIn(9, ids)
        self.assertNotIn(10, ids)
        self.assertNotIn(11, ids)
