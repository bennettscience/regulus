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


class TestCoursePresenters(TestBase):
    def setUp(self):
        self.app = self.create()
        ctx = self.app.app_context()
        ctx.push()

        self.client = self.app.test_client()

        fixtures = [
            "courses.json",
            "roles.json",
            "users.json",
            "course_presenters.json",
        ]

        loader = Loader(self.app, db, fixtures)
        loader.load()

    def tearDown(self):
        db.drop_all()
        db.session.close()

    def test_get_course_presenters(self):
        self.login("Admin")
        resp = self.client.get("/courses/1/presenters")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]["name"], "Admin")

    @patch("app.resources.courses.requests.post")
    def test_add_course_presenters(self, mock_put):
        self.login("Admin")
        payload = {"user_ids": [2]}
        mock_response = {
            "status": "ok",
            "statusCode": 200,
            "message": "The event was updated successfully.",
        }

        mock_put.return_value = Mock(
            status_code=200, json=lambda: json.dumps(mock_response)
        )
        with captured_templates(self.app) as templates:
            resp = self.client.post("/courses/1/presenters", data=payload)
            titles = [template["template_name"] for template in templates]

            self.assertTrue("shared/partials/event-presenter.html" in titles)
            self.assertEqual(resp.status_code, 200)

    def test_bad_add_course_presenters(self):
        self.login("Admin")
        headers = {"Content-Type": "application/json"}
        payload = {"user_ids": 2}
        resp = self.client.post(
            "/courses/1/presenters", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 422)

    def test_delete_course_presenter(self):
        self.login("Admin")
        resp = self.client.delete("/courses/1/presenters/1")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text, "ok")
        self.assertEqual(
            resp.headers.get("HX-Trigger"),
            '{"showToast": "Successfully removed the presenter."}',
        )


class TestCourseAttendees(TestBase):
    def setUp(self):
        self.app = self.create()

        # Set up the application context manually to build the database
        # and test client for requests.
        ctx = self.app.app_context()
        ctx.push()

        self.client = self.app.test_client()

        fixtures = [
            "courses.json",
            "course_registrations.json",
            "users.json",
        ]

        # Now that we're in context, we can load the database.
        loader = Loader(self.app, db, fixtures)
        loader.load()

    def tearDown(self):
        db.drop_all()
        db.session.close()

    def test_get_course_attendees(self):
        self.login("Admin")
        resp = self.client.get("/courses/1/registrations")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 2)

    def test_update_all_attendees_attended_as_admin(self):
        """
        Calls app.resources.courses.CourseAttendeesAPI.put
        """
        self.login("Admin")

        with captured_templates(self.app) as templates:
            resp = self.client.put("/courses/1/registrations")
            titles = [template["template_name"] for template in templates]

            self.assertEqual(resp.status_code, 200)
            self.assertTrue("admin/partials/registration-table.html" in titles)

            registrations = templates[0]["context"]["registrations"].all()

            # Check that both registrations are attended
            for reg in registrations:
                self.assertEqual(reg.attended, True)

    def test_update_all_attendees_attended_as_presenter(self):
        """
        Calls app.resources.courses.CourseAttendeesAPI.put
        """
        self.login("Presenter")
        with captured_templates(self.app) as templates:
            resp = self.client.put("/courses/1/registrations")
            titles = [template["template_name"] for template in templates]

            self.assertEqual(resp.status_code, 200)
            self.assertTrue("admin/partials/registration-table.html" in titles)

            registrations = templates[0]["context"]["registrations"].all()

            # Check that both registrations are attended
            for reg in registrations:
                self.assertEqual(reg.attended, True)

    @patch("app.resources.courses.requests.post")
    def test_bulk_add_attendees_to_course(self, mock_post):
        """
        Calls app.resources.courses.CourseAttendeesAPI.post
        Expects an array of user_ids[int]
        """
        self.login("Admin")
        payload = {"user_ids": [4, 5]}

        mock_response = {
            "status": "ok",
            "statusCode": 200,
            "message": "The event was updated successfully.",
        }
        mock_post.return_value = Mock(
            status_code=200, json=lambda: json.dumps(mock_response)
        )

        resp = self.client.post("/courses/1/registrations", data=payload)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.headers.get("HX-Trigger"),
            '{"showToast": "Updated registrations successfully."}',
        )

    def test_bad_bulk_add_attendees_to_course(self):
        """
        Calls app.resources.courses.CourseAttendeesAPI.post
        Expects an array of user_ids[int]
        """
        self.login("Admin")

        resp = self.client.post("/courses/1/registrations")

        self.assertEqual(resp.status_code, 422)


class TestCourseAttendeeAPI(TestBase):
    def setUp(self):
        self.app = self.create()

        # Set up the application context manually to build the database
        # and test client for requests.
        ctx = self.app.app_context()
        ctx.push()

        self.client = self.app.test_client()

        fixtures = ["courses.json", "users.json", "course_registrations.json"]

        # Now that we're in context, we can load the database.
        loader = Loader(self.app, db, fixtures)
        loader.load()

    def tearDown(self):
        db.drop_all()
        db.session.close()

    @patch("app.resources.courses.requests.post")
    def test_post_single_user_to_course(self, mock_post):
        """
        A user self-registers for a course.
        Calls `app.courses.CourseAttendeeAPI.post'
        """
        self.login("User 2")
        payload = {"acc_required": False, "acc_details": ""}

        mock_response = {
            "status": "ok",
            "statusCode": 200,
            "message": "The event was updated successfully.",
        }
        mock_post.return_value = Mock(
            status_code=200, json=lambda: json.dumps(mock_response)
        )

        with captured_templates(self.app) as templates:
            resp = self.client.post("/courses/1/register", data=payload)

            titles = [template["template_name"] for template in templates]

            self.assertEqual(resp.status_code, 200)
            self.assertTrue("events/partials/event-card.html" in titles)

    def test_update_single_user(self):
        """
        Update a single user's registration status
        Calls `app.resources.courses.CourseAttendeeAPI.put`
        """
        payload = {"attended": True}
        resp = self.client.put("/courses/1/registrations/1", data=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["attended"], True)
        self.assertEqual(resp.json["user"]["name"], "Admin")

    def test_bad_update_single_user(self):
        payload = {"attended": True}
        resp = self.client.put("/courses/1/registrations/3", data=payload)

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            resp.headers.get("HX-Trigger"),
            '{"showToast": "No user with id <3> registered for this course."}',
        )

    @patch("app.resources.courses.requests.post")
    def test_delete_user_from_course(self, mock_post):
        """
        A user cancells their registration.
        Calls `app.resources.courses.CourseAttendeeAPI.delete`
        """
        self.login("Admin")
        mock_response = {
            "status": "ok",
            "statusCode": 200,
            "message": "The event was updated successfully.",
        }
        mock_post.return_value = Mock(
            status_code=200, json=lambda: json.dumps(mock_response)
        )

        resp = self.client.delete("/courses/1/register")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.headers.get("HX-Trigger"),
            '{"showToast": "Successfully cancelled registration for Course 1"}',
        )
