import json
import os

from sqlalchemy import Table
from flask_login import current_user
from app import app, db
from app.models import Course, User, UserType
from tests.utils import captured_templates, TestBase, Loader

class TestAdminBlueprint(TestBase):

    app.config['TESTING'] = True

    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"
        app.config['TESTING'] = True
        
        db.create_all()

        self.client = app.test_client()
        
        # Load all the JSON files into a temporary db
        fixtures = [
            'courses.json',
            'course_types.json',
            'locations.json',
            'roles.json',
            'users.json'
        ]

        conn = db.engine.connect()
        metadata = db.metadata

        for filename in fixtures:
            filepath = os.path.join(app.config.get('FIXTURES_DIR'), filename)
            if os.path.exists(filepath):
                data = Loader.load(filepath)
                table = Table(data[0]['table'], metadata)
                conn.execute(table.insert(), data[0]['records'])
            else:
                raise IOError("Error loading '{0}'. File could not be found".format(filename))
            
    def tearDown(self):
        db.drop_all()
        db.session.close()

    # Just try loading the pages
    # Authorized user
    def test_authorized_admin_page(self):
        self.login('Admin')

        with captured_templates(app) as templates:
            resp = self.client.get('/admin/events')

            # Extract the template names
            names = [template['template_name'] for template in templates]

            self.assertEqual(resp.status_code, 200)
            self.assertTrue('admin/index.html' in names)
            self.assertTrue('shared/form-fields/search.html' in names)

            # The template context holds kwarg data passed to the template. For this
            # test, make sure that both courses are returned for the Admin
            for template in templates:
                if 'upcoming' in template['context']:
                    this = template['context']

                    titles = [item['title'] for item in this['upcoming']]

                    self.assertEqual(len(titles), 2)
                    self.assertTrue('Course 1' in titles)
                    self.assertTrue('Course 2' in titles)

    # Anonymous user
    def test_anonymous_user(self):
        with captured_templates(app) as templates:
            resp = self.client.get('/admin/events')
            names = [template['template_name'] for template in templates]

            self.assertEqual(resp.status_code, 401)
            self.assertTrue('shared/errors/401.html' in names)

    # Unauthorized user
    def test_unauthorized_admin_page(self):
        self.login('User')

        with captured_templates(app) as templates:
            resp = self.client.get('/admin/events')

            names = [template['template_name'] for template in templates]

            self.assertEqual(resp.status_code, 403)
            self.assertTrue('shared/errors/403.html' in names)

    def test_presenter_admin_page(self):
        self.login('Presenter')

        # Set the user as a presenter on a course first
        course = Course.query.get(2)
        user = User.query.get(2)

        course.presenters.append(user)

        with captured_templates(app) as templates:
            resp = self.client.get('/admin/events')
            names = [template['template_name'] for template in templates]

            self.assertEqual(resp.status_code, 200)
            self.assertTrue('admin/index.html' in names)

            for template in templates:
                if 'upcoming' in template['context']:
                    this = template['context']
                    titles = [item['title'] for item in this['upcoming']]

                    self.assertEqual(len(titles), 1)
                    self.assertTrue('Course 2' in titles)

    def test_get_single_event_as_admin(self):
        self.login('Admin')

        with captured_templates(app) as templates:
            resp = self.client.get('/admin/events?event_id=1')
            names = [template['template_name'] for template in templates]

            self.assertEqual(resp.status_code, 200)
            self.assertTrue('admin/event-detail.html' in names)

    # This block of tests checks the edit sidebar that pops out in the admin interface.
    # Individual actions are tested in the appropriate module (mostly course).

    # Make sure the edit event form is returned
    def test_edit_event(self):
        self.login('Admin')

        with captured_templates(app) as templates:
            resp = self.client.get('/admin/events/1/edit')
            names = [template['template_name'] for template in templates]

            self.assertTrue('admin/forms/edit-event.html' in names)

            self.assertEqual(resp.status_code, 200)

    # Test that the edit sidebar is returned.
    # Check the sidebar context for the correct event
    def test_duplicate_event(self):
        self.login('Admin')

        with captured_templates(app) as templates:
            resp = self.client.get('/admin/events/1/copy')
            names = [template['template_name'] for template in templates]

            self.assertTrue('admin/forms/duplicate-event.html')

            self.assertEqual(resp.status_code, 200)

    # Check for a streamable file
    # This does not return a template. Just check the header for an attachment.
    def test_download_registrations(self):
        self.login('Admin')

        resp = self.client.get('/admin/events/1/registrations/save')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get('Content-Disposition'), "attachment; filename=registrations.csv")

    # Test that presenters are loaded in the sidebar context
    def test_edit_presenters(self):
        self.login('Admin')

        with captured_templates(app) as templates:
            resp = self.client.get('/admin/events/1/presenters/edit')
            names = [template['template_name'] for template in templates]

            self.assertEqual(resp.status_code, 200)
            self.assertTrue('admin/forms/edit-presenters.html' in names)
            
            # Make sure the select option is actually returned
            self.assertTrue('shared/form-fields/select.html' in names)

            # Get the context to make sure users are listed
            for template in templates:
                if template['template_name'] == 'shared/form-fields/select.html':
                    context = template['context']
            
            self.assertEqual(len(context['options']), 1)

    # Test that links are loaded in the sidebar context
    def test_edit_links(self):
        self.login('Admin')

        with captured_templates(app) as templates:
            resp = self.client.get('/admin/events/1/links/edit')
            names = [template['template_name'] for template in templates]

            self.assertEqual(resp.status_code, 200)
            self.assertTrue('admin/forms/edit-links.html' in names)

    # Test user list in sidebar to update registrations
    # TODO: Get the response context and check for users
    def test_edit_users(self):
        self.login('Admin')

        with captured_templates(app) as templates:
            resp = self.client.get('/admin/events/1/users/edit')
            names = [template['template_name'] for template in templates]

            self.assertEqual(resp.status_code, 200)
            self.assertTrue('admin/forms/edit-users.html' in names)

    # Test that the confirmation dialog is returned before deleting
    def test_delete_event(self):
        self.login('Admin')

        with captured_templates(app) as templates:
            resp = self.client.get('/admin/events/1/delete')
            names = [template['template_name'] for template in templates]

            self.assertEqual(resp.status_code, 200)
            self.assertTrue('admin/forms/delete-event.html' in names)
