import json


from app.extensions import db
from tests.loader import Loader
from tests.utils import TestBase


class TestCourseLinkTypes(TestBase):
    def setUp(self):
        self.app = self.create()

        # Set up the application context manually to build the database
        # and test client for requests.
        ctx = self.app.app_context()
        ctx.push()

        self.client = self.app.test_client()

        fixtures = ["course_link_type.json", "users.json"]

        # Now that we're in context, we can load the database.
        loader = Loader(self.app, db, fixtures)
        loader.load()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_all_link_types(self):
        self.login("Admin")
        resp = self.client.get("/courselinktypes")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 2)

    def test_create_new_link_type(self):
        self.login("Admin")
        headers = {"Content-Type": "application/json"}
        payload = {"name": "Link Type 3", "description": "The third link type"}
        resp = self.client.post(
            "/courselinktypes", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json), 3)
        self.assertEqual(resp.json["name"], "Link Type 3")

    def test_create_bad_link_type(self):
        self.login("Admin")
        headers = {"Content-Type": "application/json"}
        payload = {"description": "Link type 2"}
        resp = self.client.post(
            "/courselinktypes", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 422)

    def test_get_single_link_type(self):
        self.login("Admin")
        resp = self.client.get("/courselinktypes/1")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json["name"] == "Type 1")

    def test_get_missing_single_link_type(self):
        self.login("Admin")
        resp = self.client.get("/courselinktypes/3")
        self.assertEqual(resp.status_code, 404)

    def test_update_link_type(self):
        self.login("Admin")
        headers = {"Content-Type": "application/json"}
        payload = {"description": "Updated"}
        resp = self.client.put(
            "/courselinktypes/1", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json["description"] == "Updated")

    def test_bad_update_link_type(self):
        self.login("Admin")
        headers = {"Content-Type": "application/json"}
        payload = {"danger": "The second link type"}
        resp = self.client.put(
            "/courselinktypes/1", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 422)

    def test_missing_update_link_type(self):
        self.login("Admin")
        headers = {"Content-Type": "application/json"}
        payload = {"description": "The second link type"}
        resp = self.client.put(
            "/courselinktypes/3", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 404)

    def test_delete_link_type(self):
        self.login("Admin")
        resp = self.client.delete("/courselinktypes/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["message"], "Link type successfully deleted")
