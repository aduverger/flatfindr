# pylint: disable-all

import io
import unittest
import unittest.mock

from flatfindr.facebook import Facebook

""" Test the Facebook Class """


class TestLogIn(unittest.TestCase):
    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_log_in(self, mock_stdout):
        fb = Facebook(headless=False)
        fb.log_in()
        self.assertEqual(mock_stdout.getvalue(), "")
        fb.quit_driver()
