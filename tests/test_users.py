from app.extensions import db
from tests.loader import Loader
from app.models import Course, CourseUserAttended, User
from tests.utils import TestBase, captured_templates


class TestUsers(TestBase):
    def setUp(self) -> None:
        self.app = self.create()

        # Set up the application context manually to build the database
        # and test client for requests.
        ctx = self.app.app_context()
        ctx.push()

        self.client = self.app.test_client()

        fixtures = [
            "courses.json",
            "locations.json",
            "roles.json",
            "users.json",
        ]

        # Now that we're in context, we can load the database.
        loader = Loader(self.app, db, fixtures)
        loader.load()

    def tearDown(self):
        db.drop_all()
        db.session.close()

    # Request all users as an admin
    # A missing querystring defaults to all users in the database
    def test_get_users_as_admin(self):
        self.login("Admin")

        with captured_templates(self.app) as templates:
            resp = self.client.get("/admin/users")

            self.assertEqual(resp.status_code, 200)

            names = [template["template_name"] for template in templates]
            self.assertIn("users/index.html", names)
            for template in templates:
                if template["template_name"] == "users/partials/user-table-rows":
                    context = template["context"]
                    self.assertEqual(len(context["users"]), 3)

    # request only users of a certain type
    def test_get_users_of_type(self):
        self.login("Admin")

        with captured_templates(self.app) as templates:
            resp = self.client.get("/admin/users?usertype_id=2")

            self.assertEqual(resp.status_code, 200)

            for template in templates:
                if template["template_name"] == "users/partials/user-table-row.html":
                    context = template["context"]
                    # There is only one user with that type
                    self.assertEqual(len(context["users"]), 1)

    def test_get_users_as_non_admin(self):
        self.login("Presenter")

        resp = self.client.get("/admin/users")
        self.assertEqual(resp.status_code, 403)

    # When requesting as a non-admin, user_type is a required param, otherwise 401
    # TODO: This just gets the sidebar, test the route to actually add a user
    def test_add_presenter_as_presenter(self):
        self.login("Presenter")
        resp = self.client.get("/admin/events/1/presenters/edit")
        self.assertEqual(resp.status_code, 200)

    # When requesting as a non-admin, return 403
    def test_get_users_as_user_no_type(self):
        self.login("User")
        resp = self.client.get("/admin/users")
        self.assertEqual(resp.status_code, 403)

    def test_get_user_as_self(self):
        self.login("User")
        resp = self.client.get("/users/3")
        self.assertEqual(resp.status_code, 200)

    def test_get_user_as_admin(self):
        self.login("Admin")
        # request a non-self user
        resp = self.client.get("/users/3")
        self.assertEqual(resp.status_code, 200)

    def test_get_user_as_presenter(self):
        self.login("Presenter")
        resp = self.client.get("/users/3")
        self.assertEqual(resp.status_code, 403)

    # Users cannot see other users' information
    def test_get_user_forbidden(self):
        self.login("User")
        resp = self.client.get("/users/1")
        self.assertTrue(resp.status_code == 403)

    def test_put_user(self):
        self.login("Admin")
        payload = {"name": "My new name"}

        resp = self.client.put("/users/1", data=payload)
        self.assertEqual(resp.status_code, 200)

    # Non-superadmin users can edit themselves
    def test_put_user_self(self):
        self.login("User")
        payload = {"name": "My new name"}
        resp = self.client.put("/users/3", data=payload)
        self.assertTrue(resp.status_code == 200)

    def test_bad_put_user(self):
        self.login("Admin")
        payload = {"flame": "My new name"}
        resp = self.client.put("/users/1", data=payload)
        self.assertTrue(resp.status_code == 422)

    def test_put_user_forbidden(self):
        self.login("Presenter")
        payload = {"name": "My new name"}
        resp = self.client.put("/users/1", data=payload)
        self.assertTrue(resp.status_code == 403)

    # Only superadmins can delete users
    def test_delete_user(self):
        self.login("Admin")
        user = User.query.filter(User.name == "User").first()
        resp = self.client.delete(f"/users/{user.id}")
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["message"], "Delete successful.")

    # Non-admins cannot delete users
    def test_delete_user_forbidden_presenter(self):
        self.login("User")
        user = User.query.filter(User.name == "User").first()
        resp = self.client.delete(f"/users/{user.id}")
        self.assertTrue(resp.status_code == 403)

    # Non-admins cannot delete users
    def test_delete_user_forbidden_user(self):
        self.login("Presenter")
        user = User.query.filter(User.name == "User").first()
        resp = self.client.delete(f"/users/{user.id}")
        self.assertTrue(resp.status_code == 403)

    # superadmins cannot delete themselves
    def test_delete_user_admin(self):
        self.login("Admin")
        user = User.query.filter(User.name == "Admin").first()
        resp = self.client.delete(f"/users/{user.id}")
        self.assertTrue(resp.status_code == 403)

    # No access control on this method to test
    def test_get_user_location(self):
        self.login("Admin")
        resp = self.client.get("/users/1/locations")
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "Location 1")

    # Superadmins can change user locations
    def test_post_user_location_admin(self):
        self.login("Admin")
        payload = {"location_id": 2}
        # Check a non-self user id
        resp = self.client.post("users/3/locations", data=payload)
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "Location 2")

    # Users can change their own location
    def test_post_user_location_self(self):
        self.login("User")
        payload = {"location_id": 2}
        resp = self.client.post("users/3/locations", data=payload)
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json["name"], "Location 2")

    # Superadmin can delete any location
    def test_delete_user_location(self):
        self.login("Admin")
        resp = self.client.delete("/users/2/locations")
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json, {})

    # Users can remove their own location.
    def test_delete_user_location_self(self):
        self.login("User")
        resp = self.client.delete("/users/3/locations")
        self.assertTrue(resp.status_code == 200)
        self.assertEqual(resp.json, {})

    # Users can get their own registrations
    def test_user_attending(self):
        # db.session.add(CourseUserAttended(course_id=1, user_id=3))
        course = Course.query.get(1)
        course.registrations.append(CourseUserAttended(course_id=1, user_id=3))
        db.session.commit()

        self.login("User")

        with captured_templates(self.app) as templates:
            resp = self.client.get("/users/3/registrations")
            self.assertEqual(resp.status_code, 200)

            names = [template["template_name"] for template in templates]
            self.assertIn("registrations/index.html", names)

            for template in templates:
                if template["template_name"] == "registrations/index.html":
                    context = template["context"]

                    self.assertEqual(len(context["events"]), 1)

    # Admins can get lists of attendees for any session
    def test_user_attending_admin(self):
        # db.session.add(CourseUserAttended(course_id=1, user_id=3))
        course = Course.query.get(1)
        course.registrations.append(CourseUserAttended(course_id=1, user_id=3))
        db.session.commit()

        self.login("Admin")

        with captured_templates(self.app) as templates:
            resp = self.client.get("/users/3/registrations")
            self.assertEqual(resp.status_code, 200)

            names = [template["template_name"] for template in templates]
            self.assertIn("registrations/index.html", names)

            for template in templates:
                if template["template_name"] == "registrations/index.html":
                    context = template["context"]

                    self.assertEqual(len(context["events"]), 1)

    # Users can get their own list of presenting sessions
    def test_user_presenting(self):
        course = Course.query.get(1)
        course.presenters.append(User.query.get(2))
        db.session.commit()

        self.login("Presenter")
        resp = self.client.get("/users/2/presenting")
        self.assertTrue(resp.status_code == 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 1)
        self.assertEqual(resp.json[0]["title"], "Course 1")
