#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the export_data resource of Meerkat API
"""
import json
import unittest
from datetime import datetime
import csv
from . import settings
import meerkat_api
from meerkat_api.test import db_util
from meerkat_abacus import data_management, model, config


class MeerkatAPITestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        self.app = meerkat_api.app.test_client()
        self.app = meerkat_api.app.test_client()
        for table in model.form_tables:
            meerkat_api.db.session.query(model.form_tables[table]).delete()
        meerkat_api.db.session.commit()
        db_util.insert_codes(meerkat_api.db.session)
        db_util.insert_locations(meerkat_api.db.session)
        db_util.insert_cases(meerkat_api.db.session, "public_health_report")
        case_form_name = config.country_config["tables"][0]
        data_management.table_data_from_csv("demo_case", model.form_tables[case_form_name],
                                            "meerkat_api/test/test_data/",
                                            meerkat_api.db.session, meerkat_api.db.engine,
                                            deviceids=["1", "2", "3", "4", "5", "6"],
                                            table_name=case_form_name)
        dr_name = config.country_config["tables"][1]
        data_management.table_data_from_csv("demo_alert", model.form_tables[dr_name],
                                            "meerkat_api/test/test_data/",
                                            meerkat_api.db.session, meerkat_api.db.engine,
                                            deviceids=["1", "2", "3", "4", "5", "6"],
                                            table_name=dr_name)

        
    def tearDown(self):
        pass


    def test_forms(self):
        """ Test the getting the fields of a form"""

        keys = ["SubmissionDate","child_age","deviceid","end", "icd_code", "index", "intro./visit", "intro_module", "meta/instanceID", "nationality", "pregnancy_complications", "pregnant", "pt./visit_date","pt1./age", "pt1./gender", "pt1./status", "start", "clinic", "district", "region"]

        rv = self.app.get('/export/forms', headers=settings.header)
        self.assertEqual(rv.status_code, 200)

        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(data["demo_alert"]), sorted(["alert_labs./return_lab","deviceid","meta/instanceID","pt./alert_id", "clinic", "region", "district"]))
        self.assertEqual(data["demo_register"], [])
        self.assertEqual(sorted(data["demo_case"]), sorted(keys))

    
    def test_export_data(self):
        """ Test the export of the data table """
        rv = self.app.get('/export/data', headers={**{"Accept": "text/csv"}, **settings.header})
        self.assertEqual(rv.status_code, 200)
        lines = rv.data.decode("utf-8").strip().split("\r\n")
        self.assertEqual(len(lines), 13)

        c = csv.DictReader(lines)
        has_found = False
        for line in c:
            if line["uuid"] == "uuid:2d14ec68-c5b3-47d5-90db-eee510ee9375":
                has_found = True
                self.assertEqual(line["sta_1"], "1")
                self.assertEqual(line["gen_1"], "1")
                self.assertEqual(line["gen_2"], "")
                self.assertEqual(line["clinic"], "Clinic 1")

        self.assertTrue(has_found)

        
    def test_export_category(self):
        """ Test getting a from with category """
        
        rv = self.app.get('/export/category/demo_case/cd_tab/cd?variables=[["icd_code", "icd code"], ["icd_name$cd_tab", "Name"], ["code$ale_2,ale_3,ale_4$Confirmed,Disregarded,Ongoing","Alert Status"], ["clinic", "Clinic"], ["meta/instanceID", "uuid"], ["end$month", "Month"], ["end$year", "Year"], ["end$epi_week", "epi_week"]]', 
headers={**{"Accept": "text/csv"}, **settings.header})

        self.assertEqual(rv.status_code, 200)
        lines = rv.data.decode("utf-8").strip().split("\r\n")
        self.assertEqual(len(lines), 8)
        c = csv.DictReader(lines)
        found_cholera = False
        found_tf = False
        found_bd = False
        found_uuid = False
        for line in c:
            if line["icd code"] == "A00":
                found_cholera = True
                self.assertEqual(line["Name"], "Cholera")
            if line["icd code"] == "A01":
                found_tf = True
                self.assertEqual(line["Name"], "Typhoid fever")
            if line["icd code"] == "A03":
                found_bd = True
                self.assertEqual(line["Name"], "Bloody diarrhoea")

            if line["uuid"] == "uuid:2d14ec68-c5b3-47d5-90db-eee510ee9376":
                self.assertEqual(line["Clinic"], "Clinic 5")
                self.assertEqual(line["icd code"], "A06")
                self.assertEqual(line["Name"], "")
                self.assertEqual(line["Month"], "5")
                self.assertEqual(line["Year"], "2016")
                self.assertEqual(line["epi_week"], "18")
                
                found_uuid = True
        self.assertTrue(found_cholera)
        self.assertTrue(found_tf)
        self.assertTrue(found_bd)
        self.assertTrue(found_uuid)
        #TODO: Test the general framework for accessing data in linked forms.

    def test_export_forms(self):
        """ Test the basic export form functionality """
        rv = self.app.get('/export/form/demo_case', headers={{"Accept": "text/csv"}, **settings.header})

        self.assertEqual(rv.status_code, 200)
        lines = rv.data.decode("utf-8").strip().split("\r\n")
        self.assertEqual(len(lines), 11)
        c = csv.DictReader(lines)
        found_uuid = False
        for line in c:
            if line["meta/instanceID"] == "uuid:2d14ec68-c5b3-47d5-90db-eee510ee9376":
                found_uuid = True
                self.assertEqual(line["deviceid"], "5")
                self.assertEqual(line["icd_code"], "A06")
        self.assertTrue(found_uuid)
        
        rv = self.app.get('/export/form/demo_case?fields=icd_code,intro./module', headers={{"Accept": "text/csv"}, **settings.header})

        self.assertEqual(rv.status_code, 200)
        lines = rv.data.decode("utf-8").strip().split("\r\n")
        self.assertEqual(len(lines), 11)
        for line in c:
            self.assertEqual(sorted(line.keys()),
                             sorted(["icd_code", "intro./module"]))

    # def test_export_alerts(self):
    #     """ Test exporting alerts """
    #     rv = self.app.get('/export/alerts', headers={"Accept": "text/csv"})
    #     self.assertEqual(rv.status_code, 200)
    #     lines = rv.data.decode("utf-8").strip().split("\r\n")
    #     self.assertEqual(len(lines), 2)
    #     c = csv.DictReader(lines)

    #     for line in c:
    #         line["reason"] = "cmd_11"
    #         line["alert_id"] = "ee9376"
    #         line["alert_investigator"] = "Clinic 1"

