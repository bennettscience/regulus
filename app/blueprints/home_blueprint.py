from typing import List
from flask import Blueprint, redirect, render_template, request, session, url_for
from flask_login import current_user

from app.utils import get_user_navigation

home_bp = Blueprint('home_bp', __name__)


@home_bp.get('/')
def index():
    if current_user.is_anonymous:
        return render_template('auth/login.html')
    else:
        nav_items = get_user_navigation()
    
        if request.headers.get('HX-Request'):
            return render_template('home/index-partial.html', menuitems=nav_items)
        else:
            return render_template('home/index.html', menuitems=nav_items)

@home_bp.get('/create')
def create():
    from app.models import CourseType, Location
    from app.schemas import CourseTypeSchema, LocationSchema

    course_types = CourseType.query.all()
    locations = sorted(Location.query.all())

    content = {
        "course_types": CourseTypeSchema(many=True).dump(course_types),
        "locations": LocationSchema(many=True).dump(locations)
    }

    return render_template('admin/forms/create-form.html', **content)
