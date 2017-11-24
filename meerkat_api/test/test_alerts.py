#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the alerts resource in Meerkat API
"""
import json, unittest, meerkat_api
from meerkat_api.test import settings
from datetime import datetime
from meerkat_api.test import db_util

class MeerkatAPIAlertsTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        self.app = meerkat_api.app.test_client()
        self.db = db_util.session
        db_util.insert_codes(self.db)
        db_util.insert_locations(self.db)
        db_util.insert_cases(self.db, "alerts")

    def tearDown(self):
        pass
    
    def test_alert(self):
        """test alert"""
        rv = self.app.get('/alert/ce9341', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))["alert"]
        self.assertEqual(data["variables"]["alert_id"], "ce9341")
        self.assertEqual(data["variables"]["alert_reason"], "cmd_11")
        self.assertEqual(data["clinic"], 7)
        self.assertEqual(data["region"], 2)
        self.assertEqual(data["uuid"], "uuid:b013c24a-4790-43d6-8b43-4d28a4ce9341")
        self.assertEqual(data["variables"]["alert_gender"],  "female")
        self.assertEqual(data["variables"]["alert_age"], "33")
        self.assertIn( "ale_2", data["variables"])
        self.assertIn("ale_6", data["variables"])
        self.assertIn("ale_7", data["variables"])


    def test_aggregate_alert(self):
        """test aggregate_alerts"""
        rv = self.app.get('/aggregate_alerts', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["total"], 8)
        self.assertEqual(sorted(list(data.keys())),
                         sorted(["cmd_1", "cmd_2", "cmd_11", "cmd_19", "total"]))

        self.assertEqual(data["cmd_1"], {"Pending": 1})
        self.assertEqual(data["cmd_2"], {"Pending": 1, "Ongoing": 1})
        self.assertEqual(data["cmd_11"],
                         {"Pending": 2, "Confirmed": 1, "Disregarded": 1})
        self.assertEqual(data["cmd_19"], {"Pending": 1})

        # Now with a subset of clinics
        rv = self.app.get('/aggregate_alerts?location=3', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["cmd_19"], {"Pending": 1})
        self.assertEqual(sorted(list(data.keys())),
                         sorted(["cmd_19", "total"]))
        rv = self.app.get('/aggregate_alerts?location=2', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["total"], 7)
        # With only one reason
        rv = self.app.get('/aggregate_alerts?reason=cmd_19', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["cmd_19"], {"Pending": 1})
        self.assertEqual(sorted(list(data.keys())),
                         sorted(["cmd_19", "total"]))

    
    def test_alerts(self):
        """test alerts"""
        rv = self.app.get('/alerts', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["alerts"]), 8)

        rv = self.app.get('/alerts?reason=cmd_1', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["alerts"]), 1)
        self.assertEqual(data["alerts"][0]["uuid"],
                         "uuid:b013c24a-4790-43d6-8b43-4d28a4ce9342")
        self.assertEqual(data["alerts"][0]["region"], 2)

        rv = self.app.get('/alerts?reason=cmd_11', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["alerts"]), 4)

    
        rv = self.app.get('/alerts?location=11', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["alerts"]), 1)
        rv = self.app.get('/alerts?location=1', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["alerts"]),8)

        #Test the date filter
        start = datetime(2015, 3, 1, 0, 0).isoformat()
        end = datetime(2015, 4, 23, 0, 0).isoformat()
        rv = self.app.get('/alerts?start_date=' + start + '&end_date=' + end, headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["alerts"]), 2)

        # Get only the last three alerts
        rv = self.app.get('/alerts?only_latest=3', headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["alerts"]), 3)
        
        self.assertEqual(data["alerts"][0]["uuid"],
                         "uuid:b013c24a-4790-43d6-8b43-4d28a4ce9342")
        self.assertEqual(data["alerts"][1]["uuid"],
                         "uuid:b013c24a-4790-43d6-8b43-4d28a4ce9347")
        self.assertEqual(data["alerts"][2]["uuid"],
                         "uuid:b013c24a-4790-43d6-8b43-4d28a4ce9341")

        for i in range(1, 8):
            rv = self.app.get('/alerts?only_latest={}'.format(i),
                              headers=settings.header)
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode("utf-8"))
            self.assertEqual(len(data["alerts"]), i)
