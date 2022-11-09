import json

from app.extensions import db
from app.models import Log

from tests.loader import Loader
from tests.utils import TestBase


class TestLogging(TestBase):
    def setUp(self):
        self.app = self.create()

        # Set up the application context manually to build the database
        # and test client for requests.
        ctx = self.app.app_context()
        ctx.push()

        self.client = self.app.test_client()

        fixtures = [
            "courses.json",
            "course_types.json",
            "locations.json",
            "roles.json",
            "users.json",
        ]

        # Now that we're in context, we can load the database.
        loader = Loader(self.app, db, fixtures)
        loader.load()

    def tearDown(self):
        db.drop_all()
        db.session.close()

    # Log is empty because it is an anonymous request.
    def test_anonymous_log(self):
        self.client.get("/courses")
        log = Log.query.all()
        self.assertEqual(len(log), int("0"))

    def test_authenticated_log(self):
        self.login("User")
        self.client.get("/users/1")
        log = Log.query.all()
        self.assertEqual(len(log), 1)

    # Simulate creating a new user
    def test_post_request(self):
        self.login("Admin")
        payload = {
            "name": "User 5",
            "location_id": 1,
            "usertype_id": 1,
            "email": "user3@example.com",
        }
        self.client.post("/users", data=payload)
        log = Log.query.get(1)
        log_json = json.loads(log.json_data)
        self.assertTrue(log.method == "POST")
        self.assertEqual(log_json["name"], "User 5")
