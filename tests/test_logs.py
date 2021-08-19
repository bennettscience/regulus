import json
import unittest

from flask_login.utils import login_user

from app import app, db
from app.models import Course, Log, Location, User, UserType


class TestLog(unittest.TestCase):
    @app.route('/auto_login/<username>')
    def auto_login(username):
        user = User.query.filter_by(name=username).first()
        login_user(user, remember=True)
        return "ok"
    
    def login(self, username):
        response = self.client.get(f"/auto_login/{username}")
    
    def setUp(self) -> None:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
        db.create_all()
        user = User(name="User", location_id=1, usertype_id=4)
        superadmin = User(name="SuperAdmin", location_id=1, usertype_id=1)
        course = Course(title="Course 1")
        location = Location(name="Building 1")
        ut = UserType(name="Type1")
        
        db.session.add_all([course, user, superadmin, location, ut])
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
    
    # Log is empty because it is an anonymous request.
    def test_anonymous_log(self):
        self.client.get("/courses")
        log = Log.query.all()
        self.assertEqual(len(log), int('0'))

    def test_authenticated_log(self):
        self.login("User")
        resp = self.client.get("/users/1")
        log = Log.query.all()
        self.assertEqual(len(log), 1)

    def test_post_request(self):
        self.login("SuperAdmin")
        headers = {"Content-Type": "application/json"}
        payload = {
            "name": "User 3",
            "location_id": 1,
            "usertype_id": 1,
            "email": "something@email.com",
        }
        self.client.post("/users", data=json.dumps(payload), headers=headers)
        log = Log.query.get(1)
        log_json = json.loads(log.json_data)
        self.assertTrue(log.method == 'POST')
        self.assertEqual(log_json['name'], "User 3")