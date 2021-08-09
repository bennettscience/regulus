import json
import unittest

from app import app, db
from app.models import Course, Location, User


class TestUsers(unittest.TestCase):
    def setUp(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        db.create_all()
        self.client = app.test_client()

        l1 = Location(
            name="Location 1", description="High School", address="123 main st"
        )
        u1 = User(name="User 1", email="user1@example.com", location_id=1)
        c1 = Course(title="Course 1", location_id=1)
        db.session.add_all([c1, l1, u1])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_locations(self):
        resp = self.client.get("/locations")
        self.assertTrue(resp.status_code == 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(resp.json[0]["name"], "Location 1")

    def test_post_location(self):
        headers = {"Content-Type": "application/json"}
        payload = {
            "name": "Location 2",
            "description": "Another location",
            "address": "999 Oak St.",
        }
        resp = self.client.post("/locations", data=json.dumps(payload), headers=headers)
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "Location 2")

    def test_post_bad_location(self):
        headers = {"Content-Type": "application/json"}
        payload = {"description": "Another location", "address": "999 Oak St."}
        resp = self.client.post("/locations", data=json.dumps(payload), headers=headers)
        self.assertTrue(resp.status_code == 422)
        self.assertEqual(
            resp.json["messages"]["name"][0], "Missing data for required field."
        )

    def test_get_single_location(self):
        resp = self.client.get("/locations/1")
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "Location 1")

    def test_get_unknown_location(self):
        resp = self.client.get("/locations/2")
        self.assertEqual(resp.status_code, 404)

    def test_get_location_users(self):
        resp = self.client.get("/locations/1/users")
        self.assertTrue(resp.status_code == 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(resp.json[0]["name"], "User 1")

    def test_get_missing_location_useres(self):
        resp = self.client.get("/locations/10/users")
        self.assertTrue(resp.status_code == 404)

    def test_get_location_courses(self):
        resp = self.client.get("/locations/1/courses")
        self.assertTrue(resp.status_code == 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 1)
