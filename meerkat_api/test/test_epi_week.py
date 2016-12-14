#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the epi week resource of Meerkat Api
"""

import json
import unittest
from datetime import datetime
from datetime import timedelta
from sqlalchemy import extract
from . import settings
import meerkat_api
from meerkat_abacus.util import epi_week_start_date
import meerkat_abacus.config as config
import meerkat_abacus.model as model


class MeerkatAPIEpiWeekTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        self.app = meerkat_api.app.test_client()

    def tearDown(self):
        pass

    def test_epi_year_start(self):
        """ Test the epi_year_start function """
        meerkat_api.app.config['TESTING'] = False
        rv = self.app.get('/epi_week_start/2015/1', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["start_date"], epi_week_start_date(2015).isoformat())
        
    def test_epi_week(self):
        """ Test date to epi week"""
        rv = self.app.get('/epi_week/2015-01-05', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["epi_week"], 1)
        rv = self.app.get('/epi_week/2015-12-02', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["epi_week"], 48)

    def test_epi_week_start(self):
        """ test epi-week to date """
        rv = self.app.get('/epi_week_start/2015/49', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["start_date"], "2015-12-03T00:00:00")
        rv = self.app.get('/epi_week_start/2015/2', headers=settings.header)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["start_date"], "2015-01-08T00:00:00")
