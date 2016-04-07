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

    def test_index(self):
        tester = app.test_client(self)
        response = tester.get('/')
        self.assertEqual(response.status_code, 200)

    def test_tags(self):
        tester = app.test_client(self)
        response = tester.get('/tags')
        self.assertEqual(response.status_code, 200)



if __name__ == '__main__':
    unittest.main()
