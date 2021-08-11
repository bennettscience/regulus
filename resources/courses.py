import json
from datetime import datetime
from typing import List

from flask import abort, jsonify, request
from flask.views import MethodView
from flask_login import current_user
from webargs.flaskparser import parser

from app import db

from config import Config

from app.calendar import CalendarService
from app.models import Course, CourseType, CourseUserAttended, User
from app.schemas import (
    CourseAttendingSchema,
    CoursePresenterSchema,
    CourseSchema,
    CourseTypeSchema,
    NewCourseSchema,
    PublicCourseSchema,
    UserAttended,
    UserSchema,
)

course_schema = CourseSchema()
courses_schema = CourseSchema(many=True)
course_attending_schema = CourseAttendingSchema(many=True)
presenter_schema = CoursePresenterSchema()
presenters_schema = CoursePresenterSchema(many=True)
user_schema = UserSchema()
users_schema = UserSchema(many=True)
attended_schema = UserAttended()
attendee_schema = UserAttended(many=True)


class CourseListAPI(MethodView):
    def get(self: None) -> List[Course]:
        """Get a list of future active courses.

        Returns:
            List: List of Course objects.
        """
        now = datetime.now()
        if current_user.is_anonymous:
            abort(401)

        # This filters events down to active, future events.
        # TODO: accept arguments to filter per request rather than all.
        if current_user.usertype_id == 1:
            courses = Course.query.all()
        else:
            courses = Course.query.filter(
                Course.active == True, Course.starts >= now
            ).all()

        if len(courses) > 0:

            # calculate the remaining number of seats at request time.
            for course in courses:
                course.available = course.available_size()

            sorted_courses = sorted(courses)

            if current_user.role.name == "SuperAdmin":
                return jsonify(CourseSchema(many=True).dump(sorted_courses))
            return jsonify(PublicCourseSchema(many=True).dump(sorted_courses))
        else:
            return jsonify({"message": "No courses"})

    def post(self: None) -> Course:
        """Create a new event

        Returns:
            Course: JSON representation of the event
        """
        args = parser.parse(NewCourseSchema(), location="json")

        # Add Google Calendar event to public page. Store the event ID with the event
        calendar_id = Config.GOOGLE_CALENDAR_ID

        print(args["starts"])
        print(args["ends"])

        # Becuase this is done through a hook, the times need to be converted to JS (milliseconds)
        # instead of Python timestamps (seconds).
        starts = CalendarService().convertToISO(args["starts"])
        ends = CalendarService().convertToISO(args["ends"])
        default_presenter = current_user.id

        body = {
            "summary": args["title"],
            "description": args["description"],
            "start": {
                "dateTime": starts,
                "timeZone": "America/Indiana/Indianapolis",
            },
            "end": {
                "dateTime": ends,
                "timeZone": "America/Indiana/Indianapolis",
            },
            "attendees": [{
                "email": current_user.email,
                "responseStatus": "accepted"
            }],
        }

        # post to a webhook to handle the event creation
        import requests
        webhook_url = Config.CALENDAR_HOOK_URL

        payload = {
            "method": "post",
            "token": Config.CALENDAR_HOOK_TOKEN,
            "userId": current_user.email,
            "calendarId": Config.GOOGLE_CALENDAR_ID,
            "body": body,
        }

        response = requests.post(webhook_url, json=payload)

        # Upate the args object before posting to the database
        args["ext_calendar"] = response.json()["id"]
        args["starts"] = datetime.fromtimestamp(args["starts"])
        args["ends"] = datetime.fromtimestamp(args["ends"])

        # TODO: mutate the args into something without 'presenter' for creating the event.
        course = Course().create(Course, args)
        result = Course.query.get(course.id)

        # Add a default presenter for now
        result.presenters.append(current_user)
        db.session.add(result)
        db.session.commit()

        # print(args['presenters'])

        # Now that the course exists, the default presenter can be added.
        # result.presenters.append(args['presenter'])

        # dump the entire course record for the admin
        return jsonify(CourseSchema().dump(result))


class CourseAPI(MethodView):
    def get(self: None, course_id: int) -> Course:
        """Get a single event

        Args:
            course_id (int): valid event ID

        Returns:
            Course: JSON representation of event
        """
        course = Course.query.get(course_id)
        if course is None:
            abort(404)

        if current_user.role.name == "SuperAdmin":
            return jsonify(CourseSchema().dump(course))

        # TODO: Do we need a different version of the object?
        return jsonify(PublicCourseSchema().dump(course))

    def put(self: None, course_id: int) -> Course:
        """Update details for an event

        Args:
            course_id (int): valid event ID

        Returns:
            Course: JSON representation of the updated event
        """
        import requests
        args = parser.parse(CourseSchema(), location="json")
        course = Course.query.get(course_id)
        calendar_id = Config.GOOGLE_CALENDAR_ID
        webhook_url = Config.CALENDAR_HOOK_URL

        if course is None:
            abort(404)
        try:
            course.update(args)
            if "starts" in args or "ends" in args:
                if "starts" in args:
                    starts = CalendarService().convertToISO(
                        datetime.timestamp(args["starts"])
                    )
                if "ends" in args:
                    ends = CalendarService().convertToISO(
                        datetime.timestamp(args["ends"])
                    )

                service = CalendarService().build()

                body = {
                    "start": {
                        "dateTime": (starts * 1000),
                        "timeZone": "America/Indiana/Indianapolis",
                    },
                    "end": {
                        "dateTime": (ends * 1000),
                        "timeZone": "America/Indiana/Indianapolis",
                    },
                }

                payload = {
                    "method": "put",
                    "token": Config.CALENDAR_HOOK_TOKEN,
                    "eventId": course.ext_calendar,
                    "calendarId": calendar_id,
                    "body": body,
                }

                response = requests.post(webhook_url, json=body)

            return (
                jsonify({"message": "success", "course": CourseSchema().dump(course)}),
                200,
            )
        except Exception as e:
            return jsonify(e)

    def delete(self: None, course_id: int) -> dict:
        """Remove an event

        Args:
            course_id (int): valid event ID

        Returns:
            dict: Status of the removal as an error or success message.
        """
        import requests
        webhook_url = Config.CALENDAR_HOOK_URL
        calendar_id = Config.GOOGLE_CALENDAR_ID

        course = Course.query.get(course_id)
        if course is None:
            abort(404)

        payload = {
            "method": "delete",
            "token": Config.CALENDAR_HOOK_TOKEN,
            "calendarId": calendar_id,
            "eventId": course.ext_calendar,
        }

        response = requests.post(webhook_url, json=payload)
        print(response.text)

        # service.events().delete(
        #     calendarId=calendar_id, eventId=course.ext_calendar, sendUpdates="all"
        # ).execute()

        db.session.delete(course)
        db.session.commit()

        return {"message": "Course successfully deleted"}


class CourseTypesAPI(MethodView):
    def get(self: None) -> List[CourseType]:
        """Get all coursetypes

        Returns:
            List[CourseType]: List of <CourseType> as JSON
        """
        course_types = CourseType.query.all()
        print(CourseTypeSchema(many=True).dump(course_types))
        return jsonify(CourseTypeSchema(many=True).dump(course_types))

    def post(self: None) -> CourseType:
        """Create a new CourseType in the database

        Returns:
            CourseType: <CourseType> as JSON
        """
        args = parser.parse(CourseTypeSchema(), location="json")
        try:
            course_type = CourseType().create(CourseType, args)
            result = CourseType.query.get(course_type.id)
            return jsonify(CourseTypeSchema().dump(result))
        except Exception as e:
            return jsonify(e)


class CourseTypeAPI(MethodView):
    def get(self: None, coursetype_id: int) -> CourseType:
        course_type = CourseType.query.get(coursetype_id)
        if course_type is None:
            abort(404)

        return jsonify(CourseTypeSchema().dump(course_type))

    def put(self: None, coursetype_id: int) -> CourseType:
        """Update details for a single CourseType

        Args:
            coursetype_id (int): valid course type ID

        Returns:
            CourseType: <CourseType> as JSON.
        """
        args = parser.parse(CourseTypeSchema(), location="json")
        course_type = CourseType.query.get(coursetype_id)
        if course_type is None:
            abort(404)

        try:
            course_type.update(args)
            return jsonify(CourseTypeSchema().dump(course_type))
        except Exception as e:
            return jsonify(e)

    def delete(self: None, coursetype_id: int) -> dict:
        """Delete a course type.

        Args:
            coursetype_id (int): valid course type ID

        Returns:
            dict: Status of the deletion
        """
        course_type = CourseType.query.get(coursetype_id)
        if course_type is None:
            abort(404)

        db.session.delete(course_type)
        db.session.commit()

        return jsonify({"message": "Successfully deleted course type."})


class CoursePresentersAPI(MethodView):
    def get(self: None, course_id: int) -> list:
        """Get all presenters for an event

        Args:
            id int: valid event id

        Returns:
            list: <User>
        """
        presenters = Course.query.get(course_id).presenters
        if presenters is None:
            abort(404)

        return jsonify(CoursePresenterSchema(many=True).dump(presenters))

    def post(self: None, course_id: int, *args: list) -> List[User]:
        """Bulk add presenter(s) to an event. Accepts a list of any length.

        Args:
            course_id (int): course id
            user_ids[] (list): list of user IDs

        Returns:
            list: event presenters
        """
        args = request.get_json()
        if type(args["user_ids"]) is not list:
            return jsonify({"messages": "Expected an array of user_id"}), 422

        course = Course.query.get(course_id)

        if course is None:
            abort(404)

        for user_id in args["user_ids"]:
            user = User.query.get(user_id)
            if user is not None:

                # Update the user to a presenter so they get the dashboard at login
                if user.usertype_id != 1 and user.usertype_id != 2:
                    user.update({"usertype_id": 2})
                course.presenters.append(user)

        db.session.commit()

        return jsonify(CoursePresenterSchema(many=True).dump(course.presenters))


class CoursePresenterAPI(MethodView):
    def post(self: None, course_id: int, user_id: int) -> List[User]:
        """Add a single user as a presenter to an event.

        Args:
            course_id (int): valid event ID.
            user_id (int): valid user ID.

        Returns:
            List[User]: Updated list of all presenters for the event.
        """
        course = Course.query.get(course_id)
        if course is None:
            abort(404)

        user = User.query.get(user_id)
        if user is None:
            abort(404)

        # Update the user to a presenter so they get the dashboard at login
        if user.usertype_id != 2 and user.usertype_id != 1:
            user.update({"usertype_id": 2})

        course.presenters.append(user)

        db.session.commit()

        return jsonify(CoursePresenterSchema().dump(course.presenters))

    def delete(self: None, course_id: int, user_id: int) -> List[User]:
        """Remove a single presenter from an event.

        Args:
            course_id (int): valid event ID
            user_id (int): valid user ID

        Returns:
            List[User]: Updated list of all presenters for the event.
        """
        course = Course.query.get(course_id)
        user = User.query.get(user_id)

        if course is None or user is None:
            abort(404)

        course.presenters.remove(user)
        db.session.commit()

        return jsonify({"message": "Deletion successful"})


class CourseAttendeesAPI(MethodView):
    def get(self: None, course_id: int) -> List[User]:
        """Get a list of event attendees

        Args:
            course_id (int): valid event ID

        Returns:
            list[User]: List of users registered for the event
        """
        course = Course.query.get(course_id)
        if course is None:
            abort(404)
        registrations = [
            {"attended": user.attended, "user": user.user}
            for user in course.registrations
        ]
        return jsonify(UserAttended(many=True).dump(registrations))

    def put(self: None, course_id: int, *args: list) -> List[User]:
        """Bulk update user attended status.

        Args:
            course_id (int): valid event ID
            user_ids[] (list): list of user_id

        Returns:
            List[User]: List of users registered for the course
        """
        course = Course.query.get(course_id)
        if course is None:
            abort(404)
        args = request.get_json()
        if type(args["user_ids"]) is not list:
            return jsonify({"messages": "Expected an array of user_id"}), 422

        if args:
            users = [
                user
                for user in course.registrations
                if user.user.id in args["user_ids"]
            ]
        else:
            users = course.registrations

        for user in users:
            user.attended = not user.attended

        db.session.commit()
        return jsonify(UserAttended(many=True).dump(course.registrations))

    def post(self: None, course_id: int, *args: list) -> List[User]:
        """Add multiple users to a course as an attendee

        Each user can have one registration record per course. This filters the user's current
        course registrations before creating a record.

        Single users can also be added at /courses/:course_id/registrations/:user_id

        Args:
            self (None): [description]
            course_id (int): [description]

        Returns:
            List[User]: [description]
        """
        args = request.get_json()
        if type(args["user_ids"]) is not list:
            return jsonify({"messages": "Expected an array of user_id"}), 422

        course = Course.query.get(course_id)
        if course is None:
            abort(404)

        # If the list is longer than the number of seats left, throw an error
        if len(args["user_ids"]) > course.available_size():
            abort(409)

        for user_id in args["user_ids"]:
            user = User.query.get(user_id)

            # TODO: Handle NoneType IDs with an error?
            # Store NoneType IDs in an array and pass them back in a note that those users are NOT registered.
            if user is not None:
                current = [course.course.id for course in user.registrations]
                if course.id not in current:
                    course.registrations.append(
                        CourseUserAttended(course_id=course.id, user_id=user.id)
                    )

        db.session.commit()

        return jsonify(UserAttended(many=True).dump(course.registrations))


class CourseAttendeeAPI(MethodView):
    def post(self: None, course_id: int, user_id: int) -> User:
        """Register a single user for a course

        Args:
            course_id (int)
            user_id (int)

        Returns:
            User: User registration
        """
        course = Course.query.get(course_id)
        user = User.query.get(user_id)
        webhook_url = Config.CALENDAR_HOOK_URL

        # Catch errors if the user or course cannot be found.
        if course is None:
            abort(404, f"No course with id <{course_id}>")
        elif user is None:
            abort(404, f"No user with id <{user_id}>")

        if course.available_size() > 0:
            course.registrations.append(
                CourseUserAttended(course_id=course.id, user_id=user.id)
            )

            # The service account can't add people directly without Domain-Wide Delegation, which is a major
            # security concern. POSTing to a private webhook will allow the PD account to manupulate
            # the Calendar directly to add/remove people.
            import requests

            raw = {
                "method": "patch",
                "token": Config.CALENDAR_HOOK_TOKEN,
                "userId": current_user.email,
                "calendarId": Config.GOOGLE_CALENDAR_ID,
                "eventId": course.ext_calendar,
            }

            response = requests.post(webhook_url, json=raw)

            db.session.commit()

        else:
            abort(409)

        user = course.registrations.filter_by(user_id=user_id).first()
        return jsonify({"message": "success", "data": UserAttended().dump(user)})

    def put(self: None, course_id: int, user_id: int) -> dict:
        """Update a single course registration for an attendee

        Args:
            course_id (int): valid event ID
            user_id (int): valid user ID

        Returns:
            dict: JSON representation of user attendance record.
        """
        course = Course.query.get(course_id)

        if course is None:
            abort(404, f"No course with id <{course_id}>")

        user = course.registrations.filter_by(user_id=user_id).first()
        if user is None:
            abort(404, f"No user with id <{user_id}> registered for this course")

        user.attended = not user.attended
        db.session.commit()

        return jsonify(UserAttended().dump(user))

    def delete(self: None, course_id: int, user_id: int) -> dict:
        """Remove a user from a course

        Args:
            course_id (int): valid event ID
            user_id (int): valid user ID

        Returns:
            dict: removal status.
        """
        course = Course.query.get(course_id)
        user = course.registrations.filter_by(user_id=user_id).first()
        webhook_url = Config.CALENDAR_HOOK_URL

        if user is None:
            abort(
                404,
                f"No user with id <{user_id}> registered for course with id <{course_id}>",
            )

        raw = {
            "method": "pop",
            "token": Config.CALENDAR_HOOK_TOKEN,
            "userId": current_user.email,
            "calendarId": Config.GOOGLE_CALENDAR_ID,
            "eventId": course.ext_calendar,
        }

        import requests

        response = requests.post(webhook_url, json=raw)

        course.registrations.remove(user)
        db.session.commit()

        return jsonify({"message": "Success"})
