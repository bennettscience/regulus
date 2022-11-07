import json
from typing import List

from flask import abort, jsonify
from flask.views import MethodView
from webargs.flaskparser import parser

from app.extensions import db
from app.models import CourseLinkType
from app.schemas import CourseLinkTypeSchema, NewCourseLinkTypeSchema
from app.wrappers import admin_only, restricted


class CourseLinkTypesAPI(MethodView):
    def get(self: None) -> List[CourseLinkType]:
        """Get a list of all link types.

        Returns:
            List[CourseLinkType]: List of link types.
        """
        links = CourseLinkType.query.all()
        return jsonify(CourseLinkTypeSchema(many=True).dump(links))

    @restricted
    def post(self: None) -> CourseLinkType:
        """Create a new link type

        Returns:
            CourseLinkType: <CourseLinkType> as JSON.
        """
        args = parser.parse(NewCourseLinkTypeSchema, location="json")
        try:
            link = CourseLinkType().create(CourseLinkType, args)
            return jsonify(CourseLinkTypeSchema().dump(link))
        except Exception as e:
            return jsonify(e)


class CourseLinkTypeAPI(MethodView):
    @restricted
    def get(self: None, linktype_id: int) -> CourseLinkType:
        """Get a single link type.

        Args:
            linktype_id (int): valid link type ID

        Returns:
            CourseLinkType: <CourseLink> as JSON.
        """
        link = CourseLinkType.query.get(linktype_id)

        if link is None:
            abort(404)

        return jsonify(CourseLinkTypeSchema().dump(link))

    @restricted
    def put(self: None, linktype_id: int) -> CourseLinkType:
        """Edit a single link type.

        Args:
            linktype_id (int): valid link type ID.

        Returns:
            CourseLinkType: Updated <CourseLink> as JSON.
        """
        args = parser.parse(CourseLinkTypeSchema, location="json")
        link = CourseLinkType.query.get(linktype_id)

        if link is None:
            abort(404)

        try:
            link.update(args)
            return jsonify(CourseLinkTypeSchema().dump(link))
        except Exception as e:
            return jsonify(e)

    @admin_only
    def delete(self: None, linktype_id: int) -> dict:
        """Delete a link type.

        Args:
            linktype_id (int): valid link type ID

        Returns:
            dict: Status of deletion.
        """
        link = CourseLinkType.query.get(linktype_id)
        if link is None:
            abort(404)

        db.session.delete(link)
        db.session.commit()

        return jsonify({"message": "Link type successfully deleted"})
