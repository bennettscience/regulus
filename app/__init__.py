import click
from flask import Flask

from flask_login import current_user

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from config import Config
from app.extensions import cache, cors, db, partials, lm, migrate


def traces_sampler(sampling_context):
    # wsgi_environ is set by Sentry's flask integration
    # https://docs.sentry.io/platforms/python/guides/flask/configuration/sampling
    try:
        request_uri = sampling_context["wsgi_environ"]["REQUEST_URI"]
    except KeyError:
        return 0

    if request_uri in ["https://events.elkhart.k12.in.us/resource-query"]:
        return 0

    return 0.1


sentry_sdk.init(
    dsn=Config.SENTRY_DSN,
    integrations=[FlaskIntegration()],
    traces_sampler=traces_sampler,
)

from app.blueprints.admin_blueprint import admin_bp
from app.blueprints.auth_blueprint import auth_bp
from app.blueprints.courselinktype_blueprint import course_link_type_bp
from app.blueprints.documents_blueprint import documents_bp
from app.blueprints.events_blueprint import events_bp
from app.blueprints.home_blueprint import home_bp
from app.blueprints.locations_blueprint import locations_bp
from app.blueprints.users_blueprint import users_bp

from app.errors import (
    forbidden,
    handle_error,
    internal_error,
    page_not_found,
    request_conflict,
    unauthorized,
)
from app.logging import create_log

from app.models import (
    Course,
    CourseLink,
    CourseLinkType,
    CourseType,
    CourseUserAttended,
    Location,
    Log,
    User,
    UserType,
)
from app.utils import get_user_navigation


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    cache.init_app(app)
    cors.init_app(
        app,
        resources={
            r"/courses": {"origins": "chrome-extension://*"},
            r"/resource-query": {"origins": "chrome-extension://*"},
        },
    )
    db.init_app(app)
    lm.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)

    partials.register_extensions(app)

    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(course_link_type_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(locations_bp)
    app.register_blueprint(users_bp)

    app.register_error_handler(400, handle_error)
    app.register_error_handler(401, unauthorized)
    app.register_error_handler(403, forbidden)
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(409, request_conflict)
    app.register_error_handler(422, handle_error)
    app.register_error_handler(500, internal_error)

    # Logging
    @app.before_request
    def log_request():
        if not current_user.is_anonymous:
            create_log()

    @app.shell_context_processor
    def make_shell_context():
        return {
            "db": db,
            "CourseType": CourseType,
            "CourseUserAttended": CourseUserAttended,
            "CourseLinkType": CourseLinkType,
            "Location": Location,
            "UserType": UserType,
            "Course": Course,
            "CourseLink": CourseLink,
            "User": User,
            "Log": Log,
        }

    @app.cli.command("seed-location")
    @click.argument("filename")
    def seed_location(filename):
        import sys
        import csv

        if filename is None:
            print("Please provide a csv file for processing")
            sys.exit(1)

        with open(filename, "r") as file:
            reader = csv.reader(file)
            for row in reader:
                loc = Location.query.filter(Location.name == row[0]).first()
                if loc is None:
                    print("Adding {}".format(row[0]))
                    db.session.add(Location(name=row[0], address=row[2]))
                else:
                    print("Location {} already exists, updating address".format(row[0]))
                    loc.address = row[2]

        db.session.commit()
        sys.exit()

    @app.cli.command("seed-events")
    @click.argument("filename")
    def seed_events(filename):
        import sys
        import csv
        from dateutil import parser

        if filename is None:
            print("Please provide a csv file for processing")
            sys.exit(1)

        with open(filename, "r") as file:
            reader = csv.reader(file)
            for row in reader:
                print("Checking for {}...".format(row[3]))
                exists = Course.query.filter(Course.ext_calendar == row[9]).first()
                if exists is None:
                    print("{} does not exist. Creating...".format(row[3]))
                    starts = parser.parse(row[5])
                    ends = parser.parse(row[6])
                    created_at = parser.parse(row[10])
                    event = Course(
                        coursetype_id=row[0],
                        location_id=row[1],
                        course_size=row[2],
                        title=row[3],
                        description=row[4],
                        starts=starts,
                        ends=ends,
                        active=bool(row[7]),
                        occurred=bool(row[8]),
                        ext_calendar=row[9],
                        created_at=created_at,
                    )
                    db.session.add(event)
        db.session.commit()
        print("Added events successfully.")
        sys.exit()

    @app.cli.command("seed-role")
    def seed_role():
        import sys

        print("Creating all roles")
        site_roles = [
            UserType(name="SuperAdmin"),
            UserType(name="Presenter"),
            UserType(name="Observer"),
            UserType(name="User"),
        ]
        db.session.add_all(site_roles)
        db.session.commit()
        print("Successfully created all roles.")
        sys.exit()

    @app.cli.command("import-users")
    @click.argument("filename")
    def import_users(filename):
        import sys
        import csv

        if filename is None:
            print("Please provide a csv file for processing")
            sys.exit(1)

        with open(filename, "r") as file:
            reader = csv.reader(file)
            for row in reader:
                print("Checking for {}...".format(row[3]))
                exists = User.query.filter(User.email == row[0]).first()
                if exists is None:
                    print("{} does not exist. Creating...".format(row[3]))
                    location_id = row[3] or None
                    user = User(
                        email=row[0],
                        name=row[1],
                        location_id=location_id,
                        usertype_id=4,
                    )
                    db.session.add(user)
        db.session.commit()
        print("Added users successfully.")
        sys.exit()

    @app.cli.command("fix-registrations")
    @click.argument("filename")
    def fix_registrations(filename):
        # Loop through the file and append each user to the course attendees object
        # look up each user by their email
        import sys
        import csv

        if filename is None:
            print("Please provide a csv file for processing")
            sys.exit(1)

        with open(filename, "r") as file:
            reader = csv.reader(file)
            for row in reader:
                course = Course.query.filter(Course.ext_calendar == row[1]).first()
                users = row[2].split(",")
                for user in users:
                    print("Searching for {}".format(user))
                    u = User.query.filter(User.email == user).first()
                    if u is not None:
                        course.registrations.append(
                            CourseUserAttended(
                                course_id=course.id,
                                user_id=u.id,
                            )
                        )
                        db.session.commit()
                    else:
                        print("Could not find {}".format(user))

    return app


# TODO: Check all sensititve API routes for access control logic.

from app.models import User
from app.resources.courselinktypes import CourseLinkTypeAPI, CourseLinkTypesAPI
from app.resources.courses import CourseTypeAPI

from app.resources.usertypes import UserTypesAPI


course_type_view = CourseTypeAPI.as_view("course_type_api")
course_linktypes_view = CourseLinkTypesAPI.as_view("course_linktypes_api")
course_linktype_view = CourseLinkTypeAPI.as_view("course_linktype_api")


@lm.user_loader
def load_user(id):
    return User.query.get(id)


# # Request all logs for an event
# @app.route("/logs/<int:course_id>", methods=["GET"])
# def get_logs(course_id):
#     query = Log.query.filter(Log.endpoint.like(f"/courses/{course_id}/%")).all()
#     return jsonify(LogSchema(many=True).dump(query))
