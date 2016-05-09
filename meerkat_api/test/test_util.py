"""
Unittests for meerkat_api.util
"""
import unittest
from datetime import datetime

from meerkat_api import util
from meerkat_abacus import model


class UtilTests(unittest.TestCase):

    def test_is_child(self):
        """Testing is_child"""
        locations = {
            1: model.Locations(name="Demo"),
            2: model.Locations(name="Region 1",
                               parent_location=1),
            3: model.Locations(name="Region 2",
                               parent_location=1),
            4: model.Locations(name="District 1",
                               parent_location=2),
            5: model.Locations(name="District 2",
                               parent_location=3),
            6: model.Locations(name="Clinic 1",
                               parent_location=4),
            7: model.Locations(name="Clinic 2",
                               parent_location=5)
        }
        self.assertTrue(util.is_child(1, 3, locations))
        self.assertTrue(util.is_child(2, 4, locations))
        self.assertTrue(util.is_child(1, 7, locations))
        self.assertTrue(util.is_child(3, 7, locations))
        self.assertTrue(util.is_child("3", "7", locations))
        self.assertFalse(util.is_child(3, 6, locations))
        self.assertFalse(util.is_child(2, 5, locations))

    def test_get_children(self):
        """Test get_children"""
        locations = {
            1: model.Locations(name="Demo"),
            2: model.Locations(name="Region 1",
                               parent_location=1),
            3: model.Locations(name="Region 2",
                               parent_location=1),
            4: model.Locations(name="District 1",
                               parent_location=2),
            5: model.Locations(name="District 2",
                               parent_location=3),
            6: model.Locations(name="Clinic 1",
                               parent_location=4,
                               case_report=1),
            7: model.Locations(name="Clinic 2",
                               parent_location=5,
                               case_report=1),
            8: model.Locations(name="Region With No Clinics",
                               parent_location=1)
        }
        children = util.get_children(1, locations)
        self.assertEqual(children, [6, 7])
        children = util.get_children(2, locations)
        self.assertEqual(children, [6])
        children = util.get_children(6, locations)
        self.assertEqual(children, [6])
        children = util.get_children(8, locations)
        self.assertEqual(children, [])

    def test_row_to_dict(self):
        """ Test row_to_dict """

        row_1 = model.Locations(name="Test",
                              parent_location=2,
                              case_report=1)

        result_dict = util.row_to_dict(row_1)
        self.assertEqual(result_dict["name"], "Test")
        self.assertEqual(result_dict["parent_location"], 2)
        self.assertEqual(result_dict["case_report"], 1)
        row_2 = model.Data(uuid="test-uuid",
                         date=datetime(2016, 1, 1),
                         variables={"tot_1": 4}
                         )
        result_dict = util.row_to_dict(row_2)
        self.assertEqual(result_dict["uuid"], "test-uuid")
        self.assertEqual(result_dict["date"], datetime(2016, 1, 1))
        self.assertEqual(result_dict["variables"], {"tot_1": 4})

        # Test with a tuple of rows
        result_dict = util.row_to_dict((row_1, row_2))

        self.assertIn("data", result_dict)
        self.assertIn("locations", result_dict)
        self.assertEqual(result_dict["data"]["variables"], {"tot_1": 4})
        self.assertEqual(result_dict["locations"]["name"], "Test")

    def test_rows_to_dicts(self):
        rows1 = []
        for i in range(50):
            rows1.append(model.AggregationVariables(
                id="tot_" + str(i),
                name="Test " + str(i)
            ))
        result_dicts = util.rows_to_dicts(rows1)
        for i in range(50):
            self.assertEqual(result_dicts[i]["id"], "tot_" + str(i))
            self.assertEqual(result_dicts[i]["name"], "Test " + str(i))

        # With id
        result_dicts = util.rows_to_dicts(rows1, dict_id="id")
        for i in range(50):
            self.assertEqual(result_dicts["tot_" + str(i)]["id"],
                             "tot_" + str(i))
        # With tuple of tables
        combined_rows = []
        for i in range(50):
            combined_rows.append(
                (
                    rows1[i],
                    model.Locations(name="Location " + str(i),
                                    id=str(i))
                )
            )
        result_dicts = util.rows_to_dicts(combined_rows)
        for i in range(50):
            self.assertIn("locations", result_dicts[i])
            self.assertIn("aggregation_variables", result_dicts[i])
            self.assertEqual(result_dicts[i]["aggregation_variables"]["id"],
                             "tot_" + str(i))
            self.assertEqual(result_dicts[i]["locations"]["name"],
                             "Location " + str(i))
        with self.assertRaises(TypeError):
            result_dicts = util.rows_to_dicts(combined_rows, dict_id="id")
