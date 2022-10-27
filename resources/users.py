import json
from math import ceil

from flask import jsonify, request, abort, make_response, render_template
from flask.views import MethodView
from flask_login import current_user
from typing import List
from webargs import fields, validate
from webargs.flaskparser import parser, use_args, use_kwargs

from app import db

from app.static.assets.icons import attended, registered
from app.wrappers import admin_only, admin_or_self
from app.models import Course, CourseUserAttended, Location, User
from app.schemas import (
    CourseSchema,
    NewUserLocation,
    NewUserSchema,
    SmallCourseSchema,
    UserAttendingSchema,
    UserLocationSchema,
    UserSchema,
)
from app.utils import get_user_navigation


class UserAPI(MethodView):
    @admin_or_self
    def get(self: None, user_id: int) -> User:
        """Get a single user

        Args:
            user_id (int): valid user ID

        Returns:
            User: JSON representation of the user.
        """
        options = [
            {"value": location.id, "text": location.name}
            for location in Location.query.all()
        ]
        user = User.query.get(user_id)

        content = {
            "data": options,
            "user": user,
        }
        return render_template(
            "shared/partials/sidebar.html",
            partial="users/partials/user-edit-account-form.html",
            **content
        )

    @admin_or_self
    def put(self: None, user_id: int) -> User:
        """Update a user's details

        Args:
            user_id (int): valid user ID

        Returns:
            User: updated user as JSON
        """
        # Validate the fields coming from the user
        required = {
            "name": fields.Str(),
            "location_id": fields.Int(),
            "usertype_id": fields.Int(),
        }
        # Limit this to SuperAdmins or the user making the request.
        if current_user.usertype_id == 1 or current_user.id == user_id:
            args = parser.parse(required, location="form")

            user = User.query.get(user_id)
            if user is None:
                abort(404)

            try:
                user.update(args)
                response = make_response("ok")
                response.headers.set(
                    "HX-Trigger",
                    json.dumps({"showToast": "Successfully updated the user."}),
                )
                return response
                # return jsonify(UserSchema().dump(user))
            except Exception as e:
                return jsonify(e)
        else:
            abort(403)

    @admin_only
    def delete(self: None, user_id: int) -> dict:
        """Delete a user.

        Deletion will cascade through the database and remove their records
        of attendance, registrations, and presentations. Be careful.

        Args:
            user_id (int): valid user ID

        Returns:
            dict: status of the deletion.
        """
        user = User.query.get(user_id)

        if user is None:
            abort(404)

        if user == current_user:
            abort(403)

        try:
            db.session.delete(user)
            db.session.commit()

            return jsonify({"message": "Delete successful."})
        except Exception as e:
            return jsonify(e)


class UserLocationAPI(MethodView):
    def get(self: None, user_id: int) -> User:
        """Get a user's location

        Args:
            user_id (int): valid user ID

        Returns:
            User: user location as JSON
        """
        user = User.query.get(user_id)
        if user is None:
            abort(404)

        return jsonify(UserLocationSchema().dump(user.location))

    @admin_or_self
    def post(self: None, user_id: int) -> User:
        """Update a user's location

        Args:
            user_id (int): valid user ID

        Returns:
            User: Updated user location as JSON
        """
        args = parser.parse(NewUserLocation(), location="form")

        user = User.query.get(user_id)
        if user is None:
            abort(404)

        try:
            user.update(args)
            return jsonify(UserLocationSchema().dump(user.location))
        except Exception as e:
            return jsonify(e)

    @admin_or_self
    def delete(self: None, user_id: int) -> User:
        """Delete a user's location

        Args:
            user_id (int): valid user ID

        Returns:
            User: User as JSON
        """
        user = User.query.get(user_id)
        if user is None:
            abort(404)

        user.location = None
        db.session.commit()

        return jsonify(UserLocationSchema().dump(user.location))


class UserAttendingAPI(MethodView):
    @admin_or_self
    def get(self: None, user_id: int) -> List[Course]:
        """Get events where user is listed as an attendee.

        Args:
            user_id (int): valid user ID

        Returns:
            List[Course]: list of courses
        """
        # Note to future Brian: using `is` works for low integers, not for large.

        user = User.query.get(user_id)
        if user is None:
            abort(404)

        if request.headers.get("HX-Request"):
            template = "registrations/index-partial.html"
        else:
            template = "registrations/index.html"

        registrations = user.registrations.all()

        for reg in registrations:
            reg.course.available = reg.course.available_size()
            if reg.attended:
                reg.course.state = "attended"
                reg.course.icon = attended
            elif current_user.is_enrolled(reg.course) and not reg.attended:
                reg.course.state = "registered"
                reg.course.icon = registered
            else:
                reg.course.state = "available"

        sorted_regs = sorted([reg.course for reg in registrations], reverse=True)

        return render_template(
            template,
            events=SmallCourseSchema(many=True).dump(sorted_regs),
        )


class UserConfirmedAPI(MethodView):
    # Return only _confirmed_ courses for a user
    def get(self: None, user_id: int) -> List[Course]:
        """Get a list of sessions for which the user's attendance has been confirmed.

        Args:
            user_id (int): User ID

        Returns:
            List[Course]: List of <Course> objects as JSON
        """
        if (
            user_id == current_user.id
            or current_user.usertype_id == 1
            or current_user.usertype_id == 2
        ):
            confirmed = CourseUserAttended.query.filter_by(
                user_id=user_id, attended=1
            ).all()
            if confirmed is None:
                abort(404)

            for event in confirmed:
                event.course.total = ceil(
                    (event.course.ends - event.course.starts).total_seconds() / 3600
                )

            return jsonify(UserAttendingSchema(many=True).dump(confirmed))
        else:
            abort(403)


class UserPresentingAPI(MethodView):
    # Show courses a user is presenting
    @admin_or_self
    def get(self: None, user_id: int) -> List[Course]:
        """Return a list of Courses where the user_id is listed as a presenter.

        Args:
            user_id (int): User ID

        Returns:
            List[Course]: List of <Course> objects as JSON
        """
        user = User.query.get(user_id)
        if user is None:
            abort(404)

        return jsonify(CourseSchema(many=True).dump(user.presenting))
