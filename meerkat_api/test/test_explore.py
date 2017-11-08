#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the explore resource of Meerkat API
"""
import json
import unittest
from datetime import datetime
import pytz
from . import settings
import meerkat_api
from meerkat_api.test import db_util
from meerkat_api.resources import explore

class MeerkatAPITestCase(meerkat_api.test.TestCase):

    def setUp(self):
        """Setup for testing"""
        self._mock_epi_week_abacus_logic()
        meerkat_api.app.config['TESTING'] = True
        meerkat_api.app.config['API_KEY'] = ""
        self.app = meerkat_api.app.test_client()
        session = db_util.session
        db_util.insert_codes(session)
        db_util.insert_locations(session)
        db_util.insert_cases(session, "public_health_report")

    def tearDown(self):
        pass

    def test_sort_dates(self):
        """Test sort dates"""

        start_date = datetime(2015, 4, 3)
        end_date = datetime(2013, 4, 5)
        new_dates = explore.fix_dates(start_date.isoformat(),
                                      end_date.isoformat())
        self.assertEqual(new_dates[0], start_date)
        self.assertEqual(new_dates[1], end_date)
        new_dates = explore.fix_dates(None, None)
        self.assertEqual(new_dates[0], datetime(datetime.now().year, 1, 1))
        self.assertLess((datetime.now() - new_dates[1]).seconds, 1)

        start_date_timezone = pytz.UTC.localize(start_date)
        end_date_timezone = pytz.UTC.localize(end_date)
        new_dates = explore.fix_dates(start_date_timezone.isoformat(),
                                      end_date_timezone.isoformat())
        self.assertEqual(new_dates[0], start_date)
        self.assertEqual(new_dates[1], end_date)


    def test_get_variables(self):
        """ Test get variables """
        variables = explore.get_variables("pc")
        self.assertEqual(sorted(list(variables.keys())),
                         sorted(["prc_1", "prc_2", "prc_3", "prc_4", "prc_6", "prc_7"]))

    def test_get_locations_by_level(self):
        """ Test getting locations by level """

        locs = explore.get_locations_by_level("region", 1)
        self.assertEqual(sorted(list(locs.keys())), [2, 3])
        locs = explore.get_locations_by_level("district", 2)
        self.assertEqual(sorted(list(locs.keys())), [4, 5])
        locs = explore.get_locations_by_level("district", 1)
        self.assertEqual(sorted(list(locs.keys())), [4, 5, 6])
        locs = explore.get_locations_by_level("clinic", 1)
        self.assertEqual(sorted(list(locs.keys())), [7, 8, 10, 11])
        locs = explore.get_locations_by_level("clinic", 3)
        self.assertEqual(sorted(list(locs.keys())), [11])

    def test_query_variable(self):
        date_start = datetime(2015, 1, 1)
        date_end = datetime(2015, 12, 31)
        rv = self.app.get(
            '/query_variable/tot_1/gender/{}/{}'.format(date_start.isoformat(),date_end.isoformat()),
            headers=settings.header
        )
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(data.keys()),
                         sorted(["Female", "Male"]))
        self.assertEqual(data["Female"]["total"], 7)
        self.assertEqual(data["Female"]["weeks"]["18"], 5)
        self.assertEqual(data["Female"]["weeks"]["22"], 1)
        self.assertEqual(data["Male"]["total"], 3)
        self.assertEqual(data["Male"]["weeks"]["18"], 3)
        rv = self.app.get(
            '/query_variable/tot_1/gender/{}/{}?use_ids=1'.format(date_start.isoformat(),date_end.isoformat()),
            headers=settings.header
        )
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(data.keys()),
                         sorted(["gen_2", "gen_1"]))
        self.assertEqual(data["gen_2"]["total"], 7)
        self.assertEqual(data["gen_2"]["weeks"]["18"], 5)
        self.assertEqual(data["gen_2"]["weeks"]["22"], 1)
        self.assertEqual(data["gen_1"]["total"], 3)
        self.assertEqual(data["gen_1"]["weeks"]["18"], 3)

        # Only Region 2
        rv = self.app.get(
            '/query_variable/tot_1/gender/{}/{}?only_loc=3'.format(date_start.isoformat(),date_end.isoformat()),
            headers=settings.header
        )
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(data.keys()),
                         sorted(["Female", "Male"]))
        self.assertEqual(data["Female"]["total"], 4)
        self.assertEqual(data["Female"]["weeks"]["18"], 3)
        self.assertEqual(data["Female"]["weeks"]["22"], 1)
        self.assertEqual(data["Male"]["total"], 0)
        self.assertEqual(data["Male"]["weeks"]["18"], 0)


        # Check Weeks
        self.assertEqual(sorted(data["Female"]["weeks"].keys()),
                         sorted([str(i) for i in range(1, 54)]))

        new_date_start = datetime(2014, 1, 1)
        rv = self.app.get(
            '/query_variable/tot_1/gender/{}/{}?only_loc=3'.format(new_date_start.isoformat(),date_end.isoformat()),
            headers=settings.header
        )
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(data["Female"]["weeks"].keys()),
                         sorted([str(i) for i in range(1, 107)]))


    def test_query_variable_location(self):
        """Test with variable = location"""
        date_start = datetime(2015, 1, 1)
        date_end = datetime(2015, 12, 31)
        rv = self.app.get(
            '/query_variable/location:3/gender/{}/{}'.format(date_start.isoformat(),date_end.isoformat()),
            headers=settings.header
        )
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(data.keys()),
                         sorted(["Female", "Male"]))
        self.assertEqual(data["Female"]["total"], 4)
        self.assertEqual(data["Female"]["weeks"]["18"], 3)
        self.assertEqual(data["Female"]["weeks"]["22"], 1)
        self.assertEqual(data["Male"]["total"], 0)
        print(data)
        self.assertEqual(data["Male"]["weeks"]["18"], 0)

    def test_query_variable_locations(self):
        """Test with group_by = locations"""
        date_start = datetime(2015, 1, 1)
        date_end = datetime(2015, 12, 31)
        rv = self.app.get(
            '/query_variable/gen_2/locations:region/{}/{}'.format(date_start.isoformat(),date_end.isoformat()),
            headers=settings.header
        )
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(data.keys()),
                         sorted(["Region 1", "Region 2"]))
        self.assertEqual(data["Region 1"]["total"], 3)
        self.assertEqual(data["Region 1"]["weeks"]["18"], 2)
        self.assertEqual(data["Region 2"]["total"], 4)
        self.assertEqual(data["Region 2"]["weeks"]["18"], 3)
        self.assertEqual(data["Region 2"]["weeks"]["22"], 1)

        rv = self.app.get(
            '/query_variable/gen_2/locations:clinic/{}/{}?only_loc=2'.format(
                date_start.isoformat(),
                date_end.isoformat()
            ),
            headers=settings.header
        )
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))

        self.assertEqual(sorted(data.keys()),
                         sorted(["Clinic 1", "Clinic 2", "Clinic 4"]))


    def test_query_category(self):
        """test query category """

        date_start = datetime(2015, 1, 1)
        date_end = datetime(2015, 12, 31)
        rv = self.app.get(
            '/query_category/gender/pc/{}/{}'.format(date_start.isoformat(),date_end.isoformat()),
            headers=settings.header
        )
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(data.keys()),
                         sorted(["Female", "Male"]))
        self.assertEqual(data["Female"]["Communicable disease"], 4)
        self.assertEqual(data["Female"]["Non-communicable disease"], 2)
        self.assertEqual(data["Female"]["Mental Health"], 1)
        self.assertEqual(data["Female"]["Injury"], 0)
        self.assertEqual(data["Male"]["Communicable disease"], 3)
        self.assertEqual(data["Male"]["Non-communicable disease"], 0)
        self.assertEqual(data["Male"]["Mental Health"], 0)

        # With only_loc
        rv = self.app.get(
            '/query_category/gender/pc/{}/{}?only_loc=3'.format(date_start.isoformat(),date_end.isoformat()),
            headers=settings.header
        )
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(data.keys()),
                         sorted(["Female", "Male"]))
        self.assertEqual(data["Female"]["Communicable disease"], 1)
        self.assertEqual(data["Female"]["Non-communicable disease"], 2)
        self.assertEqual(data["Female"]["Mental Health"], 1)
        self.assertEqual(data["Female"]["Injury"], 0)
        self.assertEqual(data["Male"]["Communicable disease"], 0)
        self.assertEqual(data["Male"]["Non-communicable disease"], 0)
        self.assertEqual(data["Male"]["Mental Health"], 0)
        date_start = datetime(2015, 1, 1)
        date_end = datetime(2015, 12, 31)

        # With use ids
        rv = self.app.get(
            '/query_category/gender/pc/{}/{}?use_ids=1'.format(date_start.isoformat(),date_end.isoformat()),
            headers=settings.header
        )
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(data.keys()),
                         sorted(["gen_2", "gen_1"]))
        self.assertEqual(data["gen_2"]["prc_1"], 4)
        self.assertEqual(data["gen_2"]["prc_2"], 2)
        self.assertEqual(data["gen_2"]["prc_3"], 1)
        self.assertEqual(data["gen_2"]["prc_4"], 0)
        self.assertEqual(data["gen_1"]["prc_1"], 3)
        self.assertEqual(data["gen_1"]["prc_2"], 0)
        self.assertEqual(data["gen_1"]["prc_3"], 0)


        # With use ids and locations
        rv = self.app.get(
            '/query_category/gender/locations:region/{}/{}?use_ids=1'.format(
                date_start.isoformat(),
                date_end.isoformat()
            ),
            headers=settings.header
        )
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(data.keys()),
                         sorted(["gen_2", "gen_1"]))
        self.assertEqual(data["gen_2"]["2"], 3)
        self.assertEqual(data["gen_2"]["3"], 4)
        self.assertEqual(data["gen_1"]["2"], 3)
        self.assertEqual(data["gen_1"]["3"], 0)
        rv = self.app.get(
            '/query_category/locations:region/gender/{}/{}?use_ids=1'.format(
                date_start.isoformat(),
                date_end.isoformat()
            ),
            headers=settings.header
        )
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(data.keys()),
                         sorted(["2", "3"]))
        self.assertEqual(data["2"]["gen_2"], 3)
        self.assertEqual(data["3"]["gen_2"], 4)
        self.assertEqual(data["2"]["gen_1"], 3)
        self.assertEqual(data["3"]["gen_1"], 0)
        rv = self.app.get(
            '/query_category/locations:clinic/gender/{}/{}?use_ids=1&only_loc=3'.format(
                date_start.isoformat(),
                date_end.isoformat()
            ),
            headers=settings.header
        )
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(sorted(data.keys()),
                         sorted(["11"]))
        self.assertEqual(data["11"]["gen_2"], 4)
        self.assertEqual(data["11"]["gen_1"], 0)
