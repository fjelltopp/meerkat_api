#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the alerts resource in Meerkat API
"""
import json
import unittest
import meerkat_api
from meerkat_api.test import db_util

class MeerkatAPIAlertsTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        self.app = meerkat_api.app.test_client()
        db_util.insert_codes(meerkat_api.db.session)
        db_util.insert_locations(meerkat_api.db.session)
        db_util.insert_alerts(meerkat_api.db.session, "cd_report")
        db_util.insert_links(meerkat_api.db.session, "cd_report")

    def tearDown(self):
        pass
    
    def test_alert(self):
        """test alert"""
        rv = self.app.get('/alert/ce9341')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["alerts"]["id"], "ce9341")
        self.assertEqual(data["alerts"]["reason"], "cmd_11")
        self.assertEqual(data["alerts"]["clinic"], 7)
        self.assertEqual(data["alerts"]["region"], 2)
        self.assertEqual(data["alerts"]["uuids"], "uuid:b013c24a-4790-43d6-8b43-4d28a4ce934d")
        self.assertEqual(data["alerts"]["data"], {"gender": "female", "age": '33'})
        self.assertIn("links", data.keys())
        link = data["links"]
        self.assertEqual(link["link_def"], "alert_investigation")
        self.assertEqual(link["data"], {'investigator': '4', 'status': 'Confirmed', 'checklist': ['Contact Tracing', 'Referral']})

    def test_aggregate_alert(self):
        """test aggregate_alerts"""
        rv = self.app.get('/aggregate_alerts')
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
        rv = self.app.get('/aggregate_alerts?location=3')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["cmd_19"], {"Pending": 1})
        self.assertEqual(sorted(list(data.keys())),
                         sorted(["cmd_19", "total"]))
        rv = self.app.get('/aggregate_alerts?location=2')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(data["total"], 7)
        # With only one reason
        rv = self.app.get('/aggregate_alerts?reason=cmd_19')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        print(data)
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["cmd_19"], {"Pending": 1})
        self.assertEqual(sorted(list(data.keys())),
                         sorted(["cmd_19", "total"]))

    
    def test_alerts(self):
        """test alerts"""
        rv = self.app.get('/alerts')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["alerts"]), 8)

        rv = self.app.get('/alerts?reason=cmd_1')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["alerts"]), 1)
        self.assertEqual(data["alerts"][0]["alerts"]["uuids"],
                         "uuid:20b2022f-fbe7-43cb-8467-c569397f3f68")
        self.assertEqual(data["alerts"][0]["alerts"]["region"], 2)

        rv = self.app.get('/alerts?reason=cmd_11')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["alerts"]), 4)

        link_count = 0
        for a in data["alerts"]:
            if "links" in a:
                link_count += 1
        self.assertEqual(link_count, 2)

        rv = self.app.get('/alerts?location=11')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["alerts"]), 1)
        rv = self.app.get('/alerts?location=1')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["alerts"]),8)
        
