from datetime import datetime
from math import ceil
from flask import abort, Blueprint, render_template, request
from flask_login import current_user
from flask_weasyprint import render_pdf, HTML

import app

from app.models import CourseUserAttended, User
from app.utils import get_user_navigation
from app.wrappers import admin_or_self

documents_bp = Blueprint('documents_bp', __name__)

@documents_bp.route("/users/<int:user_id>/documents")
@admin_or_self
def get_documents(user_id):
    if request.headers.get('HX-Request'):
        template = 'users/documents/index-partial.html'
        nav_items = None
    else:
        template = 'users/documents/index.html'
        nav_items = get_user_navigation()

    # Set the user_id to the correct value
    user = User.query.get(user_id)

    total = 0
    total_registrations = len(user.registrations.all())
    registrations = user.registrations.filter(CourseUserAttended.attended == True).all()

    for event in registrations:
        event_total = ceil((event.course.ends - event.course.starts).total_seconds() / 3600)
        total = total + event_total
        event.course.total = event_total

    content = {
        "events": registrations,
        "total": total,
        "total_registrations": total_registrations,
        "user": user,
        "menuitems": nav_items
    }
    
    return render_template(
        template, **content
    )


@documents_bp.route("/users/<int:user_id>/documents/create/")
@admin_or_self
def generate_pdf(user_id):
    events = []
    total = 0
    user = User.query.get(user_id)
    query = CourseUserAttended.query.filter_by(user_id=user_id, attended=1).all()
    for event in query:
        eventTotal = ceil((event.course.ends - event.course.starts).total_seconds() / 3600)
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

@documents_bp.route("/users/<int:user_id>/documents/create/<int:course_id>")
@admin_or_self
def generate_single_pdf(user_id, course_id):
    events = []
    total = 0
    user = User.query.get(user_id)
    event = CourseUserAttended.query.filter_by(user_id=user_id, course_id=course_id, attended=1).first()
    eventTotal = ceil((event.course.ends - event.course.starts).total_seconds() / 3600)
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
