"""
Unittests for meerkat_api.util
"""
import unittest
from datetime import datetime
from meerkat_api import util, db
from meerkat_api.util import data_query
from meerkat_abacus import model
from meerkat_api.test import db_util


class DataQueryTests(unittest.TestCase):
    
    def setUp(self):
        """Setup for testing"""
        db_util.insert_codes(db.session)
        db_util.insert_locations(db.session)
        db_util.insert_cases(db.session, "public_health_report")
        
    def test_query_sum(self):
        """ Test basic query_sum functionality"""
        start_date = datetime(2015, 1, 1)
        end_date = datetime(2016, 1, 1)
        
        result = data_query.query_sum(db, ["tot_1"], start_date, end_date, 1)
        self.assertEqual(result["total"], 10)
        result = data_query.query_sum(db, ["tot_1"], start_date, end_date, 1)
        self.assertEqual(result["total"], 10)
        result = data_query.query_sum(db, ["gen_1", "age_1"],
                                        start_date, end_date, 1)
        self.assertEqual(result["total"], 2)
        result = data_query.query_sum(db, ["gen_1", "gen_2"],
                                        start_date, end_date, 1)
        self.assertEqual(result["total"], 0)

    def test_query_sum_by_level(self):
        """ Test query_data by level"""
        start_date = datetime(2015, 1, 1)
        end_date = datetime(2016, 1, 1)
        
        result = data_query.query_sum(db, ["tot_1"], start_date,
                                        end_date, 1, level="region")
        self.assertEqual(result["total"], 10)
        self.assertIn("region", result.keys())

        self.assertEqual(result["region"][2], 6)
        self.assertEqual(result["region"][3], 4)
        result = data_query.query_sum(db, ["nat_1", "tot_1"], start_date,
                                        end_date, 1, level="district")
        self.assertEqual(result["total"], 7)
        self.assertIn("district", result.keys())
        self.assertEqual(result["district"][6], 7)
        result = data_query.query_sum(db, ["gen_1", "age_1"],
                                        start_date, end_date, 1,
                                        level="clinic")
        self.assertEqual(result["total"], 2)
        self.assertIn("clinic", result.keys())
        self.assertEqual(result["clinic"][7], 2)

    def test_query_sum_location(self):
        """ Test that the location restriction works"""
        start_date = datetime(2015, 1, 1)
        end_date = datetime(2016, 1, 1)
        
        result = data_query.query_sum(db, ["tot_1"], start_date,
                                        end_date, 2)
        self.assertEqual(result["total"], 6)
        result = data_query.query_sum(db, ["tot_1"], start_date,
                                        end_date, 3)
        self.assertEqual(result["total"], 4)
        result = data_query.query_sum(db, ["tot_1"], start_date,
                                        end_date, 3, level="district")
        self.assertEqual(result["total"], 4)
        self.assertIn("district", result.keys())
        self.assertEqual(result["district"][6], 3)
        self.assertEqual(result["district"][5], 1)

    def test_query_sum_weeks(self):
        """ Test that the week breakdown works"""
        start_date = datetime(2015, 1, 1)
        end_date = datetime(2016, 1, 1)
        
        result = data_query.query_sum(db, ["tot_1"], start_date,
                                        end_date, 1, weeks=True)

        self.assertEqual(result["total"], 10)
        self.assertIn("weeks", result)
        self.assertEqual(result["weeks"], {18: 9, 22: 1})

        result = data_query.query_sum(db, ["gen_1", "age_1"], start_date,
                                        end_date, 1, weeks=True)

        self.assertEqual(result["total"], 2)
        self.assertIn("weeks", result)
        self.assertEqual(result["weeks"], {18: 2})
        result = data_query.query_sum(db, ["tot_1"], start_date,
                                        end_date, 1, weeks=True, level="region")

        self.assertEqual(result["total"], 10)
        self.assertIn("weeks", result)
        self.assertEqual(result["weeks"], {18: 9, 22: 1})
        self.assertEqual(result["region"][2]["weeks"][18], 6)
        self.assertEqual(result["region"][2]["total"], 6)
        self.assertEqual(result["region"][3]["weeks"][18], 3)
        self.assertEqual(result["region"][3]["weeks"][22], 1)
        self.assertEqual(result["region"][3]["total"], 4)
