#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the Meerkat frontend
"""
import meerkat_api
import json
import meerkat_abacus.manage as manage
import unittest
import meerkat_abacus.config as config
import meerkat_abacus.model as model
import subprocess



class MeerkatFrontendTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        manage.set_up_everything(
            config.DATABASE_URL,
            True, True, N=500)

        self.app = meerkat_api.app.test_client()

    def tearDown(self):
        pass

    def test_index(self):
        """Check the index page loads"""
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'WHO', rv.data)

    def test_locations(self):
        """Check locations"""
        rv = self.app.get('/locations')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(data), 11)
        
    def test_location(self):
        """Check locations"""
        rv = self.app.get('/location/1')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["name"], "Demo")

    def test_variable(self):
        """Check locations"""
        rv = self.app.get('/variable/1')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["name"], "Total")
        
    def test_variables(self):
        """Check locations"""
        rv = self.app.get('/variables/gender')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(data), 2)

    def test_aggregate(self):
        """Check locations"""
        rv = self.app.get('/aggregate/1/1')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        results = meerkat_api.db.session.query(
            model.form_tables["case"]).filter(
            model.form_tables["case"].data.contains(
                {"intro./visit_type": 'new'}))
        self.assertEqual(data["value"], len(results.all()))

    def test_aggregate_yearly(self):
        """Check locations"""
        rv = self.app.get('/aggregate_year/1/1')
        rv2 = self.app.get('/aggregate_year/1/1/2015')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv2.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        data2 = json.loads(rv2.data.decode("utf-8"))
        self.assertEqual(data, data2)

        results = meerkat_api.db.session.query(
            model.form_tables["case"]).filter(
            model.form_tables["case"].data.contains(
                {"intro./visit_type": 'new'}))
        self.assertEqual(data["year"],len(results.all()))

    def test_aggregate_category(self):
        """Check locations"""
        rv = self.app.get('/aggregate_category/gender/1')
        rv2 = self.app.get('/aggregate_category/gender/1/2015')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv2.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        data2 = json.loads(rv2.data.decode("utf-8"))
        self.assertEqual(data, data2)

        results = meerkat_api.db.session.query(
            model.form_tables["case"]).filter(
            model.form_tables["case"].data.contains(
                {"intro./visit_type": 'new', "pt1./gender": "female"}))
        self.assertEqual(data['3']["year"],len(results.all()))
    

if __name__ == '__main__':
    unittest.main()
