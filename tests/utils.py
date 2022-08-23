import unittest
from contextlib import contextmanager
from flask import template_rendered
from flask_login.utils import login_user

from app import app
from app.models import User

class TestBase(unittest.TestCase):
    @app.route('/auto_login/<user_name>')
    def auto_login(user_name):
        user = User.query.filter(User.name == user_name).first()
        login_user(user, remember=True)
        return "ok"

    def login(self, user_name):
        response = self.client.get(f"/auto_login/{user_name}")

@contextmanager
def captured_templates(app):
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append({
            "template_name": template.name,
            "context": context
        })
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)
