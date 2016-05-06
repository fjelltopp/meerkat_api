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




class MeerkatAPITestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        manage.set_up_everything(
            True, True, 500)

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
    def test_autentication(self):
        meerkat_api.app.config['API_KEY'] = "test-api"
        rv = self.app.get("/test-authentication?api_key=test-api")
        self.assertEqual(rv.status_code, 200)
        rv = self.app.get("/test-authentication")
        self.assertEqual(rv.status_code, 401)
        rv = self.app.get("/test-authentication?api_key=not-real-key")
        self.assertEqual(rv.status_code, 401)

    def test_completeness(self):
        #Need some more testing here
        variable = "tot_1"
        rv = self.app.get('/completeness/{}/4'.format(variable))
        year = datetime.now().year
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        
        assert "clinics" in data.keys()
        assert "regions" in data.keys()
        assert "1" in data["clinics"].keys()
        for clinic in data["clinics"]["1"].keys():
            results = meerkat_api.db.session.query(
                model.Data).filter(
                    model.Data.clinic == clinic,
                    extract("year", model.Data.date) == year,
                    model.Data.variables.has_key(variable)
                ).all()
            assert data["clinics"]["1"][clinic]["year"] == len(results)


if __name__ == '__main__':
    unittest.main()
