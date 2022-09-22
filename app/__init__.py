from flask import (
    Flask,
    jsonify,
    redirect,
)

from flask_login import (
    LoginManager,
    current_user,
    login_user,
    logout_user,
)

from flask_caching import Cache
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import jinja_partials
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from config import Config

sentry_sdk.init(
    dsn=Config.SENTRY_DSN,
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.5
)

app = Flask(__name__)
app.secret_key = "!secret"
app.config.from_object(Config)
db = SQLAlchemy(app)
ma = Marshmallow(app)
migrate = Migrate(app, db, render_as_batch=True)
lm = LoginManager(app)
cache = Cache(app)
# toolbar = DebugToolbarExtension(app)
jinja_partials.register_extensions(app)

# TODO: Check all sensititve API routes for access control logic.
from app import app, db
from app.logging import create_log
from app.auth import OAuthSignIn
from app.models import User, Log
from resources.courselinktypes import CourseLinkTypeAPI, CourseLinkTypesAPI
from resources.courses import CourseTypeAPI

from resources.usertypes import UserTypesAPI
from app.schemas import UserSchema, LogSchema

# from app.blueprints import users_blueprint
from app.blueprints.admin_blueprint import admin_bp
from app.blueprints.documents_blueprint import documents_bp
from app.blueprints.events_blueprint import events_bp
from app.blueprints.home_blueprint import home_bp
from app.blueprints.locations_blueprint import locations_bp
from app.blueprints.users_blueprint import users_bp

course_type_view = CourseTypeAPI.as_view("course_type_api")
course_linktypes_view = CourseLinkTypesAPI.as_view("course_linktypes_api")
course_linktype_view = CourseLinkTypeAPI.as_view("course_linktype_api")

user_types_view = UserTypesAPI.as_view("user_types_api")

# Register all the blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(documents_bp)
app.register_blueprint(events_bp)
app.register_blueprint(home_bp)
app.register_blueprint(locations_bp)
app.register_blueprint(users_bp)

@lm.user_loader
def load_user(id):
    return User.query.get(id)

# Authorization routes run on the main app instead of through a blueprint
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

    login_user(user, False)
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


# Logging
@app.before_request
def log_request():
    if not current_user.is_anonymous:
        create_log()

# Request all logs for an event
@app.route("/logs/<int:course_id>", methods=['GET'])
def get_logs(course_id):
    query = Log.query.filter(Log.endpoint.like(f'/courses/{course_id}/%')).all()
    return jsonify(LogSchema(many=True).dump(query))


app.add_url_rule(
    "/courselinktypes", view_func=course_linktypes_view, methods=["GET", "POST"]
)
app.add_url_rule(
    "/courselinktypes/<int:linktype_id>",
    view_func=course_linktype_view,
    methods=["GET", "PUT", "DELETE"],
)


app.add_url_rule("/usertypes", view_func=user_types_view, methods=["GET", "POST"])
