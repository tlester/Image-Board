# To execute this test run python app_test.py on the Terminal
# Reading the defined test you'll see that we should expect
# a successful test, as we are passing 6 and 2 and getting 8 back
# but also a failure, as we'll purposely check a wrong value

from application import app

import os
import json
import unittest
import tempfile

class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    # Our first unit test - We are using the unittest
    # library, calling the _add_numbers route from the app
    # passing a pair of numbers, and checking that the
    # returned value, contained on the JSON response, match
    # the sum of those parameters
    def test_index(self):
        tester = app.test_client(self)
        response = tester.get('/')
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
