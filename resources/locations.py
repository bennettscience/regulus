from typing import List
from flask import abort, jsonify, request
from flask.views import MethodView
from webargs import fields, validate
from webargs.flaskparser import parser

from app.models import Location
from app.schemas import LocationCourseSchema, LocationSchema, LocationUserSchema


class LocationListAPI(MethodView):
    def get(self: None) -> List[Location]:
        """Get a list of all locations

        Returns:
            List[Location]: List of <Location> as JSON.
        """
        locations = Location.query.all()
        return jsonify(LocationSchema(many=True).dump(locations))

    def post(self: None) -> Location:
        """Create a new Location

        Returns:
            Location: <Location> as JSON.
        """
        args = parser.parse(LocationSchema(), location="json")
        try:
            location = Location().create(Location, args)
            return jsonify(LocationSchema().dump(location))
        except Exception as e:
            return jsonify(e)


class LocationAPI(MethodView):
    def get(self: None, location_id: int) -> Location:
        """Get a single location

        Args:
            location_id (int): valid location ID

        Returns:
            Location: <Location> as JSON.
        """
        location = Location.query.get(location_id)
        if location is None:
            abort(404)

        return jsonify(LocationSchema().dump(location))


class LocationUsersAPI(MethodView):
    def get(self: None, location_id: int) -> List["User"]:
        """Get a list of users at a single location.

        Returns:
            List[User]: List of <User> for the location.
        """
        location = Location.query.get(location_id)
        if location is None:
            abort(404)

        return jsonify(LocationUserSchema(many=True).dump(location.users))


class LocationCoursesAPI(MethodView):
    def get(self: None, location_id: int) -> List["Course"]:
        """Get a list of events at a single location.

        Returns:
            List[Course]: list of <Course> at the location.
        """
        location = Location.query.get(location_id)
        if location is None:
            abort(404)
        return jsonify(LocationCourseSchema(many=True).dump(location.courses))
