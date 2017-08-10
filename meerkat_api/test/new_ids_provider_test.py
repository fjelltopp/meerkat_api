"""
DHIS2 import/export Tests

Unit tests for the new dhis2 ids provider
"""
from unittest import TestCase
from unittest.mock import patch

from api_background.dhis2_export import NewIdsProvider


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
