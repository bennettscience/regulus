from math import ceil

from flask import jsonify, request, abort, render_template
from flask.views import MethodView
from flask_login import current_user
from typing import List
from webargs import fields, validate
from webargs.flaskparser import parser, use_args, use_kwargs

from app import db

from app.static.assets.icons import attended, registered
from app.auth import admin_only
from app.models import Course, CourseUserAttended, User
from app.schemas import (
    CourseSchema,
    NewUserLocation,
    NewUserSchema,
    SmallCourseSchema,
    UserAttendingSchema,
    UserLocationSchema,
    UserSchema,
)


class UserListAPI(MethodView):
    @parser.use_kwargs({'user_type': fields.Int()}, location="querystring")
    def get(self: None, user_type=None) -> List[User]:
        """ Get a list of all users.

        Returns:
            List[User]: List of users.
        """
        # TODO: Clean this up somehow?
        if current_user.usertype_id == 4:
            abort(401)
        elif current_user.usertype_id != 1 and user_type is None:
            # abort a request from non-admins for all users
            abort(401)
        elif current_user.usertype_id < 4 and current_user.usertype_id != 1 and user_type != 1:
            # presenters, observers, and admins can request non-admins
            users = User.query.filter_by(usertype_id=user_type).all()
        elif current_user.usertype_id == 1 and user_type:
            users = User.query.filter_by(usertype_id=user_type).all()
        elif current_user.usertype_id == 1 and user_type is None:
            users = User.query.all()
        else:
            abort(422)

        # TODO: Sort users by last name
        sorted_users = sorted(users)
        return jsonify(UserSchema(many=True).dump(sorted_users))

    def post(self: None) -> User:
        """ Create a new user

        Returns:
            User: JSON representation of the user
        """
        args = parser.parse(NewUserSchema(), location="json")

        if current_user.usertype_id != 1:
            abort(403)

        try:
            user = User().create(User, args)
            result = User.query.get(user.id)
            return jsonify(UserSchema().dump(result))
        except Exception as e:
            return jsonify(e)


class UserAPI(MethodView):
    def get(self: None, user_id: int) -> User:
        """Get a single user

        Args:
            user_id (int): valid user ID

        Returns:
            User: JSON representation of the user.
        """
        # Limit this to SuperAdmin, Presenters, or the user making the request
        if current_user.usertype_id == 1 or current_user.usertype_id == 2 or user_id is current_user.id:
            user = User.query.get(user_id)
            return jsonify(UserSchema().dump(user))
        else:
            abort(403)

    def put(self: None, user_id: int) -> User:
        """ Update a user's details

        Args:
            user_id (int): valid user ID

        Returns:
            User: updated user as JSON
        """

        # Limit this to SuperAdmins or the user making the request.
        if current_user.usertype_id == 1 or current_user.id == user_id:
            args = parser.parse(UserSchema(), location="json")
            user = User.query.get(user_id)
            if user is None:
                abort(404)

            try:
                user.update(args)
                return jsonify(UserSchema().dump(user))
            except Exception as e:
                return jsonify(e)
        else:
            abort(403)

    def delete(self: None, user_id: int) -> dict:
        """ Delete a user.

        Deletion will cascade through the database and remove their records
        of attendance, registrations, and presentations. Be careful.

        Args:
            user_id (int): valid user ID

        Returns:
            dict: status of the deletion.
        """
        if current_user.usertype_id != 1:
            abort(401)
        
        if current_user.id == user_id:
            abort(403)

        args = parser.parse(UserSchema(), location="query")
        user = User.query.get(user_id)

        if user is None:
            abort(404)

        try:
            db.session.delete(user)
            db.session.commit()

            return jsonify({"message": "Delete successful."})
        except Exception as e:
            return jsonify(e)


class UserLocationAPI(MethodView):
    def get(self: None, user_id: int) -> User:
        """ Get a user's location

        Args:
            user_id (int): valid user ID

        Returns:
            User: user location as JSON
        """
        user = User.query.get(user_id)
        if user is None:
            abort(404)

        return jsonify(UserLocationSchema().dump(user.location))

    def post(self: None, user_id: int) -> User:
        """ Update a user's location

        Args:
            user_id (int): valid user ID

        Returns:
            User: Updated user location as JSON
        """
        args = parser.parse(NewUserLocation(), location="json")
        
        if current_user.id == user_id or current_user.usertype_id == 1:   
            user = User.query.get(user_id)
            if user is None:
                abort(404)

            try:
                user.update(args)
                return jsonify(UserLocationSchema().dump(user.location))
            except Exception as e:
                return jsonify(e)
        else:
            abort(403)

    def delete(self: None, user_id: int) -> User:
        """ Delete a user's location

        Args:
            user_id (int): valid user ID

        Returns:
            User: User as JSON
        """
        if current_user.id == user_id or current_user.usertype_id == 1:    
            user = User.query.get(user_id)
            if user is None:
                abort(404)

            user.location = None
            db.session.commit()

            return jsonify(UserLocationSchema().dump(user.location))
        else:
            abort(403)


class UserAttendingAPI(MethodView):
    def get(self: None, user_id: int) -> List[Course]:
        """ Get events where user is listed as an attendee.

        Args:
            user_id (int): valid user ID

        Returns:
            List[Course]: list of courses
        """
        # Note to future Brian: using `is` works for low integers, not for large.
        if current_user.usertype_id == 1 or current_user.usertype_id == 2 or user_id == current_user.id:
            user = User.query.get(user_id)
            if user is None:
                abort(404)
            
            registrations = user.registrations.all()

            for reg in registrations:
                reg.course.available = reg.course.available_size()
                if reg.attended:
                    reg.course.state = 'attended'
                    reg.course.icon = attended
                elif current_user.is_enrolled(reg.course) and not reg.attended:
                    reg.course.state = 'registered'
                    reg.course.icon = registered
                else:
                    reg.course.state = 'available'
            
            sorted_regs = sorted([reg.course for reg in registrations])

            return render_template(
                'registrations/index.html',
                events=SmallCourseSchema(many=True).dump(sorted_regs)
            )

        else:
            abort(401)


class UserConfirmedAPI(MethodView):
    # Return only _confirmed_ courses for a user
    def get(self: None, user_id: int) -> List[Course]:
        """ Get a list of sessions for which the user's attendance has been confirmed.

        Args:
            user_id (int): User ID

        Returns:
            List[Course]: List of <Course> objects as JSON
        """
        if user_id == current_user.id or current_user.usertype_id == 1 or current_user.usertype_id == 2:
            confirmed = CourseUserAttended.query.filter_by(user_id=user_id, attended=1).all()
            if confirmed is None:
                abort(404)

            for event in confirmed:
                event.course.total = ceil((event.course.ends - event.course.starts).total_seconds() / 3600)
                # event.course.total = divmod((event.course.ends - event.course.starts).total_seconds(), 3600)[0]

            return jsonify(UserAttendingSchema(many=True).dump(confirmed))
        else:
            abort(403)


class UserPresentingAPI(MethodView):
    # Show courses a user is presenting
    def get(self: None, user_id: int) -> List[Course]:
        """ Return a list of Courses where the user_id is listed as a presenter.

        Args:
            user_id (int): User ID

        Returns:
            List[Course]: List of <Course> objects as JSON
        """
        if user_id == current_user.id or current_user.usertype_id == 1:
            user = User.query.get(user_id)
            if user is None:
                abort(404)
        else:
            abort(401)
        
        return jsonify(CourseSchema(many=True).dump(user.presenting))
