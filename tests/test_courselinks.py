import json

from flask_login import login_user
from tests.utils import TestBase, captured_templates

from app.extensions import db
from app.models import Course, CourseLink, CourseLinkType, User
from tests.loader import Loader


class TestCourseLinks(TestBase):
    def setUp(self):
        self.app = self.create()

        # Set up the application context manually to build the database
        # and test client for requests.
        ctx = self.app.app_context()
        ctx.push()

        self.client = self.app.test_client()

        fixtures = [
            "courses.json",
            "users.json",
            "course_link.json",
            "course_link_type.json",
        ]

        # Now that we're in context, we can load the database.
        loader = Loader(self.app, db, fixtures)
        loader.load()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    # Get all links for a course
    # No role limits
    def test_get_course_links(self):
        self.login("Admin")
        resp = self.client.get("/courses/1/links")

        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertTrue(len(resp.json), 2)

    def test_get_course_links_unauthorized(self):
        resp = self.client.get("/courses/1/links")

        self.assertEqual(resp.status_code, 401)

    def test_add_course_link(self):
        self.login("Admin")
        with captured_templates(self.app) as templates:
            payload = {
                "courselinktype_id": 1,
                "name": "Session link",
                "uri": "https://example.com",
            }
            resp = self.client.post("/courses/1/links", data=payload)

            result = templates[0]

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(result["template_name"], "shared/partials/event-link.html")
            self.assertEqual(result["context"]["link"].name, "Session link")

    def test_bad_course_link(self):
        self.login("Admin")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {"name": "Session link", "uri": "https://example.com"}
        resp = self.client.post(
            "/courses/1/links", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(
            resp.json["errors"]["form"]["courselinktype_id"][0],
            "Missing data for required field.",
        )


# class TestSingleCourseLink(TestBase):
#     def setUp(self):
#         app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
#         db.create_all()
#         self.client = app.test_client()

#         c1 = Course(title="Course 1")
#         cl1 = CourseLink(
#             name="Location 1",
#             course_id=1,
#             courselinktype_id=1,
#             uri="https://example.com",
#         )
#         lt1 = CourseLinkType(name="Meet", description="Google Meet link")

#         db.session.add_all([c1, cl1, lt1])
#         db.session.commit()

#     def tearDown(self):
#         db.session.remove()
#         db.drop_all()

#     # JSON representation of link
#     def test_get_single_link(self):
#         resp = self.client.get("courses/1/links/1")
#         self.assertEqual(resp.status_code, 200)
#         self.assertEqual(resp.json["name"], "Location 1")

#     # Missing returns 404
#     def test_get_missing_link(self):
#         resp = self.client.get("courses/1/links/10")
#         self.assertEqual(resp.status_code, 404)

#     # Endpoint accepts JSON
#     def test_update_single_link(self):
#         headers = {"Content-Type": "application/json"}
#         payload = {"name": "Updated link"}
#         resp = self.client.put(
#             "/courses/1/links/1", data=json.dumps(payload), headers=headers
#         )
#         self.assertEqual(resp.status_code, 200)
#         self.assertEqual(resp.json["name"], "Updated link")

#     # 422 when bad data is posted via JSON
#     def test_bad_update_single_link(self):
#         headers = {"Content-Type": "application/json"}
#         payload = {"nam": "Updated link"}
#         resp = self.client.put(
#             "/courses/1/links/1", data=json.dumps(payload), headers=headers
#         )
#         self.assertEqual(resp.status_code, 422)
#         self.assertEqual(resp.json["errors"]["json"]["nam"][0], "Unknown field.")

#     # Delete a link, check that the toast is sent
#     def test_delete_single_link(self):
#         resp = self.client.delete("/courses/1/links/1")

#         header = resp.headers.get('HX-Trigger')

#         self.assertEqual(resp.status_code, 200)
#         self.assertEqual(header, '{"showToast": "Link deleted successfully."}')
#         self.assertEqual(resp.get_data(as_text=True), "Ok")

#     def test_delete_missing_link(self):
#         resp = self.client.delete("/courses/1/links/10")
#         self.assertEqual(resp.status_code, 404)
