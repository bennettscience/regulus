import json
import unittest

from app import app, db
from app.models import UserType


class TestUserType(unittest.TestCase):
    def setUp(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        db.create_all()
        self.client = app.test_client()

        ut1 = UserType(name="Type1", description="The first user type")
        ut2 = UserType(name="Type2", description="The second user type")
        db.session.add_all([ut1, ut2])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_user_type(self):
        resp = self.client.get("/usertypes")
        self.assertIsInstance(resp.json, list)
        self.assertTrue(len(resp.json), 2)
        self.assertEqual(resp.json[0]["name"], "Type1")

    def test_post_user_type(self):
        payload = {"name": "Type3", "description": "A third type."}
        headers = {"Content-Type": "application/json"}
        resp = self.client.post("/usertypes", data=json.dumps(payload), headers=headers)
        self.assertEqual(resp.json["id"], 3)
