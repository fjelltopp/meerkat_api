import json

from werkzeug.exceptions import HTTPException

import meerkat_api
from meerkat_api.resources.devices import DeviceResourceBase
from meerkat_api.test import db_util, settings


class TestDeviceResourceBase(meerkat_api.test.TestCase):
    def setUp(self):
        self.object_under_test = DeviceResourceBase()

    def test_get_sql_alchemy_filters_handles_bad_filters(self):
        bad_format_filter = "not:three_args"
        with self.assertRaises(HTTPException) as http_error:
            self.object_under_test.get_sql_alchemy_filters([bad_format_filter])
        http_exception = http_error.exception
        self.assertEqual(http_exception.code, 404)
        self.assertEqual(http_exception.data['message'], "Incorrect filter: {}".format(bad_format_filter))

    def test_get_sql_alchemy_filters_handles_non_existing_parameters(self):
        bad_argument_filter = "invalidParam:eq:foobar"
        with self.assertRaises(AttributeError) as attribute_error:
            self.object_under_test.get_sql_alchemy_filters([bad_argument_filter])
        the_exception = attribute_error.exception
        actual_argument_name = bad_argument_filter.split(':')[0]
        expected_error_message = "type object 'Data' has no attribute '{}'".format(actual_argument_name)
        self.assertEqual(the_exception.args[0], expected_error_message)

    def test_get_sql_alchemy_filters_handles_non_existing_comparators(self):
        bad_comparator_filter = "id:what?!$%#:NVM"
        with self.assertRaises(NotImplementedError):
            self.object_under_test.get_sql_alchemy_filters([bad_comparator_filter])

    def test_get_sql_alchemy_filters_return_valid_object(self):
        filters = ["id:eq:1", "date:gt:2017-01-01"]
        actual_sql_alchemy_filters = self.object_under_test.get_sql_alchemy_filters(filters)
        _comparator_to_str = {
            "eq": "=",
            "gt": ">"
        }
        for _filter, _actual_sql_filter in zip(filters, actual_sql_alchemy_filters):
            expected_left, expected_comparator, expected_right = _filter.split(":")
            expected = {
                "left": 'data.' + expected_left,
                "comparator": _comparator_to_str[expected_comparator],
                "right": expected_right
            }
            actual = {
                "left": str(_actual_sql_filter.left),
                "comparator": str(_actual_sql_filter).split()[1],
                "right": _actual_sql_filter.right.effective_value
            }

            for key in expected.keys():
                self.assertEqual(expected[key], actual[key])

    def test_get_variable_count_for_device_id(self):
        db_util.insert_cases(self.db_session, "public_health_report")
        device_id = "1"
        variable_id = "gen_1"
        actual = DeviceResourceBase._get_variable_count_for_deivce_id(device_id, variable_id, [])
        expected = {'deviceId': device_id, 'variable': variable_id, 'submissionsCount': 3}
        self.assertEqual(expected, actual)

    def test_get_variable_count_for_deivce_id_should_return_zero_for_no_data(self):
        db_util.insert_cases(self.db_session, "public_health_report")
        device_id = "4"
        variable_id = "gen_1"
        actual = DeviceResourceBase._get_variable_count_for_deivce_id(device_id, variable_id, [])
        expected = {'deviceId': device_id, 'variable': variable_id, 'submissionsCount': 0}
        self.assertEqual(expected, actual)


class TestDeviceSubmissions(meerkat_api.test.TestCase):
    def setUp(self):
        db_util.insert_cases(self.db_session, "public_health_report")

    def test_existing_device_id_with_submissions(self):
        device_id = '1'
        variable_id = 'tot_1'
        expected_submissions = 4

        actual = self.__get_actual_api_response(device_id, variable_id)
        expected = self.__get_expected_dict_response(device_id, expected_submissions, variable_id)

        self.assertDictEqual(expected, actual)

    def test_existing_device_id_with_no_submissions(self):
        device_id = '1'
        variable_id = 'fake_var_id'
        expected_submissions = 0

        actual = self.__get_actual_api_response(device_id, variable_id)
        expected = self.__get_expected_dict_response(device_id, expected_submissions, variable_id)

        self.assertDictEqual(expected, actual)

    def test_non_existing_device_id(self):
        device_id = '99999000000000000000001'
        variable_id = 'tot_1'
        expected_submissions = 0

        actual = self.__get_actual_api_response(device_id, variable_id)
        expected = self.__get_expected_dict_response(device_id, expected_submissions, variable_id)

        self.assertDictEqual(expected, actual)

    def __get_expected_dict_response(self, device_id, expected_submissions, variable_id):
        expected = {'deviceId': device_id, 'variable': variable_id, 'submissionsCount': expected_submissions}
        return expected

    def __get_actual_api_response(self, device_id, variable_id):
        endpoint_under_test = '/device/{}/submissions/{}'.format(device_id, variable_id)
        rv = self.app.get(endpoint_under_test, headers=settings.header)
        self.assertEqual(rv.status_code, 200)
        actual = json.loads(rv.data.decode("utf-8"))
        return actual


class TestDeviceSubmissionsForLocation(meerkat_api.test.TestCase):
    def setUp(self):
        db_util.insert_cases(self.db_session, "public_health_report")
        db_util.insert_locations(self.db_session)

    def test_should_require_location_parameter(self):
        rv = self.app.get('/devices/submissions/tot_1', headers=settings.header)
        self.assertEqual(rv.status_code, 400)
        error_message = json.loads(rv.data.decode("utf-8")).get('message')
        self.assertIn("location", error_message)
        self.assertIn("Missing required parameter in the JSON", error_message['location'])

    def test_should_return_all_devices_from_single_clinic(self):
        rv = self.app.get('/devices/submissions/tot_1?location=7', headers=settings.header)
        response = json.loads(rv.data.decode("utf-8"))
        clinic_submissions = response['clinicSubmissions']

        self.assertEqual(len(clinic_submissions), 1)
        device_submissions = clinic_submissions[0]['deviceSubmissions']
        self.assertEqual(len(device_submissions), 2)

        actual_device_ids = [sub.get("deviceId") for sub in device_submissions]
        expected_device_ids = ["1", "6"]
        for expected_id, actual_id in zip(expected_device_ids, actual_device_ids):
            self.assertEqual(expected_id, actual_id)

    def test_should_return_all_clinics_within_parent(self):
        rv = self.app.get('/devices/submissions/tot_1?location=1', headers=settings.header)
        response = json.loads(rv.data.decode("utf-8"))
        clinic_submissions = response['clinicSubmissions']

        actual_clinic_ids = [sub.get("clinicId") for sub in clinic_submissions]
        expected_clinic_ids = [7, 8, 10, 11]
        expected_clinic_count = len(expected_clinic_ids)

        self.assertEqual(response['clinicCount'], expected_clinic_count)
        self.assertEqual(len(clinic_submissions), expected_clinic_count)
        for expected_id, actual_id in zip(expected_clinic_ids, actual_clinic_ids):
            self.assertEqual(expected_id, actual_id)
