#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the Meerkat frontend
"""
import meerkat_api
import unittest


class MeerkatFrontendTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        self.app = meerkat_api.app.test_client()

    def tearDown(self):
        pass

    def test_index(self):
        """Check the index page loads"""
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'WHO', rv.data)


if __name__ == '__main__':
    unittest.main()
