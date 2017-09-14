#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the data resource in Meerkat API
"""
import json
import unittest
from datetime import datetime
from sqlalchemy import extract
from . import settings
import meerkat_api
from meerkat_api.test import db_util
import meerkat_abacus.config as config
import meerkat_abacus.model as model

class MeerkatAPIDataTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        self.app = meerkat_api.app.test_client()
        session = db_util.session
        db_util.insert_codes(session)
        db_util.insert_locations(session)
        db_util.insert_cases(session, "public_health_report")

    def tearDown(self):
        pass

    def test_aggregate(self):
        """Check aggregate"""
        rv = self.app.get('/aggregate/tot_1/1', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["value"], 11)

        rv = self.app.get('/aggregate/reg_2/1', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["value"], 15)

        rv = self.app.get('/aggregate/gen_2/1', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["value"], 8)

        rv = self.app.get('/aggregate/gen_2/2', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["value"], 3)

        rv = self.app.get('/aggregate/gen_2/3', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["value"], 5)

        rv = self.app.get('/aggregate/gen_2/5', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["value"], 1)

        rv = self.app.get('/aggregate/gen_2/8', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["value"], 2)

    def test_aggregate_yearly(self):
        """Test for aggregate Yearly"""
        rv = self.app.get('/aggregate_year/tot_1/1/2015', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["year"], 10)
        self.assertEqual(data["weeks"]["18"], 8)
        self.assertEqual(data["weeks"]["22"], 1)

        rv = self.app.get('/aggregate_year/gen_1/1/2015', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["year"], 3)
        self.assertEqual(data["weeks"]["18"], 3)

        rv = self.app.get('/aggregate_year/gen_2/3/2015', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["year"], 4)
        self.assertEqual(data["weeks"]["18"], 3)
        self.assertEqual(data["weeks"]["22"], 1)

    def test_aggregate_category(self):
        """Test for aggregate Category """
        rv = self.app.get('/aggregate_category/gender/1/2015', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(list(data.keys())), sorted(["gen_1", "gen_2"]))
        print(data)
        self.assertEqual(data["gen_1"]["year"], 3)
        self.assertEqual(data["gen_2"]["year"], 7)
        self.assertEqual(data["gen_1"]["weeks"]["18"], 3)
        self.assertEqual(data["gen_2"]["weeks"]["18"], 5)
        self.assertEqual(data["gen_2"]["weeks"]["22"], 1)

        rv = self.app.get('/aggregate_category/gender/3/2015', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        print(data)
        self.assertEqual(sorted(list(data.keys())), sorted(["gen_1", "gen_2"]))
        self.assertEqual(data["gen_1"]["year"], 0)
        self.assertEqual(data["gen_2"]["year"], 4)
        self.assertEqual(data["gen_1"]["weeks"], {})
        self.assertEqual(data["gen_2"]["weeks"]["18"], 3)
        self.assertEqual(data["gen_2"]["weeks"]["22"], 1)

        rv = self.app.get('/aggregate_category/pc/1/2015', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(list(data.keys())),
                         sorted(["prc_1", "prc_2", "prc_3", "prc_4",  "prc_6", "prc_7"]))
        self.assertEqual(data["prc_1"]["year"], 7)
        self.assertEqual(data["prc_2"]["year"], 2)
        self.assertEqual(data["prc_3"]["year"], 1)
        rv = self.app.get('/aggregate_category/no_category/1/2015', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(list(data.keys())), [])

    def test_records(self):
        """Test records function """
        rv = self.app.get('/records/prc_1/1', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["records"]), 7)

        rv = self.app.get('/records/prc_1/3', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["records"]), 1)
        self.assertEqual(
            data["records"][0]["variables"],
            { "data_entry":1, "tot_1":1, "gen_2": 1, "age_4": 1, "age_10": 1,
              "nat_2": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1 }
        )
        self.assertEqual(data["records"][0]["clinic_type"], "Hospital")
        self.assertEqual(data["records"][0]["uuid"], "uuid:2d14ec68-c5b3-47d5-90db-eee510ee9377")
