import json
import unittest

from app.extensions import db
from tests.loader import Loader
from tests.utils import captured_templates, TestBase


class TestLocations(TestBase):
    def setUp(self):
        self.app = self.create()

        # Set up the application context manually to build the database
        # and test client for requests.
        ctx = self.app.app_context()
        ctx.push()

        self.client = self.app.test_client()

        fixtures = ["courses.json", "locations.json", "users.json"]

        # Now that we're in context, we can load the database.
        loader = Loader(self.app, db, fixtures)
        loader.load()

    def tearDown(self):
        db.drop_all()
        db.session.close()

    def test_get_locations(self):
        resp = self.client.get("/locations")
        self.assertTrue(resp.status_code == 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(resp.json[0]["name"], "Location 1")

    def test_post_location(self):
        self.login("Admin")
        payload = {
            "name": "Location 3",
            "description": "Location 3",
            "address": "999 Oak St.",
        }
        with captured_templates(self.app) as templates:
            resp = self.client.post("/locations", data=payload)

            titles = [template["template_name"] for template in templates]

            self.assertEqual(resp.status_code, 200)
            self.assertTrue("shared/form-fields/select.html" in titles)

    def test_post_bad_location(self):
        self.login("Admin")
        payload = {"description": "Another location", "address": "999 Oak St."}
        resp = self.client.post("/locations", data=payload)
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(
            resp.json["errors"]["form"]["name"][0], "Missing data for required field."
        )

    def test_get_single_location(self):
        self.login("Admin")
        resp = self.client.get("/locations/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["name"], "Location 1")

    def test_get_unknown_location(self):
        resp = self.client.get("/locations/20")
        self.assertEqual(resp.status_code, 404)

    def test_get_location_users(self):
        self.login("Admin")
        resp = self.client.get("/locations/1/users")
        self.assertTrue(resp.status_code == 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(resp.json[0]["name"], "Admin")

    def test_get_missing_location_users(self):
        self.login("Admin")
        resp = self.client.get("/locations/10/users")
        self.assertEqual(resp.status_code, 404)

    def test_get_location_courses(self):
        self.login("Admin")
        resp = self.client.get("/locations/1/courses")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 2)
