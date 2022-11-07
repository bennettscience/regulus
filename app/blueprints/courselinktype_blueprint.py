from flask import Blueprint


from app.resources.courselinktypes import CourseLinkTypeAPI, CourseLinkTypesAPI
from app.schemas import CourseLinkTypeSchema, NewCourseLinkTypeSchema

course_link_type_bp = Blueprint("course_link_type_bp", __name__)

course_link_type_view = CourseLinkTypeAPI.as_view("course_link_type_view")
course_link_types_view = CourseLinkTypesAPI.as_view("course_link_types_view")

course_link_type_bp.add_url_rule(
    "/courselinktypes", view_func=course_link_types_view, methods=["GET", "POST"]
)
course_link_type_bp.add_url_rule(
    "/courselinktypes/<int:linktype_id>",
    view_func=course_link_type_view,
    methods=["GET", "PUT", "DELETE"],
)
