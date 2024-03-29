from flask import abort, Blueprint, render_template, request
from flask_login import current_user
from app.extensions import db
from app.models import UserType, User

from webargs import fields
from webargs.flaskparser import parser

from app.wrappers import admin_only
from app.utils import get_user_navigation

from app.resources.users import (
    UserAPI,
    UserAttendingAPI,
    UserLocationAPI,
    UserPresentingAPI,
    UserConfirmedAPI,
)
from app.resources.usertypes import UserTypesAPI

from app.schemas import UserRoleSchema, UserSchema

users_bp = Blueprint("users_bp", __name__)

user_view = UserAPI.as_view("user_api")
user_location_view = UserLocationAPI.as_view("user_location_api")
user_attending_view = UserAttendingAPI.as_view("user_attending_api")
user_confirmed_view = UserConfirmedAPI.as_view("user_confirmed_api")
user_presenting_view = UserPresentingAPI.as_view("user_presenting_api")
user_types_view = UserTypesAPI.as_view("user_types_api")


@users_bp.get("/admin/users")
@admin_only
def index():
    """Return users based on the current_user and the optional

    Returns:
        _type_: _description_
    """
    args = parser.parse(
        {"usertype_id": fields.Int(load_default=None)}, location="querystring"
    )

    usertypes = UserType.query.all()
    options = [{"value": usertype.id, "text": usertype.name} for usertype in usertypes]

    # If a usertype id is in the request query, return users for that role.
    # Otherwise, return only the select field to filter down.
    if args["usertype_id"] is not None:
        template = "users/partials/user-table-rows.html"

        if args["usertype_id"] != 0:
            query = sorted(
                User.query.filter(User.usertype_id == args["usertype_id"])
                .order_by(User.name.asc())
                .all()
            )
        else:
            query = sorted(User.query.order_by(User.name.asc()).all())

        content = {
            "users": UserSchema(many=True).dump(query),
            "options": options,
        }
    else:
        if request.headers.get("HX-Request"):
            template = "users/index-partial.html"
        else:
            template = "users/index.html"

        query = sorted(User.query.order_by(User.name.asc()).all())

        content = {
            "options": options,
            "name": "usertype_id",
            "users": UserSchema(many=True).dump(query),
        }

    return render_template(template, **content)


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

users_bp.add_url_rule("/usertypes", view_func=user_types_view, methods=["GET", "POST"])
