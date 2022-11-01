import json
from typing import List
from flask import abort, jsonify, make_response, render_template, request
from flask.views import MethodView
from webargs import fields, validate
from webargs.flaskparser import parser

from app.models import Location
from app.schemas import LocationCourseSchema, LocationSchema, LocationUserSchema
from app.wrappers import restricted


class LocationListAPI(MethodView):
    def get(self: None) -> List[Location]:
        """Get a list of all locations

        Returns:
            List[Location]: List of <Location> as JSON.
        """
        # Some routes only show buildings. Use a query param to filter out all
        # locations other than physical places.
        # TODO: This is brittle, relying on missing address fields. Add a field to check against?
        args = parser.parse(
            {"locationType": fields.Str(required=False)}, location="querystring"
        )
        if args and args["locationType"] == "physical":
            locations = Location.query.filter(Location.address != "").all()
        else:
            locations = Location.query.all()

        return jsonify(LocationSchema(many=True).dump(locations))

    @restricted
    def post(self: None) -> Location:
        """Create a new Location

        Returns:
            Updated <select> of all available locations
        """
        args = parser.parse(LocationSchema(), location="form")

        try:
            location = Location().create(Location, args)

            data = [
                {"value": location.id, "text": location.name}
                for location in Location.query.all()
            ]
            response = make_response(
                render_template(
                    "shared/form-fields/select.html",
                    name="location_id",
                    options=data,
                    oob="True",
                    method="innerHTML",
                    el="#location_id",
                )
            )
            response.headers.set(
                "HX-Trigger",
                json.dumps({"showToast": "Successfully added the location."}),
            )
            return response
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
    @restricted
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
