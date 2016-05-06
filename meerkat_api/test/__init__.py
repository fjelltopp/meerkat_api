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

    def test_locations(self):
        """Check locations"""
        rv = self.app.get('/locations')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(data), 11)
    def test_tot_clinics(self):
        """Check tot_clinics"""
        rv = self.app.get('/tot_clinics/1')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        results = meerkat_api.db.session.query(
            model.Locations).filter(
                model.Locations.case_report == "1").all()
        assert data["total"] == len(results)
        rv = self.app.get('/tot_clinics/2')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        assert data["total"] == 3
    def test_location(self):
        """Check locations"""
        rv = self.app.get('/location/1')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["name"], self.locations[1]["name"])

    def test_variable(self):
        """Check locations"""
        rv = self.app.get('/variable/tot_1')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["name"], self.variables[1]["name"])
        
    def test_variables(self):
        """Check locations"""
        rv = self.app.get('/variables/gender')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        assert "gen_1" in data.keys()
        assert "gen_2" in data.keys()
        self.assertEqual(len(data), 2)

    def test_clinics(self):
        rv = self.app.get('/clinics/1')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["features"]),4)

    def test_map(self):
        rv = self.app.get('/map/tot_1')
        year = datetime.now().year
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data), 4)
        geo_location = data[list(data.keys())[0]]["geolocation"]
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("tot_1"),
            extract("year", model.Data.date) == year,
            model.Data.geolocation == ",".join(geo_location))
        
        self.assertEqual(data[list(data.keys())[0]]["value"], len(results.all()))
        

    def test_location_tree(self):
        rv = self.app.get('/locationtree')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert data["text"] == "Demo"
        nodes = data["nodes"]
        ids = []
        for n in nodes:
            ids.append(n["id"])
        assert 2 in ids
        assert 3 in ids
        assert 4 not in ids
        assert 5 not in ids

  
if __name__ == '__main__':
    unittest.main()
