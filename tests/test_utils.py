from app.extensions import db

from app.utils import email_is_student, get_user_navigation
from tests.loader import Loader
from tests.utils import TestBase


class TestUtils(TestBase):
    def setUp(self):
        self.app = self.create()

        # Set up the application context manually to build the database
        # and test client for requests.
        ctx = self.app.app_context()
        ctx.push()

        self.client = self.app.test_client()

        fixtures = ["roles.json", "users.json"]

        # Now that we're in context, we can load the database.
        loader = Loader(self.app, db, fixtures)
        loader.load()

    def tearDown(self):
        db.drop_all()
        db.session.close()

    # Anonymous users don't get extra nav items
    def test_get_user_navigation(self):

        with self.app.test_request_context():
            nav = get_user_navigation()
            self.assertEqual(len(nav), 0)

    def test_email_is_not_student(self):
        email = "staff@example.com"
        is_student = email_is_student(email)

        self.assertFalse(is_student)

    def test_email_is_student(self):
        email = "astudent123456@example.com"
        is_student = email_is_student(email)

        self.assertTrue(is_student)
