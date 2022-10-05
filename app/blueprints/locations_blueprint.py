from flask import Blueprint, make_response, render_template

from app.wrappers import restricted

from resources.locations import (
    LocationListAPI,
    LocationAPI,
    LocationUsersAPI,
    LocationCoursesAPI
)

locations_bp = Blueprint('locations_bp', __name__)

locations_view = LocationListAPI.as_view("locations_api")
location_view = LocationAPI.as_view("location_api")
location_user_view = LocationUsersAPI.as_view("location_user_api")
location_course_view = LocationCoursesAPI.as_view("location_courses_api")


@locations_bp.get('/locations/create')
@restricted
def create_new_location():
    response = make_response(
        render_template(
            'shared/partials/sidebar.html',
            partial='events/partials/new-location-form.html'
        )
    )
    return response

locations_bp.add_url_rule("/locations", view_func=locations_view, methods=["GET", "POST"])
locations_bp.add_url_rule(
    "/locations/<int:location_id>", view_func=location_view, methods=["GET"]
)
locations_bp.add_url_rule(
    "/locations/<int:location_id>/users", view_func=location_user_view, methods=["GET"]
)
locations_bp.add_url_rule(
    "/locations/<int:location_id>/courses",
    view_func=location_course_view,
    methods=["GET"]
)
