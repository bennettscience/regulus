from datetime import datetime
import requests

from flask import (
    Flask,
    jsonify,
    make_response,
    redirect,
    render_template,
    request
)

from flask_login import (
    LoginManager,
    current_user,
    login_user,
    logout_user,
)

from flask_caching import Cache
from flask_cors import CORS
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
cors = CORS(app, resources={r"/courses": {"origins": "*"}})
# toolbar = DebugToolbarExtension(app)
jinja_partials.register_extensions(app)

# TODO: Check all sensititve API routes for access control logic.
from app import app, db
from app.logging import create_log
from app.auth import OAuthSignIn
from app.models import Course, User, Log
from resources.courselinktypes import CourseLinkTypeAPI, CourseLinkTypesAPI
from resources.courses import CourseTypeAPI

from resources.usertypes import UserTypesAPI
from app.schemas import UserSchema, LogSchema, TinyCourseSchema

# from app.blueprints import users_blueprint
from app.blueprints.admin_blueprint import admin_bp
from app.blueprints.documents_blueprint import documents_bp
from app.blueprints.events_blueprint import events_bp
from app.blueprints.home_blueprint import home_bp
from app.blueprints.locations_blueprint import locations_bp
from app.blueprints.users_blueprint import users_bp

from app.errors import forbidden, page_not_found


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

app.register_error_handler(403, forbidden)
app.register_error_handler(404, page_not_found)

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

@app.route('/resource-query')
@cache.cached(timeout=120)
def update():
    today = datetime.now()

    # Get the blog post and youtube video
    blog_post = get_blog_post()
    # youtube_video = get_youtube_video()

    # if (today - blog_post['published_at']) < (today - youtube_video['published_at']):
    #     resource = blog_post
    # else:
    #     resource = youtube_video

    return jsonify(**blog_post)

def get_blog_post():
    headers = {
        'Authorization': 'Bearer ' + app.config['BLOG_AUTH_TOKEN']
    }

    response = requests.get(
        'https://blog.elkhart.k12.in.us/wp-json/wp/v2/posts?per_page=1&order=desc&_embed', 
        headers=headers
    ).json()[0]
    
    return {
        "published_at": datetime.strptime(response['date'], '%Y-%m-%dT%H:%M:%S'),
        "link": response['link'],
        "thumbnail": response['_embedded']['wp:featuredmedia'][0]['source_url'],
        "title": response['title']['rendered']
    }

def get_youtube_video():
    yt_request = requests.get('https://youtube.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=UUgwJ38NKsSVTBW_yzw8n1eQ&sort=desc&maxResults=1&key=AIzaSyBQxyTw84mwp5yUiGq5FDPlw1K-UvAcsq8').json()
    breakpoint()
    response = yt_request['items'][0]['snippet']
    return {
        "published_at": datetime.strptime(response['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'),
        "link": f"https://youtube.com/watch?v={response['resourceId']['videoId']}",
        "thumbnail": response['thumbnails']['standard']['url'],
        "title": response['title']
    }
