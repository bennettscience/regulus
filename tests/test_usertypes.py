from app.extensions import db
from tests.loader import Loader
from tests.utils import TestBase


class TestUserType(TestBase):
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
        db.session.remove()
        db.drop_all()

    def test_as_unauthorized(self):
        resp = self.client.get("/usertypes")
        self.assertEqual(resp.status_code, 401)

    def test_get_user_type(self):
        self.login("Admin")
        resp = self.client.get("/usertypes")

        self.assertIsInstance(resp.json, list)
        self.assertTrue(len(resp.json), 2)
        self.assertEqual(resp.json[0]["name"], "SuperAdmin")

    def test_post_user_type(self):
        self.login("Admin")
        payload = {"name": "Generic", "description": "A generic type."}
        resp = self.client.post("/usertypes", data=payload)
        self.assertEqual(resp.json["description"], "A generic type.")
