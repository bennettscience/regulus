import os
from unittest import skip

from app import app, db
from sqlalchemy import Table

from app.utils import get_user_navigation
from tests.utils import captured_templates, Loader, TestBase


class TestUtils(TestBase):
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

    # Anonymous users don't get extra nav items
    def test_get_user_navigation(self):

        with app.test_request_context():
            nav = get_user_navigation()
            self.assertEqual(len(nav), 0)
