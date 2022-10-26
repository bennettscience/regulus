from typing import List
from flask import Blueprint, render_template, request
from flask_login import current_user

from app.utils import get_user_navigation
from app.wrappers import restricted

home_bp = Blueprint("home_bp", __name__)


@home_bp.get("/")
def index():
    if current_user.is_anonymous:
        return render_template("auth/login.html")
    else:
        nav_items = get_user_navigation()

        if request.headers.get("HX-Request"):
            return render_template("home/index-partial.html", menuitems=nav_items)
        else:
            return render_template("home/index.html", menuitems=nav_items)


@home_bp.get("/create")
@restricted
def create():
    from app.models import CourseType, Location
    from app.schemas import CourseTypeSchema, LocationSchema

    if request.headers.get("HX-Request"):
        template = "admin/forms/create-form-partial.html"
    else:
        template = "admin/forms/create-form-full.html"

    nav_items = get_user_navigation()
    course_types = CourseType.query.all()
    locations = sorted(Location.query.all())

    content = {
        "course_types": CourseTypeSchema(many=True).dump(course_types),
        "locations": LocationSchema(many=True).dump(locations),
        "menuitems": nav_items,
    }

    return render_template(template, **content)
