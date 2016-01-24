#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the Meerkat frontend
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
from meerkat_api.resources import reports




class MeerkatAPITestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        manage.set_up_everything(
            config.DATABASE_URL,
            True, True, N=500)

        self.app = meerkat_api.app.test_client()
        self.locations = {1: {"name": "Demo"}}
        self.variables = {1: {"name": "Total"}}
    def tearDown(self):
        pass

    def test_get_variable_id(self):
        """Test get variable di"""
        variable = "tot_1"
        conn = meerkat_api.db.engine.connect()
        start_date = datetime(datetime.now().year , 1, 1)
        end_date = datetime.now()
        location = 2

        variable_id_result = reports.get_variable_id(variable,
                                                     start_date,
                                                     end_date,
                                                     location,
                                                     conn)
        rv = self.app.get('/aggregate_year/{}/{}'.format(variable, location))
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(variable_id_result,
                         data["year"])

    def test_top(self):
        """Test top function"""
        values = {"two": 2, "three":3, "four":4, "five":5, "one":1}
        result = reports.top(values)
        self.assertEqual(result, ["five", "four", "three", "two", "one"])


    def test_get_variables_category(self):
        """ Test get category """
        category = "gender"
        conn = meerkat_api.db.engine.connect()
        start_date = datetime(datetime.now().year , 1, 1)
        end_date = datetime.now()
        location = 2
        result = reports.get_variables_category(category,
                                                start_date,
                                                end_date,
                                                location,
                                                conn)
        rv = self.app.get('/aggregate_category/{}/{}'.format(category,
                                                             location))
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(result["Female"],
                         data["gen_2"]["year"]
                         )
        self.assertEqual(result["Male"],
                         data["gen_1"]["year"]
                         )

    def test_get_diease_types(self):
        category = "cd"
        conn = meerkat_api.db.engine.connect()
        start_date = datetime(datetime.now().year , 1, 1)
        end_date = datetime.now()
        location = 2
        result = reports.get_disease_types(category,
                                           start_date,
                                           end_date,
                                           location,
                                           conn)
        assert len(result) <= 5
        assert result[0]["percent"]<=100
        assert result[-1]["quantity"] > 0
        
    def test_public_health(self):
        location = 2
        rv = self.app.get('/reports/public_health/{}'.format(location))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))

    def test_cd_report(self):
        location = 2
        rv = self.app.get('/reports/cd_report/{}'.format(location))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))

        
        
        
    # def test_tot_clinics(self):
    #     """Check tot_clinics"""
    #     rv = self.app.get('/tot_clinics/1')
    #     data = json.loads(rv.data.decode("utf-8"))
    #     self.assertEqual(rv.status_code, 200)
    #     results = meerkat_api.db.session.query(
    #         model.Locations).filter(
    #             model.Locations.case_report == "1").all()
    #     assert data["total"] == len(results)
    #     rv = self.app.get('/tot_clinics/2')
    #     data = json.loads(rv.data.decode("utf-8"))
    #     self.assertEqual(rv.status_code, 200)
    #     assert data["total"] == 3


    
if __name__ == '__main__':
    unittest.main()
