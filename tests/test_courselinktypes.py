import json
import unittest

from app import app, db
from app.models import CourseLinkType


class TestCourseLinkTypes(unittest.TestCase):
    def setUp(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        db.create_all()
        self.client = app.test_client()

        ut1 = CourseLinkType(name="Type 1", description="The first link type")

        db.session.add_all([ut1])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_all_link_types(self):
        resp = self.client.get("/courselinktypes")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)

    def test_create_new_link_type(self):
        headers = {"Content-Type": "application/json"}
        payload = {"name": "Link Type 2", "description": "The second link type"}
        resp = self.client.post(
            "/courselinktypes", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["name"], "Link Type 2")

    def test_create_bad_link_type(self):
        headers = {"Content-Type": "application/json"}
        payload = {"description": "The second link type"}
        resp = self.client.post(
            "/courselinktypes", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 422)

    def test_get_single_link_type(self):
        resp = self.client.get("/courselinktypes/1")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json["name"] == "Type 1")

    def test_get_missing_single_link_type(self):
        resp = self.client.get("/courselinktypes/3")
        self.assertEqual(resp.status_code, 404)

    def test_update_link_type(self):
        headers = {"Content-Type": "application/json"}
        payload = {"description": "Updated"}
        resp = self.client.put(
            "/courselinktypes/1", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json["description"] == "Updated")

    def test_bad_update_link_type(self):
        headers = {"Content-Type": "application/json"}
        payload = {"danger": "The second link type"}
        resp = self.client.put(
            "/courselinktypes/1", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 422)

    def test_missing_update_link_type(self):
        headers = {"Content-Type": "application/json"}
        payload = {"description": "The second link type"}
        resp = self.client.put(
            "/courselinktypes/3", data=json.dumps(payload), headers=headers
        )
        self.assertEqual(resp.status_code, 404)

    def test_delete_link_type(self):
        resp = self.client.delete("/courselinktypes/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["message"], "Link type successfully deleted")

    def test_delete_missing_link_type(self):
        resp = self.client.delete("/courselinktypes/3")
        self.assertEqual(resp.status_code, 404)
