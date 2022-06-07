from flask import Blueprint
from app import app, db

from resources.users import (
    UserAPI,
    UserAttendingAPI,
    UserListAPI,
    UserLocationAPI,
    UserPresentingAPI,
    UserConfirmedAPI
)

users_bp = Blueprint('users_bp', __name__)

users_view = UserListAPI.as_view("users_api")
user_view = UserAPI.as_view("user_api")
user_location_view = UserLocationAPI.as_view("user_location_api")
user_attending_view = UserAttendingAPI.as_view("user_attending_api")
user_confirmed_view = UserConfirmedAPI.as_view("user_confirmed_api")
user_presenting_view = UserPresentingAPI.as_view("user_presenting_api")

users_bp.add_url_rule("/users", view_func=users_view, methods=["GET", "POST"])

users_bp.add_url_rule(
    "/users/<int:user_id>", view_func=user_view, methods=["GET", "PUT", "DELETE"]
)
users_bp.add_url_rule(
    "/users/<int:user_id>/locations",
    view_func=user_location_view,
    methods=["GET", "POST", "DELETE"],
)
users_bp.add_url_rule(
    "/users/<int:user_id>/registrations", view_func=user_attending_view, methods=["GET"]
)
users_bp.add_url_rule(
    "/users/<int:user_id>/confirmed", view_func=user_confirmed_view, methods=["GET"]
)
users_bp.add_url_rule(
    "/users/<int:user_id>/presenting", view_func=user_presenting_view, methods=["GET"]
)