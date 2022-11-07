import json

from tests.utils import TestBase, captured_templates

from app.extensions import db
from tests.loader import Loader


class TestCourseLinks(TestBase):
    @classmethod
    def setUpClass(self):
        self.app = self.create(self)

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

    @classmethod
    def tearDownClass(self):
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


class TestSingleCourseLink(TestBase):
    # This class cannot use the setUpClass method because the database
    # is mutated. Reset the database to the initial state before running.
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

    # JSON representation of link
    def test_get_single_link(self):
        resp = self.client.get("courses/1/links/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["name"], "Link 1")

    # Missing returns 404
    def test_get_missing_link(self):
        resp = self.client.get("courses/1/links/10")
        self.assertEqual(resp.status_code, 404)

    # Endpoint accepts JSON
    def test_update_single_link(self):
        self.login("Admin")
        headers = {"Content-Type": "application/json"}
        payload = {"name": "Updated link"}
        resp = self.client.put(
            "/courses/1/links/1", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["name"], "Updated link")

    # 422 when bad data is posted via JSON
    def test_bad_update_single_link(self):
        self.login("Admin")
        headers = {"Content-Type": "application/json"}
        payload = {"nam": "Updated link"}
        resp = self.client.put(
            "/courses/1/links/1", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json["errors"]["json"]["nam"][0], "Unknown field.")

    # Delete a link, check that the toast is sent
    def test_delete_single_link(self):
        self.login("Admin")
        resp = self.client.delete("/courses/1/links/1")

        header = resp.headers.get("HX-Trigger")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(header, '{"showToast": "Link deleted successfully."}')
        self.assertEqual(resp.get_data(as_text=True), "Ok")

    def test_delete_missing_link(self):
        self.login("Admin")
        resp = self.client.delete("/courses/1/links/10")
        self.assertEqual(resp.status_code, 404)
