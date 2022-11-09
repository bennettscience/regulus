from app.extensions import db
from sqlalchemy import Table

from tests.loader import Loader
from tests.utils import TestBase
from app.wrappers import admin_only, admin_or_self, restricted


class TestWrappers(TestBase):
    def setUp(self):
        self.app = self.create()

        # Set up the application context manually to build the database
        # and test client for requests.
        ctx = self.app.app_context()
        ctx.push()

        self.client = self.app.test_client()

        fixtures = ["roles.json", "users.json"]

        # Now that we're in context, we can load the database.
        loader = Loader(self.app, db, fixtures)
        loader.load()

        # Set up some test routes
        @self.app.route("/admin_only")
        @admin_only
        def admin_only_route():
            return "ok", 200

        @self.app.route("/admin_or_self/<int:user_id>")
        @admin_or_self
        def admin_or_self_route(user_id):
            return "ok", 200

        @self.app.route("/restricted")
        @restricted
        def restricted_route():
            return "ok", 200

    def tearDown(self):
        db.drop_all()
        db.session.close()

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
