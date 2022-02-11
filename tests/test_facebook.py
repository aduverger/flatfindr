# pylint: disable-all

import io
import os
import unittest
import unittest.mock
import platform


from flatfindr.facebook import Facebook

""" Test the Facebook Class """

TEST_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    os.path.join("raw_data", "test_db.json"),
)


class TestLogIn(unittest.TestCase):
    @unittest.mock.patch("sys.stdout", new_callable=io.StringIO)
    def test_log_in(self, mock_stdout):
        fb = Facebook(headless=True, db_path=TEST_DB_PATH)
        if platform.system() == "Linux":
            # if test is ran from GitHub
            # TODO: better way to check
            fb.email = os.environ["FB_LOGIN"]
            fb.password = os.environ["FB_PWD"]
        fb.log_in()
        self.assertEqual(mock_stdout.getvalue(), "")
        fb.quit_driver()
