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
from meerkat_api.test.test_data.locations import DEVICE_IDS_CSV_LIST, DEVICEID_1, DEVICE_IDS_IMEI_CSV_LIST, \
    LOCATION_NUMBER
from . import settings


class MeerkatAPILocationTestCase(unittest.TestCase):
    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        self.app = meerkat_api.app.test_client()
        meerkat_api.app.app_context().push()
        session = db_util.session
        db_util.insert_codes(session)
        db_util.insert_locations(session)

    def tearDown(self):
        pass

    def test_locations(self):
        """Check locations"""
        rv = self.app.get('/locations', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data), LOCATION_NUMBER)
        self.assertEqual(set(data.keys()), set([repr(x) for x in range(1, LOCATION_NUMBER + 1)]))
        self.assertEqual(data["11"]["name"], "Clinic 5")
        self.assertEqual(data["11"]["parent_location"], 6)
        self.assertEqual(data["5"]["name"], "District 2")

    def test_location(self):
        """Check location"""
        rv = self.app.get('/location/11', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["name"], "Clinic 5")
        self.assertEqual(data["parent_location"], 6)
        rv = self.app.get('/location/7', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["name"], "Clinic 1")
        self.assertEqual(data["parent_location"], 4)

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

        # Test location tree filtering functionality
        # A utility function to recursively get the clinics out of the tree
        def get_clinics(tree):
            children = []
            if tree['nodes']:
                for child in tree['nodes']:
                    children += get_clinics(child)
                    if not child['nodes']:
                        children += [child['text']]
            return children

        # Test inc functionality
        rv = self.app.get(
            '/locationtree?inc_case_types=["pip"]',
            headers=settings.header
        )
        clinics = get_clinics(json.loads(rv.data.decode("utf-8")))
        print('/locationtree?inc_case_types=["pip"]')
        print(json.loads(rv.data.decode("utf-8")))
        print(clinics)
        self.assertEqual(rv.status_code, 200)
        self.assertIn('Clinic 2', clinics)
        self.assertIn('Clinic 4', clinics)
        self.assertIn('Clinic 5', clinics)
        self.assertEqual(len(clinics), 3)

        rv = self.app.get(
            '/locationtree?inc_case_types=["pip","mh"]',
            headers=settings.header
        )
        clinics = get_clinics(json.loads(rv.data.decode("utf-8")))
        print('/locationtree?inc_case_types=["pip", "mh"]')
        print(json.loads(rv.data.decode("utf-8")))
        print(clinics)
        self.assertEqual(rv.status_code, 200)
        self.assertIn('Clinic 2', clinics)
        self.assertIn('Clinic 1', clinics)
        self.assertIn('Clinic 4', clinics)
        self.assertIn('Clinic 5', clinics)
        self.assertEqual(len(clinics), 4)

        # Test exc functionality
        rv = self.app.get(
            '/locationtree?exc_case_types=["pip"]',
            headers=settings.header
        )
        clinics = get_clinics(json.loads(rv.data.decode("utf-8")))
        print('/locationtree?exc_case_types=["pip"]')
        print(json.loads(rv.data.decode("utf-8")))
        print(clinics)
        self.assertEqual(rv.status_code, 200)
        self.assertIn('Clinic 1', clinics)
        self.assertIn('Clinic 4', clinics)
        self.assertIn('Clinic 5', clinics)
        self.assertEqual(len(clinics), 3)

        rv = self.app.get(
            '/locationtree?exc_case_types=["pip", "mh"]',
            headers=settings.header
        )
        clinics = get_clinics(json.loads(rv.data.decode("utf-8")))
        print('/locationtree?exc_case_types=["pip", "mh"]')
        print(json.loads(rv.data.decode("utf-8")))
        print(clinics)
        self.assertEqual(rv.status_code, 200)
        self.assertIn('Clinic 4', clinics)
        self.assertEqual(len(clinics), 1)

        # Test both inc and exc functionality
        rv = self.app.get(
            '/locationtree?inc_case_types=["mh"]&exc_case_types=["pip","mh"]',
            headers=settings.header
        )
        clinics = get_clinics(json.loads(rv.data.decode("utf-8")))
        print(
            '/locationtree?inc_case_types=["mh"]&exc_case_types=["pip","mh"]'
        )
        print(json.loads(rv.data.decode("utf-8")))
        print(clinics)
        self.assertEqual(rv.status_code, 200)
        self.assertIn('Clinic 4', clinics)
        self.assertEqual(len(clinics), 1)

    def test_location_by_non_existing_device_id(self):
        for id in ["42", "fake_device_id", DEVICEID_1[1:]]:
            rv = self.app.get('/device/%s/location' % id, headers=settings.header)
            self.assertEqual(rv.status_code, 404)
            self.assertTrue(("No location matching deviceid: '%s'" % id) in rv.data.decode('utf-8'))

    def test_location_by_device_id(self):
        for id in DEVICE_IDS_CSV_LIST.split(','):
            self.validate_correct_location_returned(deviceid=id, expected_loc_id=12)

    def test_location_by_device_id_imei_format(self):
        for id in DEVICE_IDS_IMEI_CSV_LIST.split(','):
            self.validate_correct_location_returned(deviceid=id, expected_loc_id=13)

    def validate_correct_location_returned(self, deviceid=None, expected_loc_id=None):
        rv = self.app.get('/device/%s/location' % deviceid, headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        actual_loc_id = json.loads(rv.data.decode('utf-8'))['id']
        self.assertEqual(actual_loc_id, expected_loc_id)
