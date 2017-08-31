import json
from importlib import reload
from unittest import TestCase
from unittest.mock import patch, MagicMock

from api_background import dhis2_export

import api_background
from api_background.dhis2_export import put, delete, get, post, NewIdsProvider, get_form_keys_to_data_elements_dict, \
    get_dhis2_organisations_codes_to_ids


class Dhis2RequestsWrapperTestCase(TestCase):
    """
    Unit tests for the requests wrapper
    """

    def setUp(self):
        self.kwargs = {"they": "shall", "pass": "ok"}
        self.fake_url = "http://foo"
        self.bar = "bar"
        self.baz = "baz"

    @patch('requests.put')
    def test_put(self, requests_mock):
        self.__mock_ok_response(requests_mock)
        put(self.fake_url, data=self.bar, json=self.baz, **self.kwargs)
        requests_mock.assert_called_once_with(self.fake_url, data=self.bar, json=self.baz, **self.kwargs)

    @patch('requests.post')
    def test_post(self, requests_mock):
        self.__mock_ok_response(requests_mock)
        post(self.fake_url, data=self.bar, json=self.baz, **self.kwargs)
        requests_mock.assert_called_once_with(self.fake_url, data=self.bar, json=self.baz, **self.kwargs)

    @patch('requests.get')
    def test_get(self, requests_mock):
        self.__mock_ok_response(requests_mock)
        get(self.fake_url, params=self.bar, **self.kwargs)
        requests_mock.assert_called_once_with(self.fake_url, params=self.bar, **self.kwargs)

    @patch('requests.delete')
    def test_delete(self, requests_mock):
        self.__mock_ok_response(requests_mock)
        delete(self.fake_url, **self.kwargs)
        requests_mock.assert_called_once_with(self.fake_url, **self.kwargs)

    @patch('requests.Response')
    @patch('requests.get')
    def test_should_report_error_when_error_response(self, requests_mock, response_mock):
        response_mock.status_code = 999
        response_mock.json.return_value = {"message": "Error 999"}
        requests_mock.return_value = response_mock
        with self.assertLogs('meerkat_api.dhis2', level='ERROR') as cm:
            get(self.fake_url)
            self.assertEqual(cm.output[0], 'ERROR:meerkat_api.dhis2:Request failed with code 999.')
            self.assertTrue("Error 999" in cm.output[1])

    def __mock_ok_response(self, requests_mock):
        response = MagicMock('requests.Response')
        response.status_code = 200
        requests_mock.return_value = response


class NewIdsProviderTestCase(TestCase):
    """
    Unit test for dhis2 uids provider.
    """

    def setUp(self):
        self.first_batch = {
            "codes": ["a", "b"]
        }
        self.second_batch = {
            "codes": ["c", "d"]
        }
        self.not_used_batch = {
            "codes": ["nope", "nah"]
        }

        response_patch = patch('requests.Response')
        get_patch = patch('requests.get')
        self.addCleanup(response_patch.stop)
        self.addCleanup(get_patch.stop)

        self.response_mock = response_patch.start()
        self.get_mock = get_patch.start()

        self.response_mock.json.side_effect = [self.first_batch, self.second_batch]
        self.response_mock.status_code = 200
        self.get_mock.return_value = self.response_mock

    def tearDown(self):
        self.response_mock.stop()
        self.get_mock.stop()

    def test_pop_should_lazy_initialize(self):
        obj_under_test = NewIdsProvider("http://fake/url/api", ('John', 'random_string'))
        self.assertFalse(self.get_mock.called)
        obj_under_test.pop()
        self.assertTrue(self.get_mock.called)

    def test_pop_should_buffer_ids_lazily(self):
        obj_under_test = NewIdsProvider("http://fake/url/api", ('John', 'random_string'))
        for i in range(3):
            obj_under_test.pop()
        self.assertEqual(self.get_mock.call_count, 2)

    def test_pop_should_return_correct_ids(self):
        obj_under_test = NewIdsProvider("http://fake/url/api", ('John', 'random_string'))
        self.__validate_return_codes(self.first_batch, obj_under_test)
        self.__validate_return_codes(self.second_batch, obj_under_test)

    def __validate_return_codes(self, batch_json, obj_under_test):
        for expected_id in reversed(batch_json["codes"]):
            actual_id = obj_under_test.pop()
            self.assertEqual(actual_id, expected_id)


class ProgramUpdateTestCase(TestCase):
    """
    Unit test for dhis2 program update
    """

    def setUp(self):
        self.form_config = {"name": "fake_form"}
        self.ORGANISATION_UNITS_KEY = 'organisationUnits'

    @patch('requests.put')
    @patch('requests.get')
    @patch('requests.Response')
    @patch('requests.Response')
    def test_with_program_id_and_with_already_assigned_organisations(self, get_res_mock, put_res_mock, get_mock,
                                                                     put_mock):
        expected_program_id = "existing_program_id"
        self.form_config['programId'] = expected_program_id
        existing = ["one", "two", "three"]
        get_res_mock.status_code = 200
        get_res_mock.json.return_value = {self.ORGANISATION_UNITS_KEY: self.ids_jarray(existing)}
        get_mock.return_value = get_res_mock
        put_res_mock.status_code = 200
        put_mock.return_value = put_res_mock
        new = ["four", "five"]

        # code under test
        returned_program_id = dhis2_export.update_program(self.form_config, new)

        # assertions
        self.assertEqual(expected_program_id, returned_program_id)
        put_mock.assert_called_once()
        called_url = put_mock.call_args[0][0]
        expected_path = '/programs/' + expected_program_id
        self.assertTrue(called_url.endswith(expected_path))

        actual_org_ids = put_mock.call_args[1]['data'][self.ORGANISATION_UNITS_KEY]
        expected_org_ids = self.ids_jarray(existing + new)
        self.assertEquals(actual_org_ids, expected_org_ids)

    @patch('requests.put')
    @patch('requests.get')
    @patch('requests.Response')
    @patch('requests.Response')
    def test_without_program_id_and_with_already_assigned_organisations(self, get_res_mock, put_res_mock, get_mock,
                                                                        put_mock):
        expected_program_id = "to_be_found_program_id"
        get_res_mock.json.return_value = {"programs": [{"id": expected_program_id}]}
        get_res_mock.status_code = 200
        get_mock.return_value = get_res_mock
        put_res_mock.status_code = 200
        put_mock.return_value = put_res_mock
        new = ["four", "five"]

        returned_program_id = dhis2_export.update_program(self.form_config, new)

        self.assertEqual(expected_program_id, returned_program_id)
        put_mock.assert_called_once()
        called_url = put_mock.call_args[0][0]
        expected_path = '/programs/' + expected_program_id
        self.assertTrue(called_url.endswith(expected_path))

    @patch('requests.post')
    @patch('requests.get')
    @patch('requests.Response')
    @patch('requests.Response')
    def test_create_a_new_program(self, post_res_mock, get_res_mock, get_mock, post_mock):
        get_res_mock.json.return_value = {"programs": []}
        get_res_mock.status_code = 200
        get_mock.return_value = get_res_mock

        post_res_mock.status_code = 200
        post_mock.return_value = post_res_mock

        ids_provder_mock = MagicMock()
        expected_program_id = 'generated_id_1'
        ids_provder_mock.pop.side_effect = [expected_program_id, "generated_id_2", "generated_id_3"]
        dhis2_export.ids = ids_provder_mock

        keys_to_dhis2_ids = {}
        for i in range(10):
            keys_to_dhis2_ids["col" + str(i)] = "dhis2_id" + str(i)
        dhis2_export.get_form_keys_to_data_elements_dict = MagicMock(return_value=keys_to_dhis2_ids)

        # code under test
        new = ["four", "five"]
        returned_program_id = dhis2_export.update_program(self.form_config, new)

        # assertions
        self.assertEqual(expected_program_id, returned_program_id)

        program_call_args = post_mock.call_args_list[0]
        called_url = program_call_args[0][0]
        expected_path = '/programs'
        self.assertTrue(called_url.endswith(expected_path))
        data_json = json.loads(program_call_args[1]['data'])
        send_program_id = data_json['id']
        self.assertEqual(expected_program_id, send_program_id)
        send_org_units = data_json['organisationUnits']
        expected_org_units = self.ids_jarray(new)
        self.assertEqual(expected_org_units, send_org_units)

        program_stages_call_args = post_mock.call_args_list[1]
        called_url = program_stages_call_args[0][0]
        expected_path = '/programStages'
        self.assertTrue(called_url.endswith(expected_path))
        expected_data_json = {
            "name": expected_program_id,
            "program": {"id": expected_program_id},
            "programStageDataElements": [{"dataElement": {"id": dhis2_id}} for dhis2_id in keys_to_dhis2_ids.values()]
        }
        actual_data_json = json.loads(program_stages_call_args[1]['data'])
        self.assertEqual(expected_data_json, actual_data_json)

    @staticmethod
    def ids_jarray(ids):
        return [{"id": id} for id in ids]


class GetFormKeysToDataElementsDictTest(TestCase):
    """ Unit test for event capture metadata creation """

    def setUp(self):
        self.keys = ["test_clinic", "test_region", "test_district"]
        self.dhis2_ids = ["FQ2o8UBlcrS", "M62VHgYT2n0", "uF1DLnZNlWe"]
        # clear module state (cached responses etc.)
        api_background.dhis2_export = reload(api_background.dhis2_export)

    @patch('requests.get')
    @patch('requests.Response', status_code=200)
    @patch('api_background.dhis2_export.__get_keys_from_db')
    def test_returns_valid_json(self, get_keys_mock, response_mock, get_mock):
        response_mock.json.return_value = {
            'dataElements': [{"id": item[0], "displayName": item[1]} for item in zip(self.dhis2_ids, self.keys)]
        }
        get_mock.return_value = response_mock
        get_keys_mock.return_value = self.keys

        actual_value = get_form_keys_to_data_elements_dict("fakeUrl", ('user', 'password'), {"headers": "some"},
                                                           "my_form")

        expected_value = dict(zip(self.keys, self.dhis2_ids))
        self.assertEqual(actual_value, expected_value)

    @patch('requests.get')
    @patch('requests.Response', status_code=200)
    @patch('api_background.dhis2_export.__get_keys_from_db')
    @patch('api_background.dhis2_export.__update_data_elements')
    def test_should_create_non_existing_keys(self, update_mock, get_keys_mock, response_mock, get_mock):
        response_mock.json.return_value = {
            'dataElements': [{"id": item[0], "displayName": item[1]} for item in zip(self.dhis2_ids, self.keys)]
        }
        get_mock.return_value = response_mock
        get_keys_mock.return_value = self.keys + ['not_present_key']
        update_mock.return_value = 'new_created_dhis2_id'

        actual_value = get_form_keys_to_data_elements_dict("fakeUrl", ('user', 'password'), {"headers": "some"},
                                                           "my_form")

        self.assertTrue('not_present_key' in update_mock.call_args[0])
        expected_value = dict(zip(self.keys + ['not_present_key'], self.dhis2_ids + ['new_created_dhis2_id']))
        self.assertEqual(actual_value, expected_value)

    @patch('requests.get')
    @patch('requests.Response', status_code=200)
    @patch('api_background.dhis2_export.__get_keys_from_db')
    def test_result_should_be_cached(self, get_keys_mock, response_mock, get_mock):
        response_mock.json.return_value = {
            'dataElements': [{"id": item[0], "displayName": item[1]} for item in zip(self.dhis2_ids, self.keys)]
        }
        get_mock.return_value = response_mock
        get_keys_mock.return_value = self.keys

        for i in range(3):
            get_form_keys_to_data_elements_dict("fakeUrl", ('user', 'password'), {"headers": "some"},
                                                "my_form")
            get_mock.assert_called_once()



class GetOrganisationsTest(TestCase):

    dhis2_org_ids = ["FQ2o8UBlcrS", "M62VHgYT2n0", "uF1DLnZNlWe"]
    dhis2_codes = ["code1", "code2", "code3"]

    def setUp(self):
        # clear module state (cached responses etc.)
        api_background.dhis2_export = reload(api_background.dhis2_export)

    def tearDown(self):
        pass

    def get_organisations_mock(*args, **kwargs):
        response_mock = MagicMock(status_code=200)
        ids = GetOrganisationsTest.dhis2_org_ids
        codes = GetOrganisationsTest.dhis2_codes
        url = args[0]
        if 'paging=False' in url:
            result = {"organisationUnits": [{"id": a_id} for a_id in ids]}
            response_mock.json.return_value = result
        else:
            # side effect fun to return propre responses for given dhis2 ids
            # e.g. get("http://localhost/organisationUnits/FQ2o8UBlcrS").json()
            # should return {"code": "code1"}
            def return_code(*_args, **_kwargs):
                dhis2_org_id = args[0].split('/')[-1]
                code = dict(zip(ids, codes))[dhis2_org_id]
                return {"code": code}

            response_mock.json.side_effect = return_code
        return response_mock

    @patch('requests.get', side_effect=get_organisations_mock)
    def test_should_return_valid_json(self, get_mock):
        actual_value = get_dhis2_organisations_codes_to_ids()
        expected_value = dict(zip(GetOrganisationsTest.dhis2_codes, GetOrganisationsTest.dhis2_org_ids))
        self.assertEqual(actual_value, expected_value)

    @patch('requests.get')
    @patch('requests.Response', status_code=200)
    def test_should_cache_result(self, response_mock, get_mock):
        # 1st call for http:localhost/organisationUnits
        # 2nd call for http:localhost/organisationUnits/id_foo
        response_mock.json.side_effect = [{'organisationUnits': [{"id": "id_foo"}]}, {"code": "code_bar"}]
        get_mock.return_value = response_mock

        get_dhis2_organisations_codes_to_ids()
        get_mock.assert_called()

        get_mock.reset_mock()
        get_dhis2_organisations_codes_to_ids()
        get_mock.assert_not_called()
