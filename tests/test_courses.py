import datetime
import json
import time
import unittest

from app import app, db
from app.models import (
    Course,
    CourseLink,
    CourseLinkType,
    CourseUserAttended,
    Location,
    User,
    UserType,
)


class TestCourseList(unittest.TestCase):
    def setUp(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        db.create_all()
        self.client = app.test_client()

        c1 = Course(title="Course 1")
        l1 = Location(name="Location 1", address="123 main st")

        db.session.add_all([c1, l1])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_all_courses(self):
        resp = self.client.get("/courses")
        self.assertTrue(resp.status_code == 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(resp.json[0]["title"], "Course 1")

    def test_post_course(self):
        headers = {"Content-Type": "application/json"}
        now = datetime.datetime.now()
        next = now + datetime.timedelta(hours=1)
        payload = {
            "title": "Course 2",
            "description": "This is course 2",
            "course_size": 10,
            "starts": now.timestamp(),
            "ends": next.timestamp(),
            "location_id": 1,
        }
        resp = self.client.post("/courses", data=json.dumps(payload), headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["title"], "Course 2")
        self.assertEqual(resp.json["location"]["name"], "Location 1")

    def test_post_bad_course(self):
        headers = {"Content-Type": "application/json"}
        now = datetime.datetime.now()
        next = now + datetime.timedelta(hours=1)
        payload = {
            "description": "This is course 2",
            "course_size": 10,
            "starts": now.timestamp(),
            "ends": next.timestamp(),
            "location_id": 1,
        }
        resp = self.client.post("/courses", data=json.dumps(payload), headers=headers)
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(
            resp.json["errors"]["json"]["title"][0], "Missing data for required field."
        )


class TestSingleCourse(unittest.TestCase):
    def setUp(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        db.create_all()
        self.client = app.test_client()

        c1 = Course(title="Course 1")
        l1 = Location(name="Location 1", address="123 main st")

        db.session.add_all([c1, l1])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_single_course(self):
        resp = self.client.get("/courses/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["title"], "Course 1")

    def test_update_single_course(self):
        headers = {"Content-Type": "application/json"}
        payload = {"title": "The new name"}
        resp = self.client.put("/courses/1", data=json.dumps(payload), headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["title"], "The new name")

    def test_bad_update_single_course(self):
        headers = {"Content-Type": "application/json"}
        payload = {"titl": "The new name"}
        resp = self.client.put("/courses/1", data=json.dumps(payload), headers=headers)
        self.assertEqual(resp.status_code, 422)
        self.assertIsInstance(resp.json["errors"]["json"], dict)

    def delete_single_course(self):
        resp = self.client.delete("/courses/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["message"], "Course successfully deleted")


class TestCoursePresenters(unittest.TestCase):
    def setUp(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        db.create_all()
        self.client = app.test_client()

        c1 = Course(title="Course 1")
        ut1 = UserType(name="Presenter", description="Course presenter")
        u1 = User(name="Person 1", email="person@example.com", usertype_id=1)
        u2 = User(name="Person 2", email="person2@example.com", usertype_id=1)

        db.session.add_all([c1, ut1, u1, u2])

        c1.presenters.append(u1)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_course_presenters(self):
        resp = self.client.get("/courses/1/presenters")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 1)

    def test_add_course_presenters(self):
        headers = {"Content-Type": "application/json"}
        payload = {"user_ids": [2]}
        resp = self.client.post(
            "/courses/1/presenters", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 2)

    def test_bad_add_course_presenters(self):
        headers = {"Content-Type": "application/json"}
        payload = {"user_ids": 2}
        resp = self.client.post(
            "/courses/1/presenters", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 422)

    def test_delete_course_presenter(self):
        resp = self.client.delete("/courses/1/presenters/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["message"], "Deletion successful")


class TestCourseAttendees(unittest.TestCase):
    def setUp(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        db.create_all()
        self.client = app.test_client()

        c1 = Course(title="Course 1")
        p1 = User(name="Presenter", email="presenter@example.com")
        u1 = User(name="Attendee 1", email="attendee@example.com")
        u2 = User(name="Attendee 2", email="attendee2@example.com")

        cr1 = CourseUserAttended(course_id=1, user_id=1)
        cr2 = CourseUserAttended(course_id=1, user_id=2)

        db.session.add_all([c1, p1, u1, u2, cr1, cr2])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_course_attendees(self):
        resp = self.client.get("/courses/1/registrations")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 2)

    def test_update_attendee_attended(self):
        headers = {"Content-Type": "application/json"}
        payload = {"user_ids": [1, 2]}
        resp = self.client.put(
            "/courses/1/registrations", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(resp.json[0]["attended"], True)

    def test_bad_update_attendee_attended(self):
        headers = {"Content-Type": "application/json"}
        payload = {"user_ids": 2}
        resp = self.client.post(
            "/courses/1/registrations", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 422)

    def test_add_attendees_to_course(self):
        pass


class TestCourseAttendeeAPI(unittest.TestCase):
    def setUp(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        db.create_all()
        self.client = app.test_client()

        c1 = Course(title="Course 1")
        u1 = User(name="Attendee 1", email="attendee@example.com")
        u2 = User(name="Attendee 2", email="attendee2@example.com")

        cr1 = CourseUserAttended(course_id=1, user_id=1)

        db.session.add_all([c1, u1, u2, cr1])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_post_single_user_to_course(self):
        headers = {"Content-Type": "application/json"}
        resp = self.client.post("/courses/1/registrations/2", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["attended"], False)
        self.assertEqual(resp.json["user"]["name"], "Attendee 2")

    def test_bad_post_single_user(self):
        headers = {"Content-Type": "application/json"}
        resp = self.client.post("/courses/1/registrations/3", headers=headers)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json["description"], "No user with id <3>")

    def test_update_single_user(self):
        headers = {"Content-Type": "application/json"}
        resp = self.client.put("/courses/1/registrations/1", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["attended"], True)
        self.assertEqual(resp.json["user"]["name"], "Attendee 1")

    def test_bad_update_single_user(self):
        headers = {"Content-Type": "application/json"}
        resp = self.client.put("/courses/1/registrations/3", headers=headers)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.json["description"], "No user with id <3> registered for this course"
        )

    def test_delete_user_from_course(self):
        resp = self.client.delete("/courses/1/registrations/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["message"], "Registration successfully cancelled")
