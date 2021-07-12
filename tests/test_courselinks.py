import json
import unittest

from app import app, db
from app.models import Course, CourseLink, CourseLinkType


class TestDirectCourseLinks(unittest.TestCase):
    def setUp(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        db.create_all()
        self.client = app.test_client()

        cl1 = CourseLink(
            name="Location 1",
            course_id=1,
            courselinktype_id=1,
            uri="https://example.com",
        )
        lt1 = CourseLinkType(name="Notes", description="Notes for a session")

        db.session.add_all([cl1, lt1])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class TestCourseLinks(unittest.TestCase):
    def setUp(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        db.create_all()
        self.client = app.test_client()

        c1 = Course(title="Course 1")
        cl1 = CourseLink(
            name="Location 1",
            course_id=1,
            courselinktype_id=1,
            uri="https://example.com",
        )
        lt1 = CourseLinkType(name="Notes", description="Notes for a session")

        db.session.add_all([c1, cl1, lt1])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_course_links(self):
        resp = self.client.get("/courses/1/links")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertTrue(len(resp.json), 2)

    def test_add_course_link(self):
        headers = {"Content-Type": "application/json"}
        payload = {
            "courselinktype_id": 1,
            "name": "Session link",
            "uri": "https://example.com",
        }
        resp = self.client.post(
            "/courses/1/links", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, dict)
        self.assertEqual(resp.json["name"], "Session link")
        self.assertEqual(resp.json["type"]["name"], "Notes")

    def test_bad_course_link(self):
        headers = {"Content-Type": "application/json"}
        payload = {"name": "Session link", "uri": "https://example.com"}
        resp = self.client.post(
            "/courses/1/links", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(
            resp.json["messages"]["json"]["courselinktype_id"][0],
            "Missing data for required field.",
        )


class TestSingleCourseLink(unittest.TestCase):
    def setUp(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        db.create_all()
        self.client = app.test_client()

        c1 = Course(title="Course 1")
        cl1 = CourseLink(
            name="Location 1",
            course_id=1,
            courselinktype_id=1,
            uri="https://example.com",
        )
        lt1 = CourseLinkType(name="Meet", description="Google Meet link")

        db.session.add_all([c1, cl1, lt1])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_single_link(self):
        resp = self.client.get("courses/1/links/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["name"], "Location 1")

    def test_get_missing_link(self):
        resp = self.client.get("courses/1/links/10")
        self.assertEqual(resp.status_code, 404)

    def test_update_single_link(self):
        headers = {"Content-Type": "application/json"}
        payload = {"name": "Updated link"}
        resp = self.client.put(
            "/courses/1/links/1", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["name"], "Updated link")

    def test_bad_update_single_link(self):
        headers = {"Content-Type": "application/json"}
        payload = {"nam": "Updated link"}
        resp = self.client.put(
            "/courses/1/links/1", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json["messages"]["json"]["nam"][0], "Unknown field.")

    def test_delete_single_link(self):
        resp = self.client.delete("/courses/1/links/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["message"], "Deletion successful")

    def test_delete_missing_link(self):
        resp = self.client.delete("/courses/1/links/10")
        self.assertEqual(resp.status_code, 404)
