#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the data resource in Meerkat API
"""
import json, logging
import unittest
from datetime import datetime, timedelta, date
from sqlalchemy import extract
import pandas as pd
from . import settings
import meerkat_api
from freezegun import freeze_time

from meerkat_api.test import db_util
import meerkat_abacus.config as config
import meerkat_abacus.model as model

class MeerkatAPIDataTestCase(unittest.TestCase):
    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        self.app = meerkat_api.app.test_client()
        db_util.insert_codes(meerkat_api.db.session)
        db_util.insert_locations(meerkat_api.db.session, date="2016-07-02")


    def tearDown(self):
        pass
    @freeze_time("2016-07-02")
    def test_non_reporting(self):
        """Check non_reporting"""
        db_util.insert_cases(meerkat_api.db.session,
                             "completeness", "2016-07-02")
        rv = self.app.get('/non_reporting/reg_1/1', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(sorted(data["clinics"]), [10, 11])
        rv = self.app.get('/non_reporting/reg_2/1', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(sorted(data["clinics"]), [7, 8, 10, 11])
        rv = self.app.get('/non_reporting/reg_1/2', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(sorted(data["clinics"]), [10])
        rv = self.app.get('/non_reporting/reg_1/4', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(sorted(data["clinics"]), [])
        rv = self.app.get('/non_reporting/reg_1/6', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(sorted(data["clinics"]), [11])


    @freeze_time("2016-07-02")
    def test_completness(self):
        """Test completeness"""
        db_util.insert_cases(meerkat_api.db.session, "completeness", "2016-07-02")
        rv = self.app.get('completeness/reg_1/1/5', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        print(data)
        self.assertEqual( 
            sorted(data.keys()),
            ["clinic_score", "clinic_yearly_score", "dates_not_reported", "score", "timeline", "yearly_score"]
        )
        self.assertEqual(data["score"]["1"], 4 / 10 * 100)
        self.assertAlmostEqual(data["score"]["2"], 4 / 10 *100)
        self.assertEqual(data["clinic_score"]["7"], 60)
        self.assertEqual(data["clinic_score"]["8"], 20)
        today = date.today()
        today = datetime(today.year, today.month, today.day)
        freq = "W-FRI"
        epi_year_weekday = 4
        start = datetime(today.year, 1, 1)
        
        offset = today.weekday() - epi_year_weekday
        if offset < 0:
            offset = 7 + offset
        end = today - timedelta(days=offset + 1)
        dates = pd.date_range(start, end, freq=freq)
        dates_iso = [d.isoformat() for d in dates.to_pydatetime()]

        self.assertEqual(data["timeline"]["1"]["weeks"], dates_iso)
        
        self.assertEqual(data["timeline"]["1"]["values"][-1], 2)
        self.assertEqual(data["timeline"]["1"]["values"][-2], 0.5)
        self.assertAlmostEqual(data["timeline"]["2"]["values"][-1], 4 / 2)
        self.assertAlmostEqual(data["timeline"]["2"]["values"][-2], 1 / 2)


        rv = self.app.get('completeness/reg_1/4/5', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["score"]["4"], 4 / 10 *100)
        self.assertAlmostEqual(data["score"]["7"], 60)
        self.assertEqual(data["score"]["8"], 20)

        self.assertEqual(data["timeline"]["4"]["values"][-1], 2)
        self.assertEqual(data["timeline"]["4"]["values"][-2], 0.5)
        self.assertAlmostEqual(data["timeline"]["7"]["values"][-1], 3)
        self.assertAlmostEqual(data["timeline"]["7"]["values"][-2], 1)
        self.assertAlmostEqual(data["timeline"]["8"]["values"][-1], 1)
        self.assertAlmostEqual(data["timeline"]["8"]["values"][-2], 0)
        start2 = datetime(today.year, 2, 1)
        dates2 = pd.date_range(start2, end, freq=freq)
        dates_iso2 = [d.isoformat() for d in dates2.to_pydatetime()]
        self.assertEqual(data["timeline"]["7"]["weeks"], dates_iso2)

        
        
        rv = self.app.get('completeness/reg_1/7/5', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["clinic_score"], {})
        self.assertAlmostEqual(data["score"]["7"], 60)
        self.assertAlmostEqual(data["timeline"]["7"]["values"][-1], 3)
        self.assertAlmostEqual(data["timeline"]["7"]["values"][-2], 1)
        
        offset = today.weekday() - start.weekday()
        if offset < 0:
            offset = 7 + offset
        record_dates = []
        for i in [1, 2, 3, 8]:
            record_dates.append(today - timedelta(days=i + offset))
        dates_to_check = pd.date_range(start2, end, freq="D")
        for d in dates_to_check.to_pydatetime():
            if d.weekday() not in [5, 6] and d not in record_dates:
                self.assertIn(d.isoformat(), data["dates_not_reported"])
        rv = self.app.get('completeness/reg_1/7/5/1/uff/4,5',
                          headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        for d in dates_to_check.to_pydatetime():
            if d.weekday() not in [4, 5] and d not in record_dates:
                self.assertIn(d.isoformat(), data["dates_not_reported"])
