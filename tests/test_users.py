import json
import unittest

from flask_login.utils import login_user

from app import app, db
from app.models import Course, CourseUserAttended, Location, User, UserType


class TestUsers(unittest.TestCase):
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
        
        # Set up user roles to test with
        super_admin_user = User(name="SuperAdmin", location_id=1, usertype_id=1)
        presenter_user = User(name="Presenter", location_id=1, usertype_id=2)
        user = User(name="User", location_id=1, usertype_id=4)
        db.session.add_all([super_admin_user, presenter_user, user])
        db.session.commit()
        
        self.client = app.test_client()

        c1 = Course(title="Course 1")
        u2 = User(name="User 2", location_id=2, usertype_id=2)
        l1 = Location(name="Building 1", address="123 Main")
        l2 = Location(name="Building 2", address="999 Oak")
        ut1 = UserType(name="Type1", description="The first user type")
        ut2 = UserType(name="Type2", description="The second user type")

        db.session.add_all([c1, u2, l1, l2, ut1, ut2])
        c1.presenters.append(presenter_user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_users_as_admin(self):
        self.login("SuperAdmin")
        resp = self.client.get("/users")
        self.assertTrue(resp.status_code == 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 4)
    
    # When requesting as a non-admin, user_type is a required param, otherwise 401
    def test_get_users_as_presenter(self):
        self.login("Presenter")
        resp = self.client.get("/users")
        self.assertTrue(resp.status_code == 401)
        # self.assertIsInstance(resp.json, list)
        # self.assertEqual(len(resp.json), 2)
    
    # When requesting as a non-admin, user_type is a required param, otherwise 401
    def test_get_users_as_presenter_with_querystring(self):
        self.login("Presenter")
        resp = self.client.get("/users?user_type=2")
        self.assertTrue(resp.status_code == 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 2)
    
    # When requesting as a non-admin, user_type is a required param, otherwise 401
    def test_get_users_as_user(self):
        self.login("User")
        resp = self.client.get("/users?user_type=2")
        self.assertTrue(resp.status_code == 401)

    def test_post_user(self):
        self.login("SuperAdmin")
        headers = {"Content-Type": "application/json"}
        payload = {
            "name": "User 3",
            "location_id": 1,
            "usertype_id": 1,
            "email": "something@email.com",
        }
        resp = self.client.post("/users", data=json.dumps(payload), headers=headers)
        self.assertTrue(resp.status_code == 200)
        self.assertTrue(resp.json["name"] == "User 3")
    
    def test_post_user_non_admin(self):
        self.login("Presenter")
        headers = {"Content-Type": "application/json"}
        payload = {
            "name": "User 3",
            "location_id": 1,
            "usertype_id": 1,
            "email": "something@email.com",
        }
        resp = self.client.post("/users", data=json.dumps(payload), headers=headers)
        self.assertTrue(resp.status_code == 403)

    def test_post_bad_user(self):
        self.login("SuperAdmin")
        headers = {"Content-Type": "application/json"}
        payload = {"name": "Bad user", "location_id": 1, "usertype_id": 1}
        resp = self.client.post("/users", data=json.dumps(payload), headers=headers)
        self.assertTrue(resp.status_code == 422)
        self.assertEqual(
            resp.json["messages"]["email"][0], "Missing data for required field."
        )

    def test_get_user_as_self(self):
        self.login("User")
        resp = self.client.get("/users/3")
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "User")

    def test_get_user_as_admin(self):
        self.login("SuperAdmin")
        # request a non-self user
        resp = self.client.get("/users/3")
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "User")
    
    def test_get_user_as_presenter(self):
        self.login("Presenter")
        resp = self.client.get("/users/3")
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "User")
    
    # Users cannot see other users' information
    def test_get_user_forbidden(self):
        self.login("User")
        resp = self.client.get("/users/1")
        self.assertTrue(resp.status_code == 403)

    def test_put_user(self):
        self.login("SuperAdmin")
        headers = {"Content-Type": "application/json"}
        payload = {"name": "My new name"}
        resp = self.client.put("/users/1", data=json.dumps(payload), headers=headers)
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "My new name")
    
    # Non-superadmin users can edit themselves
    def test_put_user_self(self):
        self.login("User")
        headers = {"Content-Type": "application/json"}
        payload = {"name": "My new name"}
        resp = self.client.put("/users/3", data=json.dumps(payload), headers=headers)
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "My new name")

    def test_bad_put_user(self):
        self.login("SuperAdmin")
        headers = {"Content-Type": "application/json"}
        payload = {"flame": "My new name"}
        resp = self.client.put("/users/1", data=json.dumps(payload), headers=headers)
        self.assertTrue(resp.status_code == 422)
        self.assertEqual(resp.json["messages"]["flame"], ["Unknown field."])
    
    def test_put_user_forbidden(self):
        self.login("Presenter")
        headers = {"Content-Type": "application/json"}
        payload = {"name": "My new name"}
        resp = self.client.put("/users/1", data=json.dumps(payload), headers=headers)
        self.assertTrue(resp.status_code == 403)

    # Only superadmins can delete users
    def test_delete_user(self):
        self.login("SuperAdmin")
        user = User.query.filter(User.name == 'User 2').first()
        resp = self.client.delete(f"/users/{user.id}")
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["message"], "Delete successful.")
    
    # Non-admins cannot delete users
    def test_delete_user_forbidden_presenter(self):
        self.login("User")
        user = User.query.filter(User.name == 'User 2').first()
        resp = self.client.delete(f"/users/{user.id}")
        self.assertTrue(resp.status_code == 401)
    
    # Non-admins cannot delete users
    def test_delete_user_forbidden_user(self):
        self.login("Presenter")
        user = User.query.filter(User.name == 'User 2').first()
        resp = self.client.delete(f"/users/{user.id}")
        self.assertTrue(resp.status_code == 401)

    # superadmins cannot delete themselves
    def test_delete_user_admin(self):
        self.login("SuperAdmin")
        user = User.query.filter(User.name == "SuperAdmin").first()
        resp = self.client.delete(f"/users/{user.id}")
        self.assertTrue(resp.status_code == 403)

    # No access control on this method to test
    def test_get_user_location(self):
        self.login("SuperAdmin")
        resp = self.client.get("/users/1/locations")
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "Building 1")

    # Superadmins can change locations
    def test_post_user_location_admin(self):
        self.login("SuperAdmin")        
        headers = {"Content-Type": "application/json"}
        payload = {"location_id": 2}
        # Check a non-self user id
        resp = self.client.post(
            "users/2/locations", data=json.dumps(payload), headers=headers
        )
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "Building 2")

    # Users can change their own location
    def test_post_user_location_self(self):
        self.login("User")
        headers = {"Content-Type": "application/json"}
        payload = {"location_id": 2}
        resp = self.client.post(
            "users/3/locations", data=json.dumps(payload), headers=headers
        )
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "Building 2")

    # Superadmin test delete any location
    def test_delete_user_location(self):
        self.login("SuperAdmin")
        resp = self.client.delete("/users/2/locations")
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json, {})
    
    def test_delete_user_location_self(self):
        self.login("User")
        resp = self.client.delete("/users/3/locations")
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json, {})

    # Users can get their own registrations
    def test_user_attending(self):
        db.session.add(CourseUserAttended(course_id=1, user_id=3))
        db.session.commit()

        self.login("User")
        resp = self.client.get("/users/3/registrations")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]["attended"], False)
        self.assertEqual(resp.json[0]["course"]["title"], "Course 1")

    # Admins can get lists of attendees for any session
    def test_user_attending_admin(self):
        db.session.add(CourseUserAttended(course_id=1, user_id=3))
        db.session.commit()

        self.login("SuperAdmin")
        resp = self.client.get("/users/3/registrations")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]["attended"], False)
        self.assertEqual(resp.json[0]["course"]["title"], "Course 1")
    
    # Users can get their own list of presenting sessions
    def test_user_presenting(self):
        self.login("Presenter")
        resp = self.client.get("/users/2/presenting")
        self.assertTrue(resp.status_code == 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]["title"], "Course 1")
