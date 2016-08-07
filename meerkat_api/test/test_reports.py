#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for Meerkat API Reports
"""
import json
import unittest
import logging
from datetime import datetime
from datetime import timedelta
from sqlalchemy import extract
from dateutil import parser
import pytz

import meerkat_api
from meerkat_api.test import db_util
from meerkat_abacus import data_management
from meerkat_abacus import model
from meerkat_api.resources import reports




class MeerkatAPIReportsUtilityTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        data_management.create_db(meerkat_api.app.config["SQLALCHEMY_DATABASE_URI"],
                                  model.Base, False)
        self.app = meerkat_api.app.test_client()
        self.db = meerkat_api.db
    def tearDown(self):
        pass


    def test_get_variable_id(self):
        """Test get variable_id"""
        variable = "tot_1"
        variables = [{"tot_1": 1, "tot_2": 3} for i in range(100)]
        locations = [(1, 2, 3, 4) for i in range(50)]
        locations += [(1, 2, 3, 5) for i in range(50)]
        db_util.create_data(self.db.session, variables, locations=locations)
        conn = meerkat_api.db.engine.connect()
        start_date = datetime(datetime.now().year, 1, 1)
        end_date = datetime.now()
        # Test with different locations
        variable_id_result = reports.get_variable_id(variable,
                                                     start_date,
                                                     end_date,
                                                     1,
                                                     conn)
        self.assertEqual(variable_id_result, 100)
        variable_id_result = reports.get_variable_id(variable,
                                                     start_date,
                                                     end_date,
                                                     2,
                                                     conn)
        self.assertEqual(variable_id_result, 100)
        variable_id_result = reports.get_variable_id(variable,
                                                     start_date,
                                                     end_date,
                                                     4,
                                                     conn)
        self.assertEqual(variable_id_result, 50)
        variable_id_result = reports.get_variable_id(variable,
                                                     start_date,
                                                     end_date,
                                                     5,
                                                     conn)
        self.assertEqual(variable_id_result, 50)

        # Dates
        dates = [datetime.now() + timedelta(days=1) for i in range(100)]
        db_util.create_data(self.db.session, variables, locations=locations,
                            dates=dates)
        variable_id_result = reports.get_variable_id(variable,
                                                     start_date,
                                                     end_date,
                                                     1,
                                                     conn)
        self.assertEqual(variable_id_result, 0)
        dates = [datetime(datetime.now().year, 1, 1) for i in range(100)]
        db_util.create_data(self.db.session, variables, locations=locations,
                            dates=dates)
        variable_id_result = reports.get_variable_id(variable,
                                                     start_date,
                                                     end_date,
                                                     1,
                                                     conn)
        self.assertEqual(variable_id_result, 100)
        # So should not get any results 
        variables = [{"tot_2": 3} for i in range(100)]
        db_util.create_data(self.db.session, variables, locations=locations,
                            dates=dates)
        variable_id_result = reports.get_variable_id(variable,
                                                     start_date,
                                                     end_date,
                                                     1,
                                                     conn)
        self.assertEqual(variable_id_result, 0)

    def test_top(self):
        """Test top function"""
        values = {"two": 2, "three": 3, "four": 4, "five": 5, "one": 1}
        result = reports.top(values)
        self.assertEqual(result, ["five", "four", "three", "two", "one"])
        result = reports.top(values, number=2)
        self.assertEqual(result, ["five", "four"])
        values = {"two": 1, "three": 1, "four": 1, "five": 1, "one": 1}
        result = reports.top(values, number=2)
        self.assertEqual(result, ["five", "four"])
        result = reports.top(values, number=3)
        self.assertEqual(result, ["five", "four", "one"])

    def test_fix_dates(self):
        """Test fix dates"""

        start_date = datetime(2015, 4, 3)
        end_date = datetime(2013, 4, 5)
        new_dates = reports.fix_dates(start_date.isoformat(),
                                      end_date.isoformat())
        self.assertEqual(new_dates[0], start_date)
        self.assertEqual(new_dates[1], end_date)
        new_dates = reports.fix_dates(None, None)
        self.assertEqual(new_dates[0], datetime(datetime.now().year, 1, 1))
        self.assertLess((datetime.now() - new_dates[1]).seconds, 1)

        start_date_timezone = pytz.UTC.localize(start_date)
        end_date_timezone = pytz.UTC.localize(end_date)
        new_dates = reports.fix_dates(start_date_timezone.isoformat(),
                                      end_date_timezone.isoformat())
        self.assertEqual(new_dates[0], start_date)
        self.assertEqual(new_dates[1], end_date)

        
        
    def test_get_variables_category(self):
        """ Test get category """
        category = "gender"
        db_util.create_category(
            self.db.session,
            ["gen_1", "gen_2"],
            "gender",
            names=["Male", "Female"]
        )
        variables = [{"gen_1": 1} for i in range(37)]
        variables += [{"gen_2": 1} for i in range(94)]
        db_util.create_data(self.db.session, variables)
        conn = meerkat_api.db.engine.connect()
        start_date = datetime(datetime.now().year, 1, 1)
        end_date = datetime.now()
        location = 2
        result = reports.get_variables_category(category,
                                                start_date,
                                                end_date,
                                                location,
                                                conn)
        self.assertEqual(result["Female"], 94)
        self.assertEqual(result["Male"], 37)

        result = reports.get_variables_category(category,
                                                start_date,
                                                end_date,
                                                location,
                                                conn,
                                                use_ids=True)
        self.assertEqual(result["gen_2"], 94)
        self.assertEqual(result["gen_1"], 37)


        
    def test_get_diease_types(self):
        category = "cd"

        db_util.create_category(
            self.db.session,
            ["cd_1", "cd_2", "cd_3", "cd_4", "cd_5", "cd_6"],
            "cd"
        )
        variables = [{"cd_1": 1} for i in range(10)]
        variables += [{"cd_2": 1} for i in range(15)]
        variables += [{"cd_3": 1} for i in range(20)]
        variables += [{"cd_4": 1} for i in range(25)]
        variables += [{"cd_5": 1} for i in range(30)]
        variables += [{"cd_6": 1} for i in range(35)]
        db_util.create_data(self.db.session, variables)

        conn = meerkat_api.db.engine.connect()
        start_date = datetime(datetime.now().year, 1, 1)
        end_date = datetime.now()
        location = 2
        result = reports.get_disease_types(category,
                                           start_date,
                                           end_date,
                                           location,
                                           conn)
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0]["title"], "cd_6")
        self.assertEqual(result[1]["title"], "cd_5")
        self.assertEqual(result[2]["title"], "cd_4")
        self.assertEqual(result[3]["title"], "cd_3")
        self.assertEqual(result[4]["title"], "cd_2")

        self.assertEqual(result[0]["quantity"], 35)
        self.assertEqual(result[1]["quantity"], 30)
        self.assertEqual(result[2]["quantity"], 25)
        self.assertEqual(result[3]["quantity"], 20)
        self.assertEqual(result[4]["quantity"], 15)

        self.assertEqual(result[0]["percent"],
                        35 / (35 + 30 + 25 + 20 + 15 + 10) * 100)
        self.assertEqual(result[1]["percent"],
                        30 / (35 + 30 + 25 + 20 + 15 + 10) * 100)
        self.assertEqual(result[2]["percent"],
                        25 / (35 + 30 + 25 + 20 + 15 + 10) * 100)
        self.assertEqual(result[3]["percent"],
                        20 / (35 + 30 + 25 + 20 + 15 + 10) * 100)
        self.assertEqual(result[4]["percent"],
                        15 / (35 + 30 + 25 + 20 + 15 + 10) * 100)

    def test_make_dict(self):
        """Test make_dict"""
        new_dict = reports.make_dict("Test", 87, 23)
        self.assertEqual(new_dict["title"], "Test")
        self.assertEqual(new_dict["quantity"], 87)
        self.assertEqual(new_dict["percent"], 23)


    def test_disease_breakdown(self):
        """Test disease_breakdown"""
        diseases = {
            "Polio, Male <20": 5,
            "Polio, Male >20": 10,
            "Polio, Female <20": 3,
            "Polio, Female >20": 7,
            "Measels, Male <20": 2,
            "Measels, Male >20": 3,
            "Measels, Female <20": 4,
            "Measels, Female >20": 5,

        }
        result = reports.disease_breakdown(diseases)
        self.assertEqual(result["diseases"]["Polio"]["total"], 25)
        self.assertEqual(result["diseases"]["Polio"][">20"]["female"], 7)
        self.assertEqual(result["diseases"]["Polio"][">20"]["male"], 10)
        self.assertEqual(result["diseases"]["Polio"]["<20"]["female"], 3)
        self.assertEqual(result["diseases"]["Polio"]["<20"]["male"], 5)

        self.assertEqual(result["diseases"]["Measels"]["total"], 14)
        self.assertEqual(result["diseases"]["Measels"][">20"]["female"], 5)
        self.assertEqual(result["diseases"]["Measels"][">20"]["male"], 3)
        self.assertEqual(result["diseases"]["Measels"]["<20"]["female"], 4)
        self.assertEqual(result["diseases"]["Measels"]["<20"]["male"], 2)

        self.assertEqual(result["age_gender"][">20"]["female"], 12)
        self.assertEqual(result["age_gender"][">20"]["male"], 13)
        self.assertEqual(result["age_gender"]["<20"]["female"], 7)
        self.assertEqual(result["age_gender"]["<20"]["male"], 7)

    def test_get_latest_category(self):
        """Test get_latest_category"""
        
        db_util.create_category(
            self.db.session,
            ["pop_1", "pop_2", "pop_3", "pop_4"],
            "population",
            ["Population, Male <20", "Population, Female <20",
             "Population, Male >20", "Population, Female >20"]
        )
        variables = [
            {"pop_1": 5, "pop_2": 6, "pop_3": 7, "pop_4": 8},
            {"pop_1": 15, "pop_2": 16, "pop_3": 17, "pop_4": 0}
        ]
        dates = [datetime(2016, 1, 1), datetime(2016, 2, 2)]
        db_util.create_data(self.db.session, variables, dates=dates)
        start_date = datetime(datetime.now().year, 1, 1)
        end_date = datetime.now()
        results = reports.get_latest_category("population", 4, start_date, end_date)
        self.assertEqual(results["<20"]["male"], 15)
        self.assertEqual(results[">20"]["male"], 17)
        self.assertEqual(results["<20"]["female"], 16)
        self.assertEqual(results[">20"]["female"], 0)
        variables = [
            {"pop_1": 5, "pop_2": 6, "pop_3": 7, "pop_4": 8},
            {"pop_1": 3}
        ]

    def test_refugee_disease(self):
        """Test refugee_disease"""
        diseases = {
            "Polio, Male <20": 1,
            "Polio, Male >20": 1,
            "Polio, Female <20": 1,
            "Polio, Female >20": 1,
            "Measels, Male <20": 2,
            "Measels, Male >20": 2,
            "Measels, Female <20": 2,
            "Measels, Female >20": 2,
            "Measels1, Male <20": 3,
            "Measels1, Male >20": 3,
            "Measels1, Female <20": 3,
            "Measels1, Female >20": 3,
            "Measels2, Male <20": 4,
            "Measels2, Male >20": 4,
            "Measels2, Female <20": 4,
            "Measels2, Female >20": 4,
            "Measels3, Male <20": 5,
            "Measels3, Male >20": 5,
            "Measels3, Female <20": 5,
            "Measels3, Female >20": 5,
            "Measels4, Male <20": 6,
            "Measels4, Male >20": 6,
            "Measels4, Female <20": 6,
            "Measels4, Female >20": 6,
            "Measels5, Male <20": 7,
            "Measels5, Male >20": 7,
            "Measels5, Female <20": 7,
            "Measels5, Female >20": 7,
            

        }
        results = reports.refugee_disease(diseases)

        self.assertEqual(results[0]["title"], "Measels5")
        self.assertEqual(results[1]["title"], "Measels4")
        self.assertEqual(results[2]["title"], "Measels3")
        self.assertEqual(results[3]["title"], "Measels2")
        self.assertEqual(results[4]["title"], "Measels1")

        self.assertEqual(results[0]["quantity"], 7 * 4)
        self.assertEqual(results[1]["quantity"], 6 * 4)
        self.assertEqual(results[2]["quantity"], 5 * 4)
        self.assertEqual(results[3]["quantity"], 4 * 4)
        self.assertEqual(results[4]["quantity"], 3 * 4)
        total = (7 + 6 + 5 + 4 + 3 + 2 + 1) * 4
        self.assertEqual(results[0]["percent"],
                         7 * 4 / total * 100 )
        self.assertEqual(results[1]["percent"],
                         6 * 4 / total  * 100)
        self.assertEqual(results[2]["percent"],
                         5 * 4 / total * 100)
        self.assertEqual(results[3]["percent"],
                         4 * 4 / total * 100)
        self.assertEqual(results[4]["percent"],
                         3 * 4 / total * 100)

def assert_dict(class_self, d, title, quantity, percent):
    """
    Check a dict

    Args: 
       class_self: class instance
       d: dict
       title: title
       quantity
       percent
    """
    class_self.assertEqual(d["title"], title)
    class_self.assertEqual(d["quantity"], quantity)
    class_self.assertEqual(d["percent"], percent)
        
class MeerkatAPIReportsTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = "" 
        self.app = meerkat_api.app.test_client()
        self.db = meerkat_api.db
    def tearDown(self):
        pass


    def test_non_location(self):
        """ Teseting that reports returns None if wrong locations"""
        db_util.insert_codes(self.db.session)
        db_util.insert_locations(self.db.session)
        reports = [
            "public_health", "cd_public_health", "ncd_public_health", "epi_monitoring",
            "ncd_report", "cd_report", "refugee_public_health", "refugee_detail", "refugee_cd"
            ]
        for report in reports:
            rv = self.app.get('/reports/{}/99'.format(report))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode("utf-8"))
            self.assertEqual(data, None)

        
    
    def test_dates(self):
        """ Testing that the dates are handled correctly """
        db_util.insert_codes(self.db.session)
        db_util.insert_locations(self.db.session)
        self.db.session.query(model.Data).delete()
        self.db.session.commit()
        reports = [
            "public_health", "cd_public_health", "ncd_public_health", "epi_monitoring",
            "ncd_report", "cd_report", "refugee_public_health", "refugee_detail", "refugee_cd"
        ]
        for report in reports:
            rv = self.app.get('/reports/{}/1'.format(report))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode("utf-8"))["data"]
            self.assertEqual(data["start_date"],
                             datetime(datetime.now().year, 1, 1).isoformat())
            self.assertLess((datetime.now() - parser.parse(data["end_date"])).seconds , 12)

            # With specified dates
            end_date = datetime(2015, 8, 7).isoformat()
            start_date = datetime(2014, 2, 3).isoformat()
            rv = self.app.get('/reports/{}/1/{}'.format(report, end_date))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode("utf-8"))["data"]
            self.assertEqual(data["start_date"],
                             datetime(2015, 1, 1).isoformat())
            self.assertEqual(data["end_date"],
                             end_date)
            
            rv = self.app.get('/reports/{}/1/{}/{}'.format(report, end_date, start_date))
            self.assertEqual(rv.status_code, 200)
            data = json.loads(rv.data.decode("utf-8"))["data"]
            self.assertEqual(data["start_date"],
                             start_date)
            self.assertEqual(data["end_date"],
                             end_date)


    def test_public_health(self):
        """ test the public health report """
        db_util.insert_codes(self.db.session)
        db_util.insert_locations(self.db.session)
        db_util.insert_cases(self.db.session, "public_health_report")
        db_util.insert_alerts(self.db.session, "public_health_report")
        end_date = datetime(2015, 12, 31).isoformat()
        start_date = datetime(2015, 1, 1).isoformat()
        rv = self.app.get('/reports/public_health/1/{}/{}'.format(end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))["data"]

        self.assertEqual(data["total_cases"], 10)
        self.assertEqual(data["total_consultations"], 15)
        self.assertEqual(data["clinic_num"], 4)
        self.assertEqual(data["alerts_total"], 3)
        
        # Reporting Sites
        assert_dict(self, data["reporting_sites"][0], "Region 1", 6, 60.0)
        assert_dict(self, data["reporting_sites"][1], "Region 2", 4, 40.0)

        # Demographics
        self.assertEqual(data["percent_cases_male"], 30.0)
        self.assertEqual(data["percent_cases_female"], 70.0)
        self.assertEqual(data["percent_cases_lt_5yo"], 20.0)
        self.assertEqual(data["demographics"][0]["age"], "<5")
        self.assertEqual(data["demographics"][0]["percent"], 20)
        self.assertEqual(data["demographics"][0]["male"]["quantity"], 2)
        self.assertEqual(data["demographics"][0]["male"]["percent"], 100.0)
        self.assertEqual(data["demographics"][0]["female"]["quantity"], 0)
        self.assertEqual(data["demographics"][0]["female"]["percent"], 0)

        self.assertEqual(data["demographics"][1]["age"], "5-9")
        self.assertEqual(data["demographics"][1]["percent"], 20)
        self.assertEqual(data["demographics"][1]["male"]["quantity"], 0)
        self.assertEqual(data["demographics"][1]["male"]["percent"], 0)
        self.assertEqual(data["demographics"][1]["female"]["quantity"], 2)
        self.assertEqual(data["demographics"][1]["female"]["percent"], 100.0)

        self.assertEqual(data["demographics"][2]["age"], "10-14")
        self.assertEqual(data["demographics"][2]["percent"], 20)
        self.assertEqual(data["demographics"][2]["male"]["quantity"], 1)
        self.assertEqual(data["demographics"][2]["male"]["percent"], 50.0)
        self.assertEqual(data["demographics"][2]["female"]["quantity"], 1)
        self.assertEqual(data["demographics"][2]["female"]["percent"], 50.0)

        self.assertEqual(data["demographics"][3]["age"], "15-19")
        self.assertEqual(data["demographics"][3]["percent"], 20)
        self.assertEqual(data["demographics"][3]["male"]["quantity"], 0)
        self.assertEqual(data["demographics"][3]["male"]["percent"], 0)
        self.assertEqual(data["demographics"][3]["female"]["quantity"], 2)
        self.assertEqual(data["demographics"][3]["female"]["percent"], 100.0)

        self.assertEqual(data["demographics"][4]["age"], "20-59")
        self.assertEqual(data["demographics"][4]["percent"], 20)
        self.assertEqual(data["demographics"][4]["male"]["quantity"], 0)
        self.assertEqual(data["demographics"][4]["male"]["percent"], 0)
        self.assertEqual(data["demographics"][4]["female"]["quantity"], 2)
        self.assertEqual(data["demographics"][4]["female"]["percent"], 100.0)
        
        # Nationality

        assert_dict(self, data["nationality"][0], "Null Island", 7, 70.0)
        assert_dict(self, data["nationality"][1], "Demo", 3, 30.0)
        # Status
        assert_dict(self, data["patient_status"][0], "Jordanian", 9, 90.0)
        assert_dict(self, data["patient_status"][1], "Refugee", 1, 10.0)

        # Morbitidy
        self.assertEqual(data["percent_morbidity_non_communicable"], 20.0)
        self.assertEqual(data["percent_morbidity_communicable"], 70.0)
        self.assertEqual(data["percent_morbidity_mental_health"], 10.0)

        assert_dict(self, data["presenting_complaints"][0], "Communicable disease", 7, 70.0)
        assert_dict(self, data["presenting_complaints"][1], "Non-communicable disease", 2, 20.0)
        assert_dict(self, data["presenting_complaints"][2], "Mental Health", 1, 10.0)

        # Communicable Disease
        assert_dict(self, data["morbidity_communicable"][0], "Intestinal infectious diseases", 7, 100.0)
        assert_dict(self, data["morbidity_communicable_tab"][0], "Cholera", 7, 100.0)
        # NonCommunicable Disease
        assert_dict(self, data["morbidity_non_communicable"][0], "Diabetes mellitus", 1, 100.0)
        assert_dict(self, data["morbidity_non_communicable_tab"][0], "Diabetes mellitus", 1, 50.0)
        assert_dict(self, data["morbidity_non_communicable_tab"][1], "Hypertension", 1, 50.0)        

        # Mental Health
        assert_dict(self,data["mental_health"][0], "Organic,including symptomatic, mental disorders", 1, 100.0)
        # Public Health Indicators

        self.assertEqual(data["public_health_indicators"][0]["quantity"], 10)
        self.assertEqual(data["public_health_indicators"][1]["quantity"], 1)
        self.assertEqual(data["public_health_indicators"][2]["quantity"], 1)
        self.assertEqual(data["public_health_indicators"][3]["quantity"], 1)
        self.assertEqual(data["public_health_indicators"][4]["quantity"], 1)
        self.assertEqual(data["public_health_indicators"][5]["quantity"], 1)
        self.assertEqual(data["public_health_indicators"][6]["quantity"], 1)


        # test with a different Location

        rv = self.app.get('/reports/public_health/2/{}/{}'.format(end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))["data"]

        self.assertEqual(data["total_cases"], 6)
        self.assertEqual(data["total_consultations"], 15)
        self.assertEqual(data["clinic_num"], 3)

        
    def test_ncd_public_health(self):
        """ test the ncd public health report """
        db_util.insert_codes(self.db.session)
        db_util.insert_locations(self.db.session)
        db_util.insert_cases(self.db.session, "ncd_public_health_report")

        end_date = datetime(2015, 12, 31).isoformat()
        start_date = datetime(2015, 1, 1).isoformat()
        rv = self.app.get('/reports/ncd_public_health/1/{}/{}'.format(end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))["data"]

        self.assertEqual(data["total_cases"], 6)
        self.assertEqual(data["clinic_num"], 4)
        
        # Reporting Sites
        assert_dict(self, data["reporting_sites"][0], "Region 1", 4, 4 / 6 * 100)
        assert_dict(self, data["reporting_sites"][1], "Region 2", 2, 2 / 6 *100)

        # Demographics

        self.assertEqual(data["percent_cases_female"], 50.0)
        self.assertEqual(data["percent_cases_male"], 50.0)
        self.assertEqual(data["percent_cases_lt_5yo"], 2 / 6 * 100)
        self.assertEqual(data["demographics"][0]["age"], "<5")
        self.assertEqual(data["demographics"][0]["percent"], round(2*100/6, 2))
        self.assertEqual(data["demographics"][0]["male"]["quantity"], 1)
        self.assertEqual(data["demographics"][0]["male"]["percent"], 50.0)
        self.assertEqual(data["demographics"][0]["female"]["quantity"], 1)
        self.assertEqual(data["demographics"][0]["female"]["percent"], 50.0)
        
        self.assertEqual(data["demographics"][1]["age"], "5-9")
        self.assertEqual(data["demographics"][1]["percent"], round(2*100/6, 2))
        self.assertEqual(data["demographics"][1]["male"]["quantity"], 2)
        self.assertEqual(data["demographics"][1]["male"]["percent"], 100.0)
        self.assertEqual(data["demographics"][1]["female"]["quantity"], 0)
        self.assertEqual(data["demographics"][1]["female"]["percent"], 0)
        
        self.assertEqual(data["demographics"][2]["age"], "10-14")
        self.assertEqual(data["demographics"][2]["percent"], 0)
        self.assertEqual(data["demographics"][2]["male"]["quantity"], 0)
        self.assertEqual(data["demographics"][2]["male"]["percent"], 0)
        self.assertEqual(data["demographics"][2]["female"]["quantity"], 0)
        self.assertEqual(data["demographics"][2]["female"]["percent"], 0)

        self.assertEqual(data["demographics"][3]["age"], "15-19")
        self.assertEqual(data["demographics"][3]["percent"], round(100/6, 2))
        self.assertEqual(data["demographics"][3]["male"]["quantity"], 0)
        self.assertEqual(data["demographics"][3]["male"]["percent"], 0)
        self.assertEqual(data["demographics"][3]["female"]["quantity"], 1)
        self.assertEqual(data["demographics"][3]["female"]["percent"], 100.0)

        self.assertEqual(data["demographics"][4]["age"], "20-59")
        self.assertEqual(data["demographics"][4]["percent"], round(1*100/6, 2))
        self.assertEqual(data["demographics"][4]["male"]["quantity"], 0)
        self.assertEqual(data["demographics"][4]["male"]["percent"], 0)
        self.assertEqual(data["demographics"][4]["female"]["quantity"], 1)
        self.assertEqual(data["demographics"][4]["female"]["percent"], 100.0)
        
        # Nationality
        assert_dict(self, data["nationality"][0], "Demo", 5, 5 / 6 * 100)
        assert_dict(self, data["nationality"][1], "Null Island", 1, 1 / 6 * 100)

        # Status
        assert_dict(self, data["patient_status"][0], "Jordanian", 5, 5 / 6 * 100)
        assert_dict(self, data["patient_status"][1], "Refugee", 1, 1 / 6 * 100)

        # NonCommunicable Disease
        assert_dict(self, data["morbidity_non_communicable_icd"][0], "Diabetes mellitus", 3, 50.0)
        assert_dict(self, data["morbidity_non_communicable_icd"][1], "Malignant neoplasms of urinary tract", 3, 50.0)
        assert_dict(self, data["morbidity_non_communicable_ncd_tab"][0], "Diabetes mellitus", 3, 50.0)
        assert_dict(self, data["morbidity_non_communicable_ncd_tab"][1], "Hypertension", 3, 50.0)        
        # Public Health Indicators

        self.assertEqual(data["public_health_indicators"][0]["quantity"], 6)
        self.assertEqual(data["public_health_indicators"][1]["quantity"], 1)
        self.assertEqual(data["public_health_indicators"][2]["quantity"], 1)

        # test with a different Location

        rv = self.app.get('/reports/ncd_public_health/2/{}/{}'.format(end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))["data"]

        self.assertEqual(data["total_cases"], 4)
        self.assertEqual(data["clinic_num"], 3)

    def test_cd_public_health(self):
        """ test the cd public health report """
        db_util.insert_codes(self.db.session)
        db_util.insert_locations(self.db.session)
        db_util.insert_cases(self.db.session, "public_health_report")
        db_util.insert_alerts(self.db.session, "public_health_report")
        db_util.insert_links(self.db.session, "public_health_report")
        end_date = datetime(2015, 12, 31).isoformat()
        start_date = datetime(2015, 1, 1).isoformat()
        rv = self.app.get('/reports/cd_public_health/1/{}/{}'.format(end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))["data"]

        self.assertEqual(data["total_cases"], 7)
        self.assertEqual(data["clinic_num"], 4)
        self.assertEqual(data["alerts_total"], 3)
        
        # Reporting Sites
        assert_dict(self, data["reporting_sites"][0], "Region 1", 6, 6 / 7 *100)
        assert_dict(self, data["reporting_sites"][1], "Region 2", 1, 1 / 7 *100)

        # Demographics
        logging.warning(data["demographics"])
        self.assertEqual(data["percent_cases_male"], 3 / 7 * 100)
        self.assertEqual(data["percent_cases_female"], 4 / 7 * 100)
        self.assertEqual(data["percent_cases_lt_5yo"], 2 / 7 *100)
        self.assertEqual(data["demographics"][0]["age"], "<5")

        self.assertEqual(data["demographics"][0]["male"]["quantity"], 2)
        self.assertEqual(data["demographics"][0]["percent"], round(2*100/7, 2))
        self.assertEqual(data["demographics"][0]["male"]["percent"], 100)
        self.assertEqual(data["demographics"][0]["female"]["quantity"], 0)
        self.assertEqual(data["demographics"][0]["female"]["percent"], 0)

        self.assertEqual(data["demographics"][1]["age"], "5-9")
        self.assertEqual(data["demographics"][1]["percent"], round(2*100/7, 2))
        self.assertEqual(data["demographics"][1]["male"]["quantity"], 0)
        self.assertEqual(data["demographics"][1]["male"]["percent"], 0)
        self.assertEqual(data["demographics"][1]["female"]["quantity"], 2)
        self.assertEqual(data["demographics"][1]["female"]["percent"], 100)

        self.assertEqual(data["demographics"][2]["age"], "10-14")
        self.assertEqual(data["demographics"][2]["percent"], round(2*100/7, 2))
        self.assertEqual(data["demographics"][2]["male"]["quantity"], 1)
        self.assertEqual(data["demographics"][2]["male"]["percent"], 50.0)
        self.assertEqual(data["demographics"][2]["female"]["quantity"], 1)
        self.assertEqual(data["demographics"][2]["female"]["percent"], 50.0)

        self.assertEqual(data["demographics"][3]["age"], "15-19")
        self.assertEqual(data["demographics"][3]["percent"], round(1*100/7, 2))
        self.assertEqual(data["demographics"][3]["male"]["quantity"], 0)
        self.assertEqual(data["demographics"][3]["male"]["percent"], 0)
        self.assertEqual(data["demographics"][3]["female"]["quantity"], 1)
        self.assertEqual(data["demographics"][3]["female"]["percent"], 100.0)
        
        # Nationality

        assert_dict(self, data["nationality"][0], "Null Island", 6, 6 / 7 * 100)
        assert_dict(self, data["nationality"][1], "Demo", 1, 1 / 7 * 100)
        # Status
        assert_dict(self, data["patient_status"][0], "Jordanian", 7, 100.0)

        # Communicable Disease
        assert_dict(self, data["morbidity_communicable_icd"][0], "Intestinal infectious diseases", 7, 100.0)
        assert_dict(self, data["morbidity_communicable_cd_tab"][0], "Cholera", 7, 100.0)

        # Public Health Indicators
        self.assertEqual(data["public_health_indicators"][0]["quantity"], 7)
        self.assertEqual(data["public_health_indicators"][1]["quantity"], 1)
        self.assertEqual(data["public_health_indicators"][2]["quantity"], 1)
        self.assertEqual(data["public_health_indicators"][3]["quantity"], 3)
        self.assertEqual(data["public_health_indicators"][4]["quantity"], 2)

        # Test with a different Location
        rv = self.app.get('/reports/cd_public_health/2/{}/{}'.format(end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))["data"]

        self.assertEqual(data["total_cases"], 6)
        self.assertEqual(data["clinic_num"], 3)
    # def test_cd_report(self):
    #     location = 2
    #     rv = self.app.get('/reports/cd_report/{}'.format(location))
    #     self.assertEqual(rv.status_code, 200)
    #     data = json.loads(rv.data.decode("utf-8"))

    def test_ncd_report(self):
        """ Test ncd report """
        db_util.insert_codes(self.db.session)
        db_util.insert_locations(self.db.session)
        db_util.insert_cases(self.db.session, "ncd_report")
        end_date = datetime(2015, 12, 31).isoformat()
        start_date = datetime(2015, 1, 1).isoformat()
        rv = self.app.get('/reports/ncd_report/1/{}/{}'.format(end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))

        # Diabetes
        self.assertEqual( data["diabetes"]["age"]["titles"],
                          ['reg', 'Total', '<5', '5-9', '10-14', '15-19', '20-59', '>60'] )
        self.assertEqual( data["diabetes"]["age"]["data"][0], 
                          { "title": "Total", "values": [2, 4, 0, 1, 1, 0, 0] } )
        self.assertEqual( data["diabetes"]["age"]["data"][1], 
                          { "title": "Region 1", "values": [2, 3, 0, 1, 0, 0, 0] } )
        self.assertEqual( data["diabetes"]["age"]["data"][2], 
                          { "title": "Region 2", "values": [0, 1, 0, 0, 1, 0, 0] } )


        self.assertEqual(data["diabetes"]["complications"]["titles"],
                         ['reg', 'tot', 'gen_1', 'gen_2', 'lab_4', 'lab_5', 'lab_7', 'lab_9', 'com_2', 'smo_2', 'lab_11']
        )
        self.assertEqual(data["diabetes"]["complications"]["data"][0],
                         {"title": "Total",
                          "values": [4, [2 , 2/ 4 * 100], [2, 2/4 * 100] , [1, 50], [1, 50], [1, 100], [1, 50], [1, 25], [1, 50], [1, 100]]}
                         )
        self.assertEqual(data["diabetes"]["complications"]["data"][1],
                         {"title": "Region 1",
                          "values": [3, [2 , 2/ 3 * 100], [1, 1/3 * 100] , [1, 50], [1, 50], [0, 0], [1, 50], [0, 0], [1, 50], [0, 0]]}
                         )
        self.assertEqual(data["diabetes"]["complications"]["data"][2],
                         {"title": "Region 2",
                          "values": [1, [0 , 0], [1, 100] , [0, 0], [0, 0], [1, 100], [0, 0], [1, 100], [0, 0], [1, 100]]}
                         )
        

        # Hypertension
        self.assertEqual(data["hypertension"]["age"]["titles"],
                         ['reg', 'Total', '<5', '5-9', '10-14', '15-19', '20-59', '>60'])
        self.assertEqual(data["hypertension"]["age"]["data"][0],
                         {"title": "Total",
                          "values": [0, 2, 4, 1, 1, 0, 0]}
                         )
        self.assertEqual(data["hypertension"]["age"]["data"][1],
                         {"title": "Region 1",
                          "values": [0, 1, 0, 1, 1, 0, 0]}
                         )
        self.assertEqual(data["hypertension"]["age"]["data"][2],
                         {"title": "Region 2",
                          "values": [0, 2, 2, 0, 0, 0, 0]}
                         )

        
        self.assertEqual(data["hypertension"]["complications"]["titles"],
                         ['reg', 'tot', 'gen_1', 'gen_2', 'lab_4', 'lab_5', 'lab_2', 'com_1', 'smo_2', 'lab_11'])

     
        self.assertEqual(data["hypertension"]["complications"]["data"][0],
                         {"title": "Total",
                          "values": [4, [2, 50], [2, 50], [1, 100], [0,0], [1, 50], [1, 1/4*100], [1, 100], [1,100]]}
                         )

        self.assertEqual(data["hypertension"]["complications"]["data"][1],
                         {"title": "Region 1",
                          "values": [2, [0, 0], [2, 100], [1, 100],[0, 0], [0, 0], [1, 50], [0, 0], [0, 0]]}
                         )
     
        self.assertEqual(data["hypertension"]["complications"]["data"][2],
                         {"title": "Region 2",
                          "values": [2, [2, 100], [0, 0], [0, 0], [0, 0], [1, 50], [0, 0], [1, 100], [1, 100]]}
                         )
     



    def test_cd_report(self):
        """ Test ncd report """
        db_util.insert_codes(self.db.session)
        db_util.insert_locations(self.db.session)
        db_util.insert_alerts(self.db.session, "cd_report")
        db_util.insert_links(self.db.session, "cd_report")
        end_date = datetime(2015, 12, 31).isoformat()
        start_date = datetime(2015, 1, 1).isoformat()
        rv = self.app.get('/reports/cd_report/1/{}/{}'.format(end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))["data"]["communicable_diseases"]

        self.assertIn("Cholera", data)
        self.assertIn('Typhoid fever', data)
        self.assertIn('Diphtheria', data)
        self.assertEqual(len(data.keys()), 3)
        # Cholera
        self.assertEqual(data["Cholera"]["weeks"],
                         ['Week 1, 2015', 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53])
        # One suspected case in epi_week 16 and no confirmed cases
        self.assertEqual(data["Cholera"]["suspected"],
                         [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
        self.assertEqual(data["Cholera"]["confirmed"],
                         [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])

        # Typhoid Fever
        self.assertEqual(data["Typhoid fever"]["weeks"],
                         ['Week 1, 2015', 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53])
        # One suspected case in epi_week 16 and no confirmed cases
        self.assertEqual(data["Typhoid fever"]["suspected"],
                         [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
        self.assertEqual(data["Typhoid fever"]["confirmed"],
                         [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])

        # Diphtheria
        self.assertEqual(data["Diphtheria"]["weeks"],
                         ['Week 1, 2015', 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53])
        # One suspected case in epi_week 16 and no confirmed cases
        self.assertEqual(data["Diphtheria"]["suspected"],
                         [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
        self.assertEqual(data["Diphtheria"]["confirmed"],
                         [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])

    def test_pip_report(self):
        """ Test pip report """
        db_util.insert_codes(self.db.session)
        db_util.insert_locations(self.db.session)
        db_util.insert_cases(self.db.session, "pip_report")
        db_util.insert_links(self.db.session, "pip_report")
        end_date = datetime(2015, 12, 31).isoformat()
        start_date = datetime(2015, 1, 1).isoformat()
        rv = self.app.get('/reports/pip/1/{}/{}'.format(end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))["data"]

        self.assertEqual(data["total_cases"], 8)
        self.assertEqual(data["num_clinic"], 2)

        # Demographics

        self.assertEqual(data["percent_cases_male"], 3 / 8 * 100)
        self.assertEqual(data["percent_cases_female"], 5 / 8 * 100)
        self.assertEqual(data["demographics"][0]["age"], "<5")
        self.assertEqual(data["demographics"][0]["percent"], 25.0)
        self.assertEqual(data["demographics"][0]["male"]["quantity"], 1)
        self.assertEqual(data["demographics"][0]["male"]["percent"], 50.0)
        self.assertEqual(data["demographics"][0]["female"]["quantity"], 1)
        self.assertEqual(data["demographics"][0]["female"]["percent"], 50.0)

        self.assertEqual(data["demographics"][1]["age"], "5-9")
        self.assertEqual(data["demographics"][1]["percent"], 25.0)
        self.assertEqual(data["demographics"][1]["male"]["quantity"], 2)
        self.assertEqual(data["demographics"][1]["male"]["percent"], 100.0)
        self.assertEqual(data["demographics"][1]["female"]["quantity"], 0)
        self.assertEqual(data["demographics"][1]["female"]["percent"], 0)

        self.assertEqual(data["demographics"][2]["age"], "10-14")
        self.assertEqual(data["demographics"][2]["percent"], 25.0)
        self.assertEqual(data["demographics"][2]["male"]["quantity"], 0)
        self.assertEqual(data["demographics"][2]["male"]["percent"], 0)
        self.assertEqual(data["demographics"][2]["female"]["quantity"], 2)
        self.assertEqual(data["demographics"][2]["female"]["percent"], 100)

        self.assertEqual(data["demographics"][3]["age"], "15-19")
        self.assertEqual(data["demographics"][0]["percent"], 25.0)
        self.assertEqual(data["demographics"][3]["male"]["quantity"], 0)
        self.assertEqual(data["demographics"][3]["male"]["percent"], 0)
        self.assertEqual(data["demographics"][3]["female"]["quantity"], 2)
        self.assertEqual(data["demographics"][3]["female"]["percent"], 100.0)
        
        # Indicators
        assert_dict(self, data["pip_indicators"][0], "Total Cases", 8, 100)
        assert_dict(self, data["pip_indicators"][1], "Patients followed up", 4, 50)
        assert_dict(self, data["pip_indicators"][2], "Laboratory results recorded", 3, 3 / 8 * 100)
        assert_dict(self, data["pip_indicators"][3], "Patients admitted to ICU", 3, 3 / 8 * 100)
        assert_dict(self, data["pip_indicators"][4], "Patients ventilated", 2, 25)
        assert_dict(self, data["pip_indicators"][5], "Mortality", 1, 12.5)

        self.assertEqual(data["cases_chronic"], 2)
        self.assertEqual(data["percent_cases_chronic"], 25)

        # Nationality
        assert_dict(self, data["nationality"][0], "Null Island", 7, 7 / 8 *100)
        assert_dict(self, data["nationality"][1], "Demo", 1, 12.5)

        # Status
        assert_dict(self, data["patient_status"][0], "Jordanian", 7, 7 / 8 * 100)
        assert_dict(self, data["patient_status"][1], "Refugee", 1, 12.5)

        # Reporting Sites
        assert_dict(self, data["reporting_sites"][0], "Clinic 2", 6, 75.0)
        assert_dict(self, data["reporting_sites"][1], "Clinic 4", 2, 25.0)

        #Timeline
        #Set up expected data.
        weeks = [i+1 for i in range(0,53)]
        weeks[0] = 'Week 1, 2015'

        zero = [0 for i in range(0,53)]

        suspected = [0 for i in range(0,53)]
        suspected[17] = 4
        suspected[25] = 2
        suspected[30] = 2

        flu_type = [0 for i in range(0,53)]
        flu_type[0] = 1

        expected = [
            { 'title':'B', 'values': flu_type },
            { 'title':'H3', 'values': zero },
            { 'title':'H1N1', 'values': flu_type },
            { 'title':'Mixed', 'values': flu_type }
        ]

        #Check that returned data is as expected.
        self.assertEqual(data["timeline"]["weeks"], weeks)
        self.assertEqual(data["timeline"]["suspected"], suspected)
        for item in expected:
            passed = item in data["timeline"]["confirmed"]
            if not passed:
                logging.warning( 
                    "Item {} not found in timeline data as expected.".format( item['title'] )
                )
            self.assertTrue( passed )





    def test_refugee_public_health(self):
        """ Test refugee public health report"""
        db_util.insert_codes(self.db.session)
        db_util.insert_locations(self.db.session)
        db_util.insert_cases(self.db.session, "refugee_data")
        end_date = datetime(2015, 12, 31).isoformat()
        start_date = datetime(2015, 1, 1).isoformat()
        rv = self.app.get('/reports/refugee_public_health/1/{}/{}'.format(end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))["data"]

        self.assertEqual(data["total_population"],
                         2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12 + 12)
        self.assertEqual(data["clinic_num"], 2)
        self.assertEqual(data["n_clinicians"], 6)
        self.assertEqual(data["percent_cases_male"], 46 / 89 * 100)
        self.assertEqual(data["percent_cases_female"], 43 / 89 * 100)
        self.assertEqual(data["percent_cases_lt_5yo"], 18 / 89 * 100)
        self.assertEqual(data["total_consultations"], 170)
        self.assertEqual(data["total_cases"], 25)
        

        self.assertEqual(data["percent_morbidity_communicable"], 6 / 25 * 100)
        self.assertEqual(data["percent_morbidity_non_communicable"], 6 / 25 * 100)
        self.assertEqual(data["percent_morbidity_mental_health"], 10 / 25 * 100)
        self.assertEqual(data["percent_morbidity_injury_health"], 3 / 25 *100)

        assert_dict(self, data["presenting_complaints"][0],
                    "Communicable Disease", 6, 6 / 25 * 100)
        assert_dict(self, data["presenting_complaints"][1],
                    "Non-Communicable Disease", 6, 6 / 25 * 100)
        assert_dict(self, data["presenting_complaints"][2],
                    "Mental Health", 10, 10 / 25 * 100)
        assert_dict(self, data["presenting_complaints"][3],
                    "Injury", 3, 3 / 25 * 100)
        
        # pop = 89, mortality = 14, u5_mortalit = 6, u5_pop = 18
        self.assertEqual(data["crude_mortality_rate"], 14 / 89 * 1000)
        self.assertEqual(data["u5_crude_mortality_rate"], 6 / 18 * 1000)


        # Public health indicators days of report = 364
        assert_dict(self, data["public_health_indicators"][0],
                    "Health Utilisation Rate",
                    170 / 89 / 364 * 365,
                    None)
        assert_dict(self, data["public_health_indicators"][1],
                    "Number of consultations per clinician per day",
                    170 / 6 / 364,
                    None)
        assert_dict(self, data["public_health_indicators"][2],
                    "Hospitalisation rate",
                    3 / 170,
                    None)
        assert_dict(self, data["public_health_indicators"][3],
                    "Referral rate",
                    9 / 170,
                    None)
        assert_dict(self, data["public_health_indicators"][4],
                    "Crude Mortality Rate (CMR)",
                     14 / 89 * 1000,
                    None)
        assert_dict(self, data["public_health_indicators"][5],
                    "Under-five Mortality Rate (U5MR)",
                    6 / 18 * 1000,
                    None)
        
        # Demographics
        
        self.assertEqual(data["demographics"][0]["age"], "0-1")
        self.assertEqual(data["demographics"][0]["male"]["quantity"], 3)
        self.assertEqual(data["demographics"][0]["male"]["percent"], 3 / 7 * 100)
        self.assertEqual(data["demographics"][0]["female"]["quantity"], 4)
        self.assertEqual(data["demographics"][0]["female"]["percent"], 4 / 7 * 100)

        self.assertEqual(data["demographics"][1]["age"], "1-4")
        self.assertEqual(data["demographics"][1]["male"]["quantity"], 5)
        self.assertEqual(data["demographics"][1]["male"]["percent"], 5 / 11 * 100)
        self.assertEqual(data["demographics"][1]["female"]["quantity"], 6)
        self.assertEqual(data["demographics"][1]["female"]["percent"], 6 / 11 * 100)

        self.assertEqual(data["demographics"][2]["age"], "5-14")
        self.assertEqual(data["demographics"][2]["male"]["quantity"], 7)
        self.assertEqual(data["demographics"][2]["male"]["percent"], 7 / 15 * 100)
        self.assertEqual(data["demographics"][2]["female"]["quantity"], 8)
        self.assertEqual(data["demographics"][2]["female"]["percent"], 8 / 15 * 100)

        self.assertEqual(data["demographics"][3]["age"], "15-44")
        self.assertEqual(data["demographics"][3]["male"]["quantity"], 9)
        self.assertEqual(data["demographics"][3]["male"]["percent"], 9 / 10 * 100)
        self.assertEqual(data["demographics"][3]["female"]["quantity"], 1)
        self.assertEqual(data["demographics"][3]["female"]["percent"], 1 / 10 * 100)

        self.assertEqual(data["demographics"][4]["age"], "45-64")
        self.assertEqual(data["demographics"][4]["male"]["quantity"], 10)
        self.assertEqual(data["demographics"][4]["male"]["percent"], 10 / 21 * 100)
        self.assertEqual(data["demographics"][4]["female"]["quantity"], 11)
        self.assertEqual(data["demographics"][4]["female"]["percent"], 11 / 21 * 100)

        self.assertEqual(data["demographics"][5]["age"], ">65")
        self.assertEqual(data["demographics"][5]["male"]["quantity"], 12)
        self.assertEqual(data["demographics"][5]["male"]["percent"], 12 / 25 * 100)
        self.assertEqual(data["demographics"][5]["female"]["quantity"], 13)
        self.assertEqual(data["demographics"][5]["female"]["percent"], 13 / 25 * 100)

        # Reporting Sites
        
        assert_dict(self, data["reporting_sites"][0], "Clinic 1", 9, 9 / 25 * 100)
        assert_dict(self, data["reporting_sites"][1], "Clinic 5", 16, 16 / 25 * 100)

        # Morbidity

        assert_dict(self, data["morbidity_communicable"][0], "Watery Diarrhoea", 6, 100)
        assert_dict(self, data["morbidity_non_communicable"][0], "Hypertension", 6, 100)
        assert_dict(self, data["mental_health"][0], "Psychotic disorder (including mania)", 7, 70)
        assert_dict(self, data["mental_health"][1], "Alcohol or other substance use disorder", 3, 30)
        assert_dict(self, data["injury"][0], "Other", 3, 100)

    def test_refugee_detail(self):
        """ Test refugee public health report"""
        db_util.insert_codes(self.db.session)
        db_util.insert_locations(self.db.session)
        db_util.insert_cases(self.db.session, "refugee_data")
        end_date = datetime(2015, 12, 31).isoformat()
        start_date = datetime(2015, 1, 1).isoformat()
        rv = self.app.get('/reports/refugee_detail/1/{}/{}'.format(end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))["data"]

        self.assertEqual(data["total_population"],
                         2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11 + 12 + 12)
        self.assertEqual(data["clinic_num"], 2)
        self.assertEqual(data["n_clinicians"], 6)

        pop = {"0-1": {"male": 3, "female": 4},
               "1-4": {"male": 5, "female": 6},
               "5-14": {"male": 7, "female": 8},
               "15-44": {"male": 9, "female": 1},
               "45-64": {"male": 10, "female": 11},
               ">65": {"male": 12, "female": 13},
               "total": 89
               }
        self.assertEqual(data["population"]["Refugee Population"], pop)



        # Morbidity
        assert_dict(self, data["mortality"][0],
                    "Crude Mortality Rate",
                     14 / 89 * 1000,
                    None)
        assert_dict(self, data["mortality"][1],
                    "Under five crude mortality rate",
                    6 / 18 * 1000,
                    None)

        zero_pop = {
            "0-1": {"male": 0, "female": 0},
            "1-4": {"male": 0, "female": 0},
            "5-14": {"male": 0, "female": 0},
            "15-44": {"male": 0, "female": 0},
            "45-64": {"male": 0, "female": 0},
            ">65": {"male": 0, "female": 0},
            "total": 0
            
        }

        for key in data["mortality_breakdown"]["diseases"]:
            if key == "Lower Respiratory Tract Infection":
                self.assertEqual(data["mortality_breakdown"]["diseases"][key],
                                 {
                                     "0-1": {"male": 0, "female": 0},
                                     "1-4": {"male": 3, "female": 3},
                                     "5-14": {"male": 0, "female": 0},
                                     "15-44": {"male": 0, "female": 0},
                                     "45-64": {"male": 0, "female": 0},
                                     ">65": {"male": 0, "female": 0},
                                     "total": 6
                                 })
                
            elif key == "Tuberculosis":
                self.assertEqual(data["mortality_breakdown"]["diseases"][key],
                                 {
                                     "0-1": {"male": 0, "female": 0},
                                     "1-4": {"male": 0, "female": 0},
                                     "5-14": {"male": 0, "female": 0},
                                     "15-44": {"male": 0, "female": 3},
                                     "45-64": {"male": 5, "female": 0},
                                     ">65": {"male": 0, "female": 0},
                                     "total": 8
                                 })
            else:
                self.assertEqual(data["mortality_breakdown"]["diseases"][key], zero_pop)
        self.assertEqual(data["mortality_breakdown"]["age_gender"],
                         {
                             "0-1": {"male": 0, "female": 0},
                             "1-4": {"male": 3, "female": 3},
                             "5-14": {"male": 0, "female": 0},
                             "15-44": {"male": 0, "female": 3},
                             "45-64": {"male": 5, "female": 0},
                             ">65": {"male": 0, "female": 0}
                         })
        self.assertEqual(data["mortality_breakdown"]["age"],
                         {
                             "0-1": 0,
                             "1-4": 6,
                             "5-14": 0,
                             "15-44": 3,
                             "45-64": 5, 
                             ">65": 0
                             })

        # 3 Morbidity
        assert_dict(self, data["staffing"][0],
                    "Total Consultations",
                     170,
                    None)
        assert_dict(self, data["staffing"][1],
                    "Number of Clinicians",
                    6,
                    None)
        assert_dict(self, data["staffing"][2],
                    "Health Utilisation Rate",
                    170 / 89 / 364 * 365,
                    None)
        assert_dict(self, data["staffing"][3],
                    "Number of consultations per clinician per day",
                    170 / 6 / 364,
                    None)

        
        for key in data["communicable_diseases"]["diseases"]:
            if key == "Watery Diarrhoea":
                self.assertEqual(data["communicable_diseases"]["diseases"][key],
                                 {
                                     "0-1": {"male": 0, "female": 0},
                                     "1-4": {"male": 0, "female": 0},
                                     "5-14": {"male": 0, "female": 0},
                                     "15-44": {"male": 3, "female": 3},
                                     "45-64": {"male": 0, "female": 0},
                                     ">65": {"male": 0, "female": 0},
                                     "total": 6
                                 })

            else:
                self.assertEqual(data["communicable_diseases"]["diseases"][key], zero_pop)
        self.assertEqual(data["communicable_diseases"]["age_gender"],
                         {
                             "0-1": {"male": 0, "female": 0},
                             "1-4": {"male": 0, "female": 0},
                             "5-14": {"male": 0, "female": 0},
                             "15-44": {"male": 3, "female": 3},
                             "45-64": {"male": 0, "female": 0},
                             ">65": {"male": 0, "female": 0}
                         })
        self.assertEqual(data["communicable_diseases"]["age"],
                         {
                             "0-1": 0,
                             "1-4": 0,
                             "5-14": 0,
                             "15-44": 6,
                             "45-64": 0, 
                             ">65": 0
                             })

        for key in data["non_communicable_diseases"]["diseases"]:
            if key == "Hypertension":
                self.assertEqual(data["non_communicable_diseases"]["diseases"][key],
                                 {
                                     "0-1": {"male": 0, "female": 0},
                                     "1-4": {"male": 3, "female": 3},
                                     "5-14": {"male": 0, "female": 0},
                                     "15-44": {"male": 0, "female": 0},
                                     "45-64": {"male": 0, "female": 0},
                                     ">65": {"male": 0, "female": 0},
                                     "total": 6
                                 })
            else:
                self.assertEqual(data["non_communicable_diseases"]["diseases"][key], zero_pop)

        self.assertEqual(data["non_communicable_diseases"]["age_gender"],
                         {
                             "0-1": {"male": 0, "female": 0},
                             "1-4": {"male": 3, "female": 3},
                             "5-14": {"male": 0, "female": 0},
                             "15-44": {"male": 0, "female": 0},
                             "45-64": {"male": 0, "female": 0},
                             ">65": {"male": 0, "female": 0}
                         })
        self.assertEqual(data["non_communicable_diseases"]["age"],
                         {
                             "0-1": 0,
                             "1-4": 6,
                             "5-14": 0,
                             "15-44": 0,
                             "45-64": 0, 
                             ">65": 0
                             })
        print(data["mental_health"])
        for key in data["mental_health"]["diseases"]:
            if key == "Alcohol or other substance use disorder":
                self.assertEqual(data["mental_health"]["diseases"][key],
                                 {
                                     "0-1": {"male": 0, "female": 0},
                                     "1-4": {"male": 0, "female": 0},
                                     "5-14": {"male": 0, "female": 0},
                                     "15-44": {"male": 0, "female": 0},
                                     "45-64": {"male": 0, "female": 0},
                                     ">65": {"male": 0, "female": 3},
                                     "total": 3
                                 })
            elif key == "Psychotic disorder (including mania)":
                self.assertEqual(data["mental_health"]["diseases"][key],
                                 {
                                     "0-1": {"male": 0, "female": 7},
                                     "1-4": {"male": 0, "female": 0},
                                     "5-14": {"male": 0, "female": 0},
                                     "15-44": {"male": 0, "female": 0},
                                     "45-64": {"male": 0, "female": 0},
                                     ">65": {"male": 0, "female": 0},
                                     "total": 7
                                 })
            else:
                self.assertEqual(data["mental_health"]["diseases"][key], zero_pop)

        self.assertEqual(data["mental_health"]["age_gender"],
                         {
                             "0-1": {"male": 0, "female": 7},
                             "1-4": {"male": 0, "female": 0},
                             "5-14": {"male": 0, "female": 0},
                             "15-44": {"male": 0, "female": 0},
                             "45-64": {"male": 0, "female": 0},
                             ">65": {"male": 0, "female": 3}
                         })
        self.assertEqual(data["mental_health"]["age"],
                         {
                             "0-1": 7,
                             "1-4": 0,
                             "5-14": 0,
                             "15-44": 0,
                             "45-64": 0, 
                             ">65": 3
                             })

        for key in data["injury"]["diseases"]:
            if key == "Other":
                self.assertEqual(data["injury"]["diseases"][key],
                                 {
                                     "0-1": {"male": 3, "female": 0},
                                     "1-4": {"male": 0, "female": 0},
                                     "5-14": {"male": 0, "female": 0},
                                     "15-44": {"male": 0, "female": 0},
                                     "45-64": {"male": 0, "female": 0},
                                     ">65": {"male": 0, "female": 0},
                                     "total": 3
                                 })
            else:
                self.assertEqual(data["injury"]["diseases"][key], zero_pop)
        self.assertEqual(data["injury"]["age_gender"],
                         {
                             "0-1": {"male": 3, "female": 0},
                             "1-4": {"male": 0, "female": 0},
                             "5-14": {"male": 0, "female": 0},
                             "15-44": {"male": 0, "female": 0},
                             "45-64": {"male": 0, "female": 0},
                             ">65": {"male": 0, "female": 0}
                         })
        self.assertEqual(data["injury"]["age"],
                         {
                             "0-1": 3,
                             "1-4": 0,
                             "5-14": 0,
                             "15-44": 0,
                             "45-64": 0, 
                             ">65": 0
                             })
        # Referral

        assert_dict(self, data["referrals"][0],
                    "Hospital Referrals",
                     3,
                    None)
        assert_dict(self, data["referrals"][1],
                    "Other Referrals",
                    6,
                    None)
        assert_dict(self, data["referrals"][2],
                    "Hospitalisation rate",
                    3 / 170 ,
                    None)
        assert_dict(self, data["referrals"][3],
                    "Referral rate",
                    9 / 170,
                    None)


    def test_refugee_cd(self):
        """ Test refugee cd report"""
        db_util.insert_codes(self.db.session)
        db_util.insert_locations(self.db.session)
        db_util.insert_cases(self.db.session, "refugee_data")
        end_date = datetime(2015, 12, 31).isoformat()
        start_date = datetime(2015, 1, 1).isoformat()
        rv = self.app.get('/reports/refugee_cd/1/{}/{}'.format(end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))["data"]

        zeroes = [0 for i in range(53)]

        wd = zeroes.copy()

        wd[0] = 2
        wd[14] = 2
        wd[16] = 2
        for key in data["communicable_diseases"]:
            self.assertEqual(data["communicable_diseases"][key]["weeks"],
                             ['Week 1, 2015', 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53])

            if key == "Watery Diarrhoea":
                self.assertEqual(data["communicable_diseases"][key]["suspected"], wd)
            else:
                self.assertEqual(data["communicable_diseases"][key]["suspected"], zeroes)

    def test_epi_monitoring(self):
        """ Test epi monitoring report"""

        #Load the test data.
        db_util.insert_locations(self.db.session)
        db_util.insert_codes_from_file(self.db.session, "codes.csv")
        db_util.insert_cases(self.db.session, "epi_monitoring")
        db_util.insert_alerts(self.db.session, "epi_monitoring")
        db_util.insert_links(self.db.session, "epi_monitoring")

        #Select report params
        end_date = datetime(2015, 1, 7).isoformat()
        start_date = datetime(2015, 1, 1).isoformat()
        location = 1

        #Call the api method and check the response is 200 OK. Store the data. 
        rv = self.app.get('/reports/epi_monitoring/{}/{}/{}'.format(location, end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))

        #Refactorisation: check the data is returned is as expected
        def check_data( data, expected ): 
            
            test_dict = {
                **data["epi_monitoring"],
                **data["deaths"],
                **data["mat_mortality"],
                **data["tot_mortality"]
            }

            for key, value in test_dict.items(): 

                if( value != expected ):
                    print( "FAILED ASSERTION | Key: {}  Value: {} Should be {}."
                           .format( key, value, expected ) )
                self.assertEqual(value, expected)

                if( key not in data["variables"] ):
                    print( "KEY NOT INCLUDED IN VARIABLES | Key: {}".format(key) )
                self.assertTrue( key in data["variables"] )

            self.assertEqual(data["alerts"]["total"], expected)
            self.assertEqual(data["alerts"]["investigated"], expected)

        #The data is set up to equal 2 everywhere, so check this is the case.
        check_data( data, 2 )

        #Change the dates and check we get what's expected.
        end_date = datetime(2016, 1, 7).isoformat()
        start_date = datetime(2016, 1, 1).isoformat()
        location = 1
 
        rv = self.app.get('/reports/epi_monitoring/{}/{}/{}'.format(location, end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))

        check_data( data, 0 )

        #Change the location and check we get whats expected.
        end_date = datetime(2015, 1, 7).isoformat()
        start_date = datetime(2015, 1, 1).isoformat()
        location = 11
 
        rv = self.app.get('/reports/epi_monitoring/{}/{}/{}'.format(location, end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))

        check_data( data, 1 )

    def test_malaria(self):
        """ Test malaria report"""

        #Load the test data.
        db_util.insert_locations(self.db.session)
        db_util.insert_codes_from_file(self.db.session, "codes.csv")
        db_util.insert_cases(self.db.session, "malaria")

        #Select report params
        end_date = datetime(2015, 1, 7).isoformat()
        start_date = datetime(2015, 1, 1).isoformat()
        location = 1

        #Call the api method and check the response is 200 OK. Store the data. 
        rv = self.app.get('/reports/malaria/{}/{}/{}'.format(location, end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))

        #Refactorisation: check the data is returned is as expected
        def check_data( data, expected ): 
            
            test_dict = {
                **data["malaria_prevention"],
                **data["malaria_situation"]
            }

            for key, value in test_dict.items(): 

                if( value != expected ):
                    print( "FAILED ASSERTION | Key: {}  Value: {} Should be {}."
                           .format( key, value, expected ) )
                self.assertEqual(value, expected)

                if( key not in data["variables"] ):
                    print( "KEY NOT INCLUDED IN VARIABLES | Key: {}".format(key) )
                self.assertTrue( key in data["variables"] )

        #The data is set up to equal 2 everywhere, so check this is the case.
        check_data( data, 2 )

        #Change the dates and check we get what's expected.
        end_date = datetime(2016, 1, 7).isoformat()
        start_date = datetime(2016, 1, 1).isoformat()
        location = 1
 
        rv = self.app.get('/reports/malaria/{}/{}/{}'.format(location, end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))

        check_data( data, 0 )

        #Change the location and check we get whats expected.
        end_date = datetime(2015, 1, 7).isoformat()
        start_date = datetime(2015, 1, 1).isoformat()
        location = 11
 
        rv = self.app.get('/reports/malaria/{}/{}/{}'.format(location, end_date, start_date))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))

        check_data( data, 1 )     

if __name__ == '__main__':
    unittest.main()
