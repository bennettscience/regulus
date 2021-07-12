import json
import unittest

from app import app, db
from app.models import Course, CourseUserAttended, Location, User, UserType


class TestUsers(unittest.TestCase):
    def setUp(self) -> None:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        db.create_all()
        self.client = app.test_client()

        c1 = Course(title="Course 1")
        u1 = User(name="User 1", location_id=1, usertype_id=1)
        u2 = User(name="User 2", location_id=2, usertype_id=2)
        l1 = Location(name="Building 1", address="123 Main")
        l2 = Location(name="Building 2", address="999 Oak")
        ut1 = UserType(name="Type1", description="The first user type")
        ut2 = UserType(name="Type2", description="The second user type")

        db.session.add_all([c1, u1, u2, l1, l2, ut1, ut2])
        c1.presenters.append(u2)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_users(self):
        resp = self.client.get("/users")
        self.assertTrue(resp.status_code == 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 2)

    def test_post_user(self):
        headers = {"Content-Type": "application/json"}
        payload = {
            "name": "User 3",
            "location_id": 1,
            "usertype_id": 1,
            "email": "something@email.com",
        }
        resp = self.client.post("/users", data=json.dumps(payload), headers=headers)
        self.assertTrue(resp.status_code == 200)
        self.assertTrue(resp.json["name"] == "User 3")

    def test_post_bad_user(self):
        headers = {"Content-Type": "application/json"}
        payload = {"name": "Bad user", "location_id": 1, "usertype_id": 1}
        resp = self.client.post("/users", data=json.dumps(payload), headers=headers)
        self.assertTrue(resp.status_code == 422)
        self.assertEqual(
            resp.json["errors"]["json"]["email"][0], "Missing data for required field."
        )

    def test_get_user(self):
        resp = self.client.get("/users/1")
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "User 1")

    def test_put_user(self):
        headers = {"Content-Type": "application/json"}
        payload = {"name": "My new name"}
        resp = self.client.put("/users/1", data=json.dumps(payload), headers=headers)
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "My new name")

    def test_bad_put_user(self):
        headers = {"Content-Type": "application/json"}
        payload = {"flame": "My new name"}
        resp = self.client.put("/users/1", data=json.dumps(payload), headers=headers)
        self.assertTrue(resp.status_code == 422)
        self.assertEqual(resp.json["errors"]["json"]["flame"], ["Unknown field."])

    def test_delete_user(self):
        resp = self.client.delete("/users/1")
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["message"], "Delete successful.")

    def test_get_user_location(self):
        resp = self.client.get("/users/1/locations")
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "Building 1")

    def test_post_user_location(self):
        headers = {"Content-Type": "application/json"}
        payload = {"location_id": 2}
        resp = self.client.post(
            "users/1/locations", data=json.dumps(payload), headers=headers
        )
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "Building 2")

    def test_delete_user_location(self):
        resp = self.client.delete("/users/1/locations")
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json, {})

    def test_user_attending(self):
        db.session.add(CourseUserAttended(course_id=1, user_id=1))
        db.session.commit()

        resp = self.client.get("/users/1/registrations")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]["attended"], False)
        self.assertEqual(resp.json[0]["course"]["title"], "Course 1")

    def test_user_presenting(self):
        resp = self.client.get("/users/2/presenting")
        self.assertTrue(resp.status_code == 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]["title"], "Course 1")
