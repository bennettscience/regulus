import datetime
import json
import unittest

from unittest.mock import Mock, patch

from app.extensions import db
from app.models import (
    Course,
    CourseUserAttended,
    Location,
    User,
    UserType,
)

from app.resources import courses

from tests.loader import Loader
from tests.utils import TestBase, captured_templates


class TestCourseList(TestBase):
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

    def test_get_all_courses(self):
        self.login("User")
        resp = self.client.get("/courses")
        self.assertEqual(resp.status_code, 200)

    @patch("app.resources.courses.requests.post")
    def test_post_course(self, mock_post):
        self.login("Admin")
        headers = {"Content-Type": "application/json"}
        now = datetime.datetime.now()
        next = now + datetime.timedelta(hours=1)
        # POST a course as "In Person" to avoid creating a Google Meet in the test.
        payload = {
            "title": "Course 2",
            "description": "This is course 2",
            "course_size": 10,
            "starts": now.timestamp(),
            "ends": next.timestamp(),
            "location_id": 1,
            "coursetype_id": 2,
        }

        # Mock the requests data in order to skip the Google Calendar endpoint
        # See https://stackoverflow.com/questions/48432029/mocking-requests-post-and-requests-json-decoder-python
        # for how to mock out responses from requests.
        mock_post.return_value = Mock(status_code=200, json=lambda: {"id": 12345})

        resp = self.client.post("/courses", data=json.dumps(payload), headers=headers)
        self.assertEqual(resp.status_code, 200)

    def test_post_bad_course(self):
        self.login("Admin")
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


class TestSingleCourse(TestBase):
    def setUp(self):
        self.app = self.create()
        ctx = self.app.app_context()
        ctx.push()

        self.client = self.app.test_client()

        fixtures = ["courses.json", "locations.json", "users.json"]

        loader = Loader(self.app, db, fixtures)
        loader.load()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_single_course(self):
        self.login("User")
        with captured_templates(self.app) as templates:
            resp = self.client.get("/courses/1")
            titles = [template["template_name"] for template in templates]

            # Check that all the required templates are present
            self.assertTrue("events/partials/registration-form.html" in titles)
            self.assertTrue("events/partials/event-details.html" in titles)
            self.assertTrue("shared/partials/sidebar.html" in titles)

            self.assertEqual(resp.status_code, 200)

    # Update title only
    def test_update_single_course(self):
        self.login("Admin")
        headers = {"Content-Type": "application/json"}
        payload = {"title": "The new name"}

        with captured_templates(self.app) as templates:
            resp = self.client.put(
                "/courses/1", data=json.dumps(payload), headers=headers
            )
            titles = [template["template_name"] for template in templates]

            # Check the template and the toast
            self.assertTrue("admin/partials/event-detail.html" in titles)
            self.assertIsNotNone(resp.headers.get("HX-Trigger"))
            self.assertEqual(
                resp.headers.get("HX-Trigger"),
                '{"showToast": "Successfully updated The new name"}',
            )
            self.assertEqual(resp.status_code, 200)

    def test_update_single_course_no_data(self):
        self.login("Admin")
        headers = {"Content-Type": "application/json"}
        payload = {}

        with captured_templates(self.app) as templates:
            resp = self.client.put(
                "/courses/1", data=json.dumps(payload), headers=headers
            )
            titles = [template["template_name"] for template in templates]

            # Check the template and the toast
            self.assertTrue("admin/partials/event-detail.html" in titles)
            self.assertIsNotNone(resp.headers.get("HX-Trigger"))
            self.assertEqual(
                resp.headers.get("HX-Trigger"), '{"showToast": "Nothing to update"}'
            )
            self.assertEqual(resp.status_code, 200)

    @patch("app.resources.courses.requests.put")
    def test_update_single_course_date(self, mock_put):
        self.login("Admin")
        now = datetime.datetime.now()
        ends = now + datetime.timedelta(hours=1)
        headers = {"Content-Type": "application/json"}
        payload = {"starts": now.timestamp(), "ends": ends.timestamp()}

        mock_put.return_value = Mock(status_code=200, json=lambda: {"id": 12345})

        with captured_templates(self.app) as templates:
            resp = self.client.put(
                "/courses/1", data=json.dumps(payload), headers=headers
            )
            titles = [template["template_name"] for template in templates]

            self.assertTrue("admin/partials/event-detail.html" in titles)
            self.assertEqual(resp.status_code, 200)

    def test_bad_update_single_course(self):
        self.login("Admin")
        headers = {"Content-Type": "application/json"}
        payload = {"titl": "The new name"}
        resp = self.client.put("/courses/1", data=json.dumps(payload), headers=headers)
        self.assertEqual(resp.status_code, 422)
        self.assertIsInstance(resp.json["errors"]["json"], dict)

    def test_delete_single_course(self):
        self.login("Admin")
        resp = self.client.delete("/courses/1")
        self.assertTrue(
            resp.headers.get("HX-Trigger"),
            '{"showToast": "Successfully deleted Course 1"}',
        )
        self.assertEqual(resp.status_code, 200)


# class TestCoursePresenters(TestBase):
#     def setUp(self):
#         self.app = self.create()
#         ctx = self.app.app_context()
#         ctx.push()

#         self.client = self.app.test_client()

#         fixtures = [
#             "courses.json",
#             "roles.json",
#             "users.json"
#         ]

#         loader = Loader(self.app, db, fixtures)
#         loader.load()

#     def test_get_course_presenters(self):
#         self.login("Admin")
#         resp = self.client.get("/courses/1/presenters")
#         self.assertEqual(resp.status_code, 200)

#     @unittest.skip()
#     def test_add_course_presenters(self):
#         self.login("Admin")
#         payload = {"user_ids": [2]}
#         resp = self.client.post(
#             "/courses/1/presenters", data=payload
#         )
#         self.assertEqual(resp.status_code, 200)

#     def test_bad_add_course_presenters(self):
#         self.login("Admin")
#         headers = {"Content-Type": "application/json"}
#         payload = {"user_ids": 2}
#         resp = self.client.post(
#             "/courses/1/presenters", data=json.dumps(payload), headers=headers
#         )
#         self.assertEqual(resp.status_code, 422)

#     def test_delete_course_presenter(self):
#         self.login("Admin")
#         resp = self.client.delete("/courses/1/presenters/1")
#         self.assertEqual(resp.status_code, 200)
#         self.assertEqual(resp.json["message"], "Deletion successful")


# class TestCourseAttendees(unittest.TestCase):
#     fixtures = [
#         "courses.json",
#         "users.json"
#     ]
#     def setUp(self):
#         app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
#         db.create_all()
#         self.client = app.test_client()

#         c1 = Course(title="Course 1")
#         p1 = User(name="Presenter", email="presenter@example.com")
#         u1 = User(name="Attendee 1", email="attendee@example.com")
#         u2 = User(name="Attendee 2", email="attendee2@example.com")

#         cr1 = CourseUserAttended(course_id=1, user_id=1)
#         cr2 = CourseUserAttended(course_id=1, user_id=2)

#         db.session.add_all([c1, p1, u1, u2, cr1, cr2])
#         db.session.commit()

#     def tearDown(self):
#         db.session.remove()
#         db.drop_all()

#     def test_get_course_attendees(self):
#         resp = self.client.get("/courses/1/registrations")
#         self.assertEqual(resp.status_code, 200)
#         self.assertIsInstance(resp.json, list)
#         self.assertEqual(len(resp.json), 2)

#     def test_update_attendee_attended(self):
#         headers = {"Content-Type": "application/json"}
#         payload = {"user_ids": [1, 2]}
#         resp = self.client.put(
#             "/courses/1/registrations", data=json.dumps(payload), headers=headers
#         )
#         self.assertEqual(resp.status_code, 200)
#         self.assertIsInstance(resp.json, list)
#         self.assertEqual(resp.json[0]["attended"], True)

#     def test_bad_update_attendee_attended(self):
#         headers = {"Content-Type": "application/json"}
#         payload = {"user_ids": 2}
#         resp = self.client.post(
#             "/courses/1/registrations", data=json.dumps(payload), headers=headers
#         )
#         self.assertEqual(resp.status_code, 422)

#     def test_add_attendees_to_course(self):
#         pass


# class TestCourseAttendeeAPI(unittest.TestCase):
#     def setUp(self):
#         app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
#         db.create_all()
#         self.client = app.test_client()

#         c1 = Course(title="Course 1")
#         u1 = User(name="Attendee 1", email="attendee@example.com")
#         u2 = User(name="Attendee 2", email="attendee2@example.com")

#         cr1 = CourseUserAttended(course_id=1, user_id=1)

#         db.session.add_all([c1, u1, u2, cr1])
#         db.session.commit()

#     def tearDown(self):
#         db.session.remove()
#         db.drop_all()

#     def test_post_single_user_to_course(self):
#         headers = {"Content-Type": "application/json"}
#         resp = self.client.post("/courses/1/registrations/2", headers=headers)
#         self.assertEqual(resp.status_code, 200)
#         self.assertEqual(resp.json["attended"], False)
#         self.assertEqual(resp.json["user"]["name"], "Attendee 2")

#     def test_bad_post_single_user(self):
#         headers = {"Content-Type": "application/json"}
#         resp = self.client.post("/courses/1/registrations/3", headers=headers)
#         self.assertEqual(resp.status_code, 404)
#         self.assertEqual(resp.json["description"], "No user with id <3>")

#     def test_update_single_user(self):
#         headers = {"Content-Type": "application/json"}
#         resp = self.client.put("/courses/1/registrations/1", headers=headers)
#         self.assertEqual(resp.status_code, 200)
#         self.assertEqual(resp.json["attended"], True)
#         self.assertEqual(resp.json["user"]["name"], "Attendee 1")

#     def test_bad_update_single_user(self):
#         headers = {"Content-Type": "application/json"}
#         resp = self.client.put("/courses/1/registrations/3", headers=headers)
#         self.assertEqual(resp.status_code, 404)
#         self.assertEqual(
#             resp.json["description"], "No user with id <3> registered for this course"
#         )

#     def test_delete_user_from_course(self):
#         resp = self.client.delete("/courses/1/registrations/1")
#         self.assertEqual(resp.status_code, 200)
#         self.assertEqual(resp.json["message"], "Registration successfully cancelled")
