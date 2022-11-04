import unittest

from contextlib import contextmanager
from flask import template_rendered
from flask_login.utils import login_user

from app import create_app
from app.extensions import db
from app.models import User
from app.schemas import UserSchema
from config import TestConfig


class TestBase(unittest.TestCase):
    def create(self):
        self.app = create_app(TestConfig)

        # Build the database structure in the application context
        with self.app.app_context():
            db.init_app(self.app)
            db.create_all()

            @self.app.route("/auto_login/<user_name>")
            def auto_login(user_name):
                user = User.query.filter(User.name == user_name).first()
                login_user(user, remember=True)
                return UserSchema().dump(user)

        return self.app

    def login(self, user_name):
        return self.client.get(f"/auto_login/{user_name}")


@contextmanager
def captured_templates(app):
    # Capture all request data and return a dictionary to the test runner
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append({"template_name": template.name, "context": context})

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)
