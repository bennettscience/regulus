import os
from unittest import skip

from app import app, db
from sqlalchemy import Table

from tests.utils import TestBase, Loader, captured_templates
from app.wrappers import admin_only, admin_or_self, restricted


class TestWrappers(TestBase):
    def setUp(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        app.config["TESTING"] = True
        db.create_all()

        fixtures = [
            "roles.json",
            "users.json",
        ]

        self.client = app.test_client()

        conn = db.engine.connect()
        metadata = db.metadata

        for filename in fixtures:
            filepath = os.path.join(app.config.get("FIXTURES_DIR"), filename)
            if os.path.exists(filepath):
                data = Loader.load(filepath)
                table = Table(data[0]["table"], metadata)
                conn.execute(table.insert(), data[0]["records"])
            else:
                raise IOError(
                    "Error loading '{0}'. File could not be found".format(filename)
                )

    def tearDown(self):
        db.drop_all()
        db.session.close()

    # Set up some test routes
    @app.route("/admin_only")
    @admin_only
    def admin_only_route():
        return "ok", 200

    @app.route("/admin_or_self/<int:user_id>")
    @admin_or_self
    def admin_or_self_route(user_id):
        return "ok", 200

    @app.route("/restricted")
    @restricted
    def restricted_route():
        return "ok", 200

    def test_as_anonymous(self):
        resp1 = self.client.get("/admin_only")
        resp2 = self.client.get("/admin_or_self/1")
        resp3 = self.client.get("/restricted")

        self.assertEqual(resp1.status_code, 401)
        self.assertEqual(resp2.status_code, 401)
        self.assertEqual(resp3.status_code, 401)

    def test_admin_only(self):
        self.login("Admin")

        resp = self.client.get("/admin_only")
        self.assertEqual(resp.status_code, 200)

    def test_admin_only_as_non_admin(self):
        self.login("User")

        resp = self.client.get("/admin_only")
        self.assertEqual(resp.status_code, 403)

    def test_admin_or_self(self):
        self.login("User")

        # The User fixture is ID #3
        resp = self.client.get("/admin_or_self/3")
        self.assertEqual(resp.status_code, 200)

    def test_restricted_as_admin(self):
        # Accepts either an admin or a presenter
        self.login("Admin")

        resp = self.client.get("/restricted")
        self.assertEqual(resp.status_code, 200)

    def test_restricted_as_presenter(self):
        # Accepts either an admin or a presenter
        self.login("Presenter")

        resp = self.client.get("/restricted")
        self.assertEqual(resp.status_code, 200)
