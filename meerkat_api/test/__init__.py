#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the Meerkat frontend
"""
import json
import unittest
from datetime import datetime
from sqlalchemy import extract

import meerkat_api
import meerkat_abacus.manage as manage
import meerkat_abacus.config as config
import meerkat_abacus.model as model




class MeerkatAPITestCase(unittest.TestCase):

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
        self.assertEqual(data['3']["year"], len(results.all()))
        
    def test_clinics(self):
        rv = self.app.get('/clinics/1')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["features"]),4)

    def test_map(self):
        rv = self.app.get('/map/1')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data), 4)
        geo_location = data[0]["geolocation"]
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("1"),
            model.Data.geolocation == geo_location)
        
        self.assertEqual(data[0]["value"], len(results.all()))
    def test_query_variable(self):
        rv = self.app.get('/query_variable/1/gender')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert("Female" in data)
        assert("Male" in data)
        year = datetime.today().year
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("1"),
            extract("year", model.Data.date) == year)
        assert(data["Male"]["total"]+data["Female"]["total"] ==
               len(results.all()))
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("2"),
            extract("year", model.Data.date) == year)
        assert(data["Male"]["total"] == len(results.all()))
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("3"),
            extract("year", model.Data.date) == year)
        assert(data["Female"]["total"] == len(results.all()))
    def test_query_variable_location(self):
        """Test with variable = location"""
        year = datetime.today().year
        rv = self.app.get('/query_variable/location:1/gender')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert("Female" in data)
        assert("Male" in data)
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("2"),
            extract("year", model.Data.date) == year)
        assert(data["Male"]["total"] == len(results.all()))
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("3"),
            extract("year", model.Data.date) == year)
        assert(data["Female"]["total"] == len(results.all()))
    def test_query_variable_locations(self):
        """Test with group_by = locations"""
        year = datetime.today().year
        rv = self.app.get('/query_variable/1/locations')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert("Demo" in data)
        assert("Clinic 1" in data)
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.region == 2,
            model.Data.variables.has_key("1"),
            extract("year", model.Data.date) == year)
        assert(data["Region 1"]["total"] == len(results.all()))
    def test_query_variable_dates(self):
        """Test with dates"""
        rv = self.app.get('/query_variable/1/gender/2015-03-01/2015-07-01')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert("Female" in data)
        assert("Male" in data)
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("1"),
            model.Data.variables.has_key("2"),
            model.Data.date >= datetime(2015, 3, 1),
            model.Data.date < datetime(2015, 7, 1))
        assert data["Male"]["total"] == len(results.all())


    def test_query_category(self):
        """test normal function"""
        year = datetime.today().year
        rv = self.app.get('/query_category/gender/age')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert("Female" in data)
        assert("Male" in data)
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("2"),
            model.Data.variables.has_key("10"),
            extract("year", model.Data.date) == year)
        n_results = len(results.all())
        if n_results > 0:
            assert("20-59" in data["Male"])
            assert(data["Male"]["20-59"] == n_results)
        else:
            assert("20-59" not in data["Male"])
            
    def test_query_category_locations(self):
        """Test with locations"""
        year = datetime.today().year
        rv = self.app.get('/query_category/gender/locations')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert("Demo" in data)
        assert("Clinic 1" in data)
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.region == 2,
            model.Data.variables.has_key("2"),
            extract("year", model.Data.date) == year)
        n_results = len(results.all())
        if n_results > 0:
            assert("Male" in data["Region 1"])
            assert(data["Region 1"]["Male"] == len(results.all()))
        else:
            assert("Male" not in data["Region 1"])
    def test_query_category_dates(self):
        """test with dates"""
        year = datetime.today().year
        rv = self.app.get('/query_category/gender/age/2015-03-01/2015-07-01')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        print(data)
        assert("Female" in data)
        assert("Male" in data)
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("2"),
            model.Data.variables.has_key("10"),
            model.Data.date >= datetime(2015, 3, 1),
            model.Data.date < datetime(2015, 7, 1))
        n_results = len(results.all())
        if n_results > 0:
            assert("20-59" in data["Male"])
            assert(data["Male"]["20-59"] == n_results)
        else:
            assert("20-59" not in data["Male"])

    def test_alert(self):
        """test alert"""
        results = meerkat_api.db.session.query(model.Alerts).first()
        rv = self.app.get('/alert/' + results.id)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert data["alerts"]["id"] == results.id
        results = meerkat_api.db.session.query(model.Links)\
                .filter(model.Links.link_def == 1).first()
        rv = self.app.get('/alert/' + results.link_value)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        print(data)
        assert "links" in data.keys()

    def test_alerts(self):
        """test alerts"""
        rv = self.app.get('/alerts')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        results = meerkat_api.db.session.query(model.Alerts).all()
        links = meerkat_api.db.session.query(model.Links).filter(
            model.Links.link_def == 1).all()
        link_ids = []
        for l in links:
            link_ids.append(l.link_value)
        for d in data["alerts"]:
            if d["alerts"]["id"] in link_ids:
                assert "links" in d
            else:
                assert "links" not in d
        
        assert len(data["alerts"]) == len(results)

        rv = self.app.get('/alerts?reason=44')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        results = meerkat_api.db.session.query(model.Alerts).filter(
            model.Alerts.reason == 44).all()
        assert len(data["alerts"]) == len(results)

        rv = self.app.get('/alerts?location=11')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        results = meerkat_api.db.session.query(model.Alerts).filter(
            model.Alerts.clinic == 11).all()
        assert len(data["alerts"]) == len(results)
        rv = self.app.get('/alerts?location=1')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        results = meerkat_api.db.session.query(model.Alerts).all()
        assert len(data["alerts"]) == len(results)

        
if __name__ == '__main__':
    unittest.main()
