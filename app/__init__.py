import json
from datetime import datetime
import re

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    send_from_directory,
    abort
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_weasyprint import render_pdf, HTML

# from authlib.integrations.flask_client import OAuth
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException

from sqlalchemy import func


from config import Config

app = Flask(__name__)
app.secret_key = "!secret"
app.config.from_object(Config)
db = SQLAlchemy(app)
ma = Marshmallow(app)
migrate = Migrate(app, db, render_as_batch=True)
lm = LoginManager(app)

# TODO: Check all sensititve API routes for access control logic.
from app import app, db, errors
from app.logging import create_log
from app.auth import OAuthSignIn, admin_only
from app.calendar import CalendarService
from app.models import CourseUserAttended, User, Course
from resources.courselinks import CourseLinkAPI, CourseLinksAPI
from resources.courselinktypes import CourseLinkTypeAPI, CourseLinkTypesAPI
from resources.courses import (
    CourseAPI,
    CourseTypesAPI,
    CourseTypeAPI,
    CourseAttendeeAPI,
    CourseAttendeesAPI,
    CourseListAPI,
    CoursePresenterAPI,
    CoursePresentersAPI,
)
from resources.locations import (
    LocationAPI,
    LocationCoursesAPI,
    LocationListAPI,
    LocationUsersAPI,
)
from resources.users import (
    UserAPI,
    UserAttendingAPI,
    UserListAPI,
    UserLocationAPI,
    UserPresentingAPI,
    UserConfirmedAPI
)
from resources.usertypes import UserTypesAPI
from app.schemas import UserSchema, CourseSchema


# Register the endpoints in Flask
# https://flask.palletsprojects.com/en/2.0.x/views/#method-views-for-apis
courses_view = CourseListAPI.as_view("courses_api")
course_view = CourseAPI.as_view("course_api")
course_types_view = CourseTypesAPI.as_view("course_types_api")
course_type_view = CourseTypeAPI.as_view("course_type_api")
course_links_view = CourseLinksAPI.as_view("course_links_api")
course_link_view = CourseLinkAPI.as_view("course_link_api")
course_linktypes_view = CourseLinkTypesAPI.as_view("course_linktypes_api")
course_linktype_view = CourseLinkTypeAPI.as_view("course_linktype_api")
course_presenters_view = CoursePresentersAPI.as_view("course_presenters_api")
course_presenter_view = CoursePresenterAPI.as_view("course_presenter_api")
course_attendees_view = CourseAttendeesAPI.as_view("course_attendees_api")
course_attendee_view = CourseAttendeeAPI.as_view("course_attendee_api")
locations_view = LocationListAPI.as_view("locations_api")
location_view = LocationAPI.as_view("location_api")
location_user_view = LocationUsersAPI.as_view("location_user_api")
location_course_view = LocationCoursesAPI.as_view("location_courses_api")
users_view = UserListAPI.as_view("users_api")
user_view = UserAPI.as_view("user_api")
user_location_view = UserLocationAPI.as_view("user_location_api")
user_attending_view = UserAttendingAPI.as_view("user_attending_api")
user_confirmed_view = UserConfirmedAPI.as_view("user_confirmed_api")
user_presenting_view = UserPresentingAPI.as_view("user_presenting_api")
user_types_view = UserTypesAPI.as_view("user_types_api")


@lm.user_loader
def load_user(id):
    return User.query.get(id)

@app.route('/')
@app.route('/schedule')
@app.route('/presenter')
@app.route('/admin')
@app.route('/create')
@app.route('/documents')
@app.route('/people')
def base():
    return send_from_directory('client/public', 'index.html')


@app.route("/<path:path>")
def home(path):
    return send_from_directory('client/public', path)


@app.route("/authorize/<provider>")
def oauth_authorize(provider):
    # redirect_uri = url_for('auth', _external=True)
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route("/callback")
def callback():
    oauth = OAuthSignIn.get_provider("google")
    token = oauth.authorize_access_token()
    received_user = oauth.parse_id_token(token)
    email = received_user["email"]
    name = received_user["name"]
    if email is None:
        return jsonify({"message": "Unable to login, email is null"})

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(name=name, email=email, usertype_id=4)
        db.session.add(user)
        db.session.commit()

    login_user(user, True)
    return redirect('/')


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")


@app.route("/getsession")
def check_session():
    if current_user.is_authenticated:
        user = User.query.get(current_user.id)
        return jsonify({"login": True, "user": UserSchema().dump(user)})
    return jsonify({"login": False})


@app.route("/data")
def get_data():
    user = User.query.get(current_user.id)
    return jsonify({"username": user.name})

@app.route("/presenters")
def get_presenters():
    presenters = User.query.join(User.role, aliased=True).filter_by(name='Presenter').all()
    return jsonify(UserSchema(many=True).dump(presenters))

@app.route("/popular")
def get_popular_course():
    # pass
    course = Course.query(func.max(Course.registrations)).one()
    return jsonify(CourseSchema().dump(course))

@app.route("/users/<int:user_id>/documents/create/")
def generate_pdf(user_id):
    events = []
    total = 0
    user = User.query.get(user_id)
    query = CourseUserAttended.query.filter_by(user_id=user_id, attended=1).all()
    for event in query:
        eventTotal = divmod((event.course.ends - event.course.starts).total_seconds(), 3600)[0]
        total = total + eventTotal
        events.append(
            {
                'title': event.course.title,
                'start': datetime.date(event.course.starts).strftime("%B %d, %Y"),
                'total': eventTotal,
            }
        )

    html = render_template('pdf.html', user=user, events=events, total=total)
    return render_pdf(HTML(string=html))

@app.route("/users/<int:user_id>/documents/create/<int:course_id>")
def generate_single_pdf(user_id, course_id):
    events = []
    total = 0
    user = User.query.get(user_id)
    query = CourseUserAttended.query.filter_by(user_id=user_id, course_id=course_id, attended=1).all()
    for event in query:
        eventTotal = divmod((event.course.ends - event.course.starts).total_seconds(), 3600)[0]
        total = total + eventTotal
        events.append(
            {
                'title': event.course.title,
                'start': datetime.date(event.course.starts).strftime("%B %d, %Y"),
                'total': eventTotal,
            }
        )

    html = render_template('pdf.html', user=user, events=events, total=total)
    return render_pdf(HTML(string=html))

# Logging
@app.before_request
def log_request():
    create_log()


# CRUD endpoints
app.add_url_rule("/courses", view_func=courses_view, methods=["GET", "POST"])
app.add_url_rule(
    "/courses/<int:course_id>", view_func=course_view, methods=["GET", "PUT", "DELETE"]
)
app.add_url_rule(
    "/courses/<int:course_id>/links",
    view_func=course_links_view,
    methods=["GET", "POST"],
)
app.add_url_rule(
    "/courses/<int:course_id>/links/<int:link_id>",
    view_func=course_link_view,
    methods=["GET", "PUT", "DELETE"],
)
app.add_url_rule(
    "/courses/<int:course_id>/presenters",
    view_func=course_presenters_view,
    methods=["GET", "POST"],
)
app.add_url_rule(
    "/courses/<int:course_id>/presenters/<int:user_id>",
    view_func=course_presenter_view,
    methods=["POST", "DELETE"],
)
app.add_url_rule(
    "/courses/<int:course_id>/registrations",
    view_func=course_attendees_view,
    methods=[
        "GET",
        "PUT",
        "POST",
    ],
)
app.add_url_rule(
    "/courses/<int:course_id>/registrations/<int:user_id>",
    view_func=course_attendee_view,
    methods=["PUT", "POST", "DELETE"],
)
app.add_url_rule(
    "/courses/types", view_func=course_types_view, methods=["GET", "POST"]
)
app.add_url_rule(
    "/courses/types/<int:coursetype_id>", view_func=course_type_view, methods=["GET", "PUT", "DELETE"]
)
app.add_url_rule(
    "/courselinktypes", view_func=course_linktypes_view, methods=["GET", "POST"]
)
app.add_url_rule(
    "/courselinktypes/<int:linktype_id>",
    view_func=course_linktype_view,
    methods=["GET", "PUT", "DELETE"],
)
app.add_url_rule("/locations", view_func=locations_view, methods=["GET", "POST"])
app.add_url_rule(
    "/locations/<int:location_id>", view_func=location_view, methods=["GET"]
)
app.add_url_rule(
    "/locations/<int:location_id>/users", view_func=location_user_view, methods=["GET"]
)
app.add_url_rule(
    "/locations/<int:location_id>/courses",
    view_func=location_course_view,
    methods=["GET"],
)

app.add_url_rule("/users", view_func=users_view, methods=["GET", "POST"])

app.add_url_rule(
    "/users/<int:user_id>", view_func=user_view, methods=["GET", "PUT", "DELETE"]
)
app.add_url_rule(
    "/users/<int:user_id>/locations",
    view_func=user_location_view,
    methods=["GET", "POST", "DELETE"],
)
app.add_url_rule(
    "/users/<int:user_id>/registrations", view_func=user_attending_view, methods=["GET"]
)
app.add_url_rule(
    "/users/<int:user_id>/confirmed", view_func=user_confirmed_view, methods=["GET"]
)
app.add_url_rule(
    "/users/<int:user_id>/presenting", view_func=user_presenting_view, methods=["GET"]
)
app.add_url_rule("/usertypes", view_func=user_types_view, methods=["GET", "POST"])
