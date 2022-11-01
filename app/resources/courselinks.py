import json
from typing import List
from flask import abort, jsonify, make_response, render_template
from flask.views import MethodView
from webargs.flaskparser import parser

from app import db
from app.models import Course, CourseLink
from app.schemas import (
    DisplayCourseLinkSchema,
    NewCourseLinkSchema,
)
from app.wrappers import restricted


class CourseLinksAPI(MethodView):
    def get(self: None, course_id: int) -> List[CourseLink]:
        """Get a list of links for an event

        Args:
            course_id (int): valid event ID

        Returns:
            List[CourseLink]: List of <CourseLink> for the event.
        """
        links = Course.query.get(course_id).links
        return jsonify(DisplayCourseLinkSchema(many=True).dump(links))

    @restricted
    def post(self: None, course_id: int) -> CourseLink:
        """Create a new link to display with an event

        Args:
            course_id (int): valid event ID

        Returns:
            CourseLink: <CourseLink> as JSON.
        """
        course = Course.query.get(course_id)
        if course is None:
            abort(404)

        args = parser.parse(NewCourseLinkSchema(), location="form")
        args["course_id"] = course_id

        try:
            link = CourseLink().create(CourseLink, args)
            course.links.append(link)
            db.session.commit()
        except Exception as e:
            return jsonify(e)

        response = make_response(
            render_template(
                "shared/partials/event-link.html", link=link, event_id=course.id
            )
        )
        response.headers.set(
            "HX-Trigger", json.dumps({"showToast": "Link successfully created."})
        )
        return response


class CourseLinkAPI(MethodView):
    def get(self: None, course_id: int, link_id: int) -> CourseLink:
        """Get a single link attached to an event.

        Args:
            course_id (int): valid event ID
            link_id (int): valid link ID

        Returns:
            CourseLink: <CourseLink> as JSON.
        """
        link = CourseLink.query.filter_by(course_id=course_id, id=link_id).first()
        if link is None:
            abort(404)

        return jsonify(DisplayCourseLinkSchema().dump(link))

    @restricted
    def put(self: None, course_id: int, link_id: int) -> CourseLink:
        """Update a CourseLink

        Args:
            course_id (int): valid event ID
            link_id (int): valid link ID

        Returns:
            CourseLink: <CourseLink> as JSON.
        """
        link = CourseLink.query.filter_by(course_id=course_id, id=link_id).first()
        if link is None:
            abort(404)

        args = parser.parse(DisplayCourseLinkSchema(), location="json")

        try:
            link.update(args)
            return jsonify(DisplayCourseLinkSchema().dump(link))
        except Exception as e:
            return jsonify(e)

    @restricted
    def delete(self: None, course_id: int, link_id: int) -> dict:
        """Remove a link from an event.

        Args:
            course_id (int): valid event ID.
            link_id (int): valid link ID

        Returns:
            dict: Status of the deletion.
        """
        link = CourseLink.query.filter_by(course_id=course_id, id=link_id).first()
        if link is None:
            abort(404)

        db.session.delete(link)
        db.session.commit()

        links = Course.query.get(course_id).links
        response = make_response("Ok", 200)
        response.headers.set(
            "HX-Trigger", json.dumps({"showToast": "Link deleted successfully."})
        )

        return response
