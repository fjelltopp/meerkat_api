from unittest import TestCase
from unittest.mock import patch

from api_background.dhis2_export import put, delete, get, post, NewIdsProvider


class TestDhis2RequestsWrapper(TestCase):
    """
    DHIS2 import/export Tests

    Unit tests for the requests wrapper
    """

    def setUp(self):
        self.kwargs = {"they": "shall", "pass": "ok"}
        self.fake_url = "http://foo"
        self.bar = "bar"
        self.baz = "baz"

    @patch('requests.put')
    def test_put(self, requests_mock):
        put(self.fake_url, data=self.bar, json=self.baz, **self.kwargs)
        requests_mock.assert_called_once_with(self.fake_url, data=self.bar, json=self.baz, **self.kwargs)

    @patch('requests.post')
    def test_put(self, requests_mock):
        post(self.fake_url, data=self.bar, json=self.baz, **self.kwargs)
        requests_mock.assert_called_once_with(self.fake_url, data=self.bar, json=self.baz, **self.kwargs)


    @patch('requests.get')
    def test_put(self, requests_mock):
        get(self.fake_url, params=self.bar, **self.kwargs)
        requests_mock.assert_called_once_with(self.fake_url, params=self.bar, **self.kwargs)


    @patch('requests.delete')
    def test_put(self, requests_mock):
        delete(self.fake_url, **self.kwargs)
        requests_mock.assert_called_once_with(self.fake_url, **self.kwargs)

    @patch('requests.Response')
    @patch('requests.get')
    def test_should_report_error_when_error_response(self, requests_mock, response_mock):
        response_mock.status_code = 999
        response_mock.json.return_value = {"message":"Error 999"}
        requests_mock.return_value = response_mock
        with self.assertLogs('meerkat_api.dhis2', level='ERROR') as cm:
            get(self.fake_url)
            self.assertEqual(cm.output[0], 'ERROR:meerkat_api.dhis2:Request failed with code 999.')
            self.assertTrue("Error 999" in cm.output[1])


class NewIdsProviderTest(TestCase):
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

