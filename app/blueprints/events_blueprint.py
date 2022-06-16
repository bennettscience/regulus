import json
from flask import Blueprint, make_response, render_template

from resources.courselinks import CourseLinksAPI, CourseLinkAPI
from resources.courses import (
    CourseListAPI,
    CourseAPI,
    CourseAttendeesAPI,
    CourseAttendeeAPI,
    CoursePresentersAPI,
    CoursePresenterAPI,
    CourseTypesAPI
)

events_bp = Blueprint('events_bp', __name__)

courses_view = CourseListAPI.as_view("courses_api")
course_view = CourseAPI.as_view("course_api")
course_attendees_view = CourseAttendeesAPI.as_view("course_attendees_api")
course_attendee_view = CourseAttendeeAPI.as_view("course_attendee_api")
course_links_view = CourseLinksAPI.as_view("course_links_view")
course_link_view = CourseLinkAPI.as_view("course_link_view")
course_presenters_view = CoursePresentersAPI.as_view("course_presenters_view")
course_presenter_view = CoursePresenterAPI.as_view("course_presenter_view")
course_types_view = CourseTypesAPI.as_view("course_types_view")

@events_bp.get('/courses/types/create')
def new_event_type():
    response = make_response(
        render_template(
            'shared/partials/sidebar.html',
            partial='events/partials/new-type-form.html'
        )
    )
    response.headers.set('HX-Trigger', json.dumps({
            'makeQuill': {
                "placeholder": "Edit event type description",
                "element": "#editor--event"
            }
        }
    ))
    return response

events_bp.add_url_rule("/courses", view_func=courses_view, methods=["GET", "POST"])
events_bp.add_url_rule(
    "/courses/<int:course_id>", view_func=course_view, methods=["GET", "PUT", "DELETE"]
)
events_bp.add_url_rule(
    "/courses/<int:course_id>/links",
    view_func=course_links_view,
    methods=["GET", "POST"],
)
events_bp.add_url_rule(
    "/courses/<int:course_id>/links/<int:link_id>",
    view_func=course_link_view,
    methods=["GET", "PUT", "DELETE"],
)
events_bp.add_url_rule(
    "/courses/<int:course_id>/presenters",
    view_func=course_presenters_view,
    methods=["GET", "POST"],
)
events_bp.add_url_rule(
    "/courses/<int:course_id>/presenters/<int:user_id>",
    view_func=course_presenter_view,
    methods=["POST", "DELETE"],
)
events_bp.add_url_rule(
    "/courses/<int:course_id>/registrations",
    view_func=course_attendees_view,
    methods=[
        "GET",
        "PUT",
        "POST",
    ],
)
events_bp.add_url_rule(
    "/courses/<int:course_id>/register",
    view_func=course_attendee_view,
    methods=["POST", "DELETE"]
)
events_bp.add_url_rule(
    "/courses/<int:course_id>/registrations/<int:user_id>",
    view_func=course_attendee_view,
    methods=["PUT"],
)
events_bp.add_url_rule(
    "/courses/types", view_func=course_types_view, methods=["GET", "POST"]
)
# events_bp.add_url_rule(
#     "/courses/types/<int:coursetype_id>", view_func=course_type_view, methods=["GET", "PUT", "DELETE"]
# )