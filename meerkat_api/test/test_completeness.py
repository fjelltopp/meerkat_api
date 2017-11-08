#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the data resource in Meerkat API
"""
import json
import unittest
from unittest.mock import patch

import pandas as pd
from datetime import datetime, timedelta, date
from freezegun import freeze_time

import meerkat_api
from meerkat_api.test import db_util
from . import settings

class MeerkatAPIDataTestCase(meerkat_api.test.TestCase):
    def setUp(self):
        """Setup for testing"""
        self._mock_epi_week_abacus_logic()
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        self.app = meerkat_api.app.test_client()
        self.session = db_util.session

        db_util.insert_codes(self.session)
        db_util.insert_locations(self.session, date="2016-07-02")

    def tearDown(self):
        pass

    @freeze_time("2016-07-02")
    def test_non_reporting(self):
        """Check non_reporting"""
        db_util.insert_cases(self.session,
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

        # Test with include/exclude
        rv = self.app.get('/non_reporting/reg_1/1/0/foreigner',
                          headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(sorted(data["clinics"]), [11])

        rv = self.app.get('/non_reporting/reg_1/1/0/foreigner,mh',
                          headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(sorted(data["clinics"]), [])
        rv = self.app.get('/non_reporting/reg_1/1/0/0/foreigner',
                          headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(sorted(data["clinics"]), [10])

        rv = self.app.get('/non_reporting/reg_1/1/0/0/foreigner,mh',
                          headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(sorted(data["clinics"]), [10, 11])

        rv = self.app.get('/non_reporting/reg_2/1/0/0/0/Refugee/0',
                          headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(sorted(data["clinics"]), [7, 11])

    @freeze_time("2016-07-02")
    def test_completness(self):
        """Test completeness"""
        db_util.insert_cases(self.session, "completeness", "2016-07-02")
        rv = self.app.get('completeness/reg_1/1/5', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(
            sorted(data.keys()),
            ["clinic_score", "clinic_yearly_score", "dates_not_reported", "score", "timeline", "yearly_score"]
        )
        self.assertEqual(data["score"]["1"], 4 / 10 * 100)
        self.assertAlmostEqual(data["score"]["2"], 4 / 10 * 100)
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
        self.assertEqual(data["score"]["4"], 4 / 10 * 100)
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

        # Test with exclude and include_case_types

        rv = self.app.get('completeness/reg_1/1/5?inc_case_types=["mh"]',
                          headers=settings.header)

        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["score"]["1"], 3 / 5 * 100)

        self.assertNotIn("8", data["clinic_score"])
        self.assertIn("7", data["clinic_score"])
        self.assertEqual(data["clinic_score"]["7"], 60)

        rv = self.app.get('completeness/reg_1/1/5?exc_case_types=["mh"]',
                          headers=settings.header)

        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["score"]["1"], 1 / 5 * 100)

        self.assertNotIn("7", data["clinic_score"])
        self.assertIn("8", data["clinic_score"])
        self.assertEqual(data["clinic_score"]["8"], 20)
