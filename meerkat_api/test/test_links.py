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
        db_util.insert_links(meerkat_api.db.session, "pip_report")

    def tearDown(self):
        pass


    def test_link(self):
        """ test getting one link by it's id"""
        rv = self.app.get('/link/1')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))["link"]
        self.assertEqual(data["link_def"], "pip_followup")
        self.assertEqual(data["link_value"], "namru-1")
        self.assertEqual(data["data"],
                         {'outcome': [], 'ventilated': "yes", 'admitted_to_icu': "yes"})

    
    def test_links(self):
        """ Test getting links by type """
        rv = self.app.get('/links/pip_followup')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))["links"]
        self.assertEqual(len(data), 4)

        self.assertEqual(data["namru-4"]["to_id"], "uuid:4e46f58e-74fd-42b6-b5ca-1350328152ee")
        self.assertEqual(data["namru-2"]["id"], 2)
        
        
        rv = self.app.get('/links/pip')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))["links"]
        self.assertEqual(len(data), 3)
        self.assertEqual(data["namru-2"]["id"], 6)
        self.assertEqual(data["namru-3"]["data"], {"type": ["H1", "H3"]})
