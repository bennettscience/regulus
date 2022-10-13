import json
import os

from sqlalchemy import Table

from app import app, db
from app.models import Course, Log, Location, User, UserType

from tests.utils import TestBase, Loader


class TestLogging(TestBase):
    def setUp(self) -> None:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///"
        app.config["TESTING"] = True

        db.create_all()

        self.client = app.test_client()

        fixtures = [
            "courses.json",
            "course_types.json",
            "locations.json",
            "roles.json",
            "users.json",
        ]

        conn = db.engine.connect()
        metadata = db.metadata

        for filename in fixtures:
            filepath = os.path.join(app.config.get("FIXTURES_DIR"), filename)
            if os.path.exists(filepath):
                data = Loader.load(filepath)
                table = Table(data[0]["table"], metadata)
                conn.execute(table.insert(), data[0]["records"])
            else:
                raise IOError(
                    "Error loading '{0}'. File could not be found".format(filename)
                )

    def tearDown(self) -> None:
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
        headers = {"Content-Type": "application/json"}
        payload = {
            "name": "User 3",
            "location_id": 1,
            "usertype_id": 1,
            "email": "user3@example.com",
        }
        self.client.post("/users", data=json.dumps(payload), headers=headers)
        log = Log.query.get(1)
        log_json = json.loads(log.json_data)
        self.assertTrue(log.method == "POST")
        self.assertEqual(log_json["name"], "User 3")
