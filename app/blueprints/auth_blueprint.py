from flask import Blueprint, jsonify, redirect, session
from flask_login import current_user, login_user, logout_user

from app.auth import OAuthSignIn
from app.extensions import db
from app.models import User
from app.schemas import UserSchema
from app.utils import get_user_navigation

auth_bp = Blueprint("auth_bp", __name__)


# Authorization routes run on the main app instead of through a blueprint
@auth_bp.route("/authorize/<provider>")
def oauth_authorize(provider):
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@auth_bp.route("/callback")
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

    # Get the user's navigation and store it as a session variable.
    login_user(user, False)

    nav_items = get_user_navigation()
    session["navigation"] = nav_items

    return redirect("/")


@auth_bp.route("/logout")
def logout():
    logout_user()
    # Removes the user's navigation items on logout
    session.clear()
    return redirect("/")


@auth_bp.route("/getsession")
def check_session():
    if current_user.is_authenticated:
        user = User.query.get(current_user.id)
        return jsonify({"login": True, "user": UserSchema().dump(user)})
    return jsonify({"login": False})
