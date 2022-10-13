import json
import html
from datetime import datetime
from typing import List

from flask import abort, current_app, jsonify, make_response, render_template, request
from flask.views import MethodView
from flask_login import current_user
from webargs import fields
from webargs.multidictproxy import MultiDictProxy
from webargs.flaskparser import parser

from app import db, cache

from config import Config

from app.calendar import CalendarService
from app.models import Course, CourseLink, CourseType, CourseUserAttended, User
from app.schemas import (
    CourseAttendingSchema,
    CourseDetailSchema,
    CoursePresenterSchema,
    CourseSchema,
    CourseTypeSchema,
    NewCourseSchema,
    SmallCourseSchema,
    TinyCourseSchema,
    UserAttended,
    UserSchema,
)
from app.static.assets.icons import (
    registered,
    attended
)
from app.utils import clean_escaped_html
from app.wrappers import admin_only, admin_or_self, restricted

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
    # @cache.cached(timeout=50, key_prefix='all_courses')
    def get(self: None) -> List[Course]:
        """Get a list of future active courses.

        Returns:
            List: List of Course objects.
        """
        args = parser.parse(
            {
                "format": fields.Str(missing=None),
                'all': fields.Bool(missing=False)
            }, location="querystring"
        )

        if args['format'] == 'json':
            now = datetime.now()
            events = Course.query.filter(Course.active == True, Course.starts >= now).order_by(Course.starts).limit(5).all()
            return jsonify(TinyCourseSchema(many=True).dump(events))
        else:
            if current_user.is_anonymous:
                abort(401)

            from app.static.assets.icons import edit
            now = datetime.now()
            
            # This filters events down to active, future events.
            # args = parser.parse({'all': fields.Bool(), 'missing': False}, location='querystring')
                
            if args['all']:
                courses = Course.query.all()
            else:
                courses = Course.query.filter(
                    Course.active == True, Course.starts >= now
                ).all()

            if len(courses) > 0:
                # calculate the remaining number of seats at request time.
                for course in courses:
                    course.available = course.available_size()

                    # Determine the current state for the user
                    if current_user.is_enrolled(course) and current_user.is_attended(course):
                        course.state = 'attended'
                        course.icon = attended
                    elif current_user.is_enrolled(course) and not current_user.is_attended(course):
                        course.state = 'registered'
                        course.icon = registered
                    else:
                        course.state = 'available'

                sorted_courses = sorted(courses)

                return render_template(
                    'events/index.html',
                    events=SmallCourseSchema(many=True).dump(sorted_courses)
                )
            else:
                return render_template('shared/partials/no-upcoming.html',
                email=current_app.config['CONTACT_EMAIL'])

    @restricted
    def post(self: None) -> Course:
        """
        Create a new event
        """
        args = parser.parse(NewCourseSchema(), location="json")

        # breakpoint()
        # Becuase this is done through a hook, the times need to be converted to JS (milliseconds)
        # instead of Python timestamps (seconds).
        starts = CalendarService().convertToISO(args["starts"])
        ends = CalendarService().convertToISO(args["ends"])

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

        # Create and attach a Google Meet if the course type is submitted as Google Meet
        # Make sure to read the course type as an integer
        if int(args['coursetype_id']) == 1:
            import uuid
            request_id = uuid.uuid1().hex

            body["conferenceData"] = {
                "createRequest": {
                    "conferenceSolutionKey": {
                        "type": "hangoutsMeet"
                    },
                    "requestId": request_id
                }
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
        args["description"] = clean_escaped_html(args["description"])

        course = Course().create(Course, args)
        result = Course.query.get(course.id)

        # Add a default presenter for now
        result.presenters.append(current_user)

        # If it's a Google Meet, add the link to th event automatically
        if 'conferenceData' in response.json():
            from app.models import CourseLinkType
            linktype_id = CourseLinkType.query.filter(CourseLinkType.name == "Google Meet").first().id
            
            link = {
                "course_id": result.id,
                "courselinktype_id": linktype_id,
                "name": "Join the Meet",
                "uri": response.json()['conferenceData']['entryPoints'][0]['uri']
            }
            course_link = CourseLink().create(CourseLink, link)
            
            result.links.append(course_link)
        
        db.session.add(result)
        db.session.commit()

        # This catches event creation when it's duplicated from another event.
        # Duplication happens on the admin page, so only return events the presenter
        # is responsible for if it's a presenter. If it's an admin, return all events.
        if request.headers.get('HX-Trigger') == "form--duplicate":
            schema = TinyCourseSchema(many=True)
            if current_user.usertype_id == 1:
                events = sorted(Course.query.all())
            elif current_user.usertype_id == 2:
                events = current_user.presenting
            else:
                abort(403)

            template = 'admin/index-partial.html'
        # If the event is created from the <Create> page, then kick the upcoming events
        # back to the user on the home page.
        else:
            now = datetime.now()
            events = Course.query.filter(
                Course.active == True, Course.starts >= now
            ).all()

            schema = SmallCourseSchema(many=True)
            template = 'home/index.html'

        response = make_response(
            render_template(template, events=schema.dump(events))
        )
        response.headers.set('HX-Trigger', json.dumps({'showToast': 'Successfully created {}'.format(course.title)}))
        response.headers.set('HX-Redirect', '/')

        return response


class CourseAPI(MethodView):
    def get(self: None, course_id: int) -> Course:
        """Get a single event

        Args:
            course_id (int): valid event ID

        Returns:
            Course: JSON representation of event
        """
        from app.static.assets.icons import (
            clock,
            edit,
            pin,
            user
        )
        course = Course.query.get(course_id)
        if course is None:
            abort(404)
        
        course.available = course.available_size()
        
        if current_user.is_enrolled(course) and current_user.is_attended(course):
            course.state = 'attended'
            course.icon = attended
        elif current_user.is_enrolled(course) and not current_user.is_attended(course):
            course.state = 'registered'
            course.icon = registered
        else:
            course.state = 'available'

        # if current_user.role.name == "SuperAdmin":
        #     return jsonify(CourseSchema().dump(course))

        icons = {
            'clock': clock,
            'pin': pin,
            'user': user,
            'edit': edit,
        }

        return render_template(
            'shared/partials/sidebar.html',
            partial='events/partials/event-details.html',
            event=CourseDetailSchema().dump(course),
            icons=icons
        )
        # return jsonify(SmallCourseSchema().dump(course))

    @restricted
    def put(self: None, course_id: int) -> Course:
        """Update details for an event

        Args:
            course_id (int): valid event ID

        Returns:
            Course: JSON representation of the updated event
        """
        import requests
        from app.static.assets.icons import left_arrow
        
        # This bug was fixable by sending everything as JSON, but I'm not sure why.
        # Sending requests through forms would result in invalid datetime objects.
        # static/js/new-event.js formats the request as JSON from the client
        args = parser.parse(CourseSchema(), location='json')

        course = Course.query.get(course_id)
        calendar_id = Config.GOOGLE_CALENDAR_ID
        webhook_url = Config.CALENDAR_HOOK_URL

        if course is None:
            abort(404)
        elif not args:
            response = make_response(
                render_template(
                    'admin/partials/event-detail.html',
                    event=CourseDetailSchema().dump(course)
                )
            )
            response.headers.set('HX-Trigger', json.dumps({'showToast': 'Nothing to update'}))
            return response
        else:

            try:
                if 'description' in args:
                    args['description'] = clean_escaped_html(args['description'])
                
                course.update(args)
                
                if "starts" in args or "ends" in args:
                    if "starts" in args:
                        starts = CalendarService().convertToISO(args["starts"])
                    if "ends" in args:
                        ends = CalendarService().convertToISO(args["ends"])

                    body = {
                        "start": {
                            "dateTime": starts,
                            "timeZone": "America/Indiana/Indianapolis",
                        },
                        "end": {
                            "dateTime": ends,
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
                    request = requests.post(webhook_url, json=payload)
                
                ordered_regs = course.registrations.order_by(CourseUserAttended.created_at).all()
                if ordered_regs:
                    last_reg = course.registrations.order_by(CourseUserAttended.created_at)[-1].created_at
                    formatted_date = last_reg.strftime("%m/%d/%y, %I:%M %p")
                else:
                    formatted_date = "-"

                # Add some calculated stats about the event
                data = [
                    {
                        'label': 'Registrations',
                        'value': len(course.registrations.all())
                    },
                    {
                        'label': 'Last Registration',
                        'value': formatted_date
                    }
                ]

                content = {
                    'event': CourseDetailSchema().dump(course),
                    'data': data,
                    'icon': left_arrow
                }
                
                response = make_response(
                    render_template(
                        'admin/partials/event-detail.html',
                        **content
                    )
                )
                response.headers.set('HX-Trigger', json.dumps({'showToast': 'Successfully updated {}'.format(course.title)}))
                return response
            
            except Exception as e:
                return jsonify(e)

    @restricted
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

        # service.events().delete(
        #     calendarId=calendar_id, eventId=course.ext_calendar, sendUpdates="all"
        # ).execute()

        db.session.delete(course)
        db.session.commit()

        schema = TinyCourseSchema(many=True)

        if current_user.usertype_id == 1:
            result = Course.query.order_by(Course.starts).all()
        elif current_user.usertype_id == 2:
            result = current_user.presenting
        else:
            abort(403)

        content = {
            'events': schema.dump(result)
        }

        response = make_response(
            render_template('admin/index.html', **content)
        )
        response.headers.set('HX-Trigger', json.dumps({'showToast': "Successfully deleted {}".format(course.title)}))

        return response


class CourseTypesAPI(MethodView):
    def get(self: None) -> List[CourseType]:
        """Get all coursetypes

        Returns:
            List[CourseType]: List of <CourseType> as JSON
        """
        course_types = CourseType.query.all()
        return jsonify(CourseTypeSchema(many=True).dump(course_types))

    @restricted
    def post(self: None) -> CourseType:
        """Create a new CourseType in the database

        # TODO: This shouldn't always be a select form, but it works for now
        Returns:
            Select form of all locations
        """
        args = parser.parse(CourseTypeSchema(), location="form")
        course_type = CourseType().create(CourseType, args)
        try:
            data = [{"value": coursetype.id, "text": coursetype.name} for coursetype in CourseType.query.all()]
            response = make_response(
                render_template(
                    'shared/form-fields/select.html',
                    name='coursetype_id',
                    options=data,
                    oob='True',
                    method='innerHTML',
                    el="#coursetype_id"
                )
            )
            response.headers.set('HX-Trigger', json.dumps({'showToast': 'Successfully added the event type.'}))
            return response
        except Exception as e:
            return jsonify(e)


class CourseTypeAPI(MethodView):
    def get(self: None, coursetype_id: int) -> CourseType:
        course_type = CourseType.query.get(coursetype_id)
        if course_type is None:
            abort(404)

        return jsonify(CourseTypeSchema().dump(course_type))

    @restricted
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

    @admin_only
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

    @restricted
    def post(self: None, course_id: int, *args: list) -> List[User]:
        """ Add a presenter to an event. Accepts a list of any length.

        Args:
            course_id (int): course ID
            user_id (int): user ID

        Returns:
            list: event presenters
        """
        args = request.form

        course = Course.query.get(course_id)

        if course is None:
            abort(404)
        
        import requests
        webhook_url = Config.CALENDAR_HOOK_URL

        user = User.query.get(args['user_id'])
        if user is not None:

            # Update the user to a presenter so they get the dashboard at login
            if user.usertype_id != 1 and user.usertype_id != 2:
                user.update({"usertype_id": 2})
            course.presenters.append(user)

            # Add the presenter to the calendar event automatically.
            raw = {
                "method": "patch",
                "token": Config.CALENDAR_HOOK_TOKEN,
                "userId": user.email,
                "calendarId": Config.GOOGLE_CALENDAR_ID,
                "eventId": course.ext_calendar,
            }

            response = requests.post(webhook_url, json=raw)

        db.session.commit()

        response = make_response(
            render_template('shared/partials/event-presenter.html', user=user, event_id=course.id)
        )
        response.headers.set('HX-Trigger', json.dumps({'showToast': 'Added {} as a presenter.'.format(user.name)}))
        return response


class CoursePresenterAPI(MethodView):
    @restricted
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

        response = make_response(
            render_template(
                'shared/partials/event-presenter.html', user=user, event_id=course.id
            )
        )
        response.headers.set('HX-Trigger', json.dumps({'showToast': 'Added {} as a presenter'.format(user.name)}))
        return response

    @restricted
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

        response = make_response("ok", 200)
        response.headers.set('HX-Trigger', json.dumps({'showToast': 'Successfully removed the presenter.'}))
        return response


class CourseAttendeesAPI(MethodView):
    @restricted
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

    @restricted
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

        users = course.registrations

        for user in users:
            user.attended = True

        db.session.commit()

        response = make_response(
            render_template(
                'admin/partials/registration-table.html',
                registrations=users
            )
        )
        response.headers.set('HX-Trigger', json.dumps({'showToast': 'All registrations updated'}))
        return response
        # return jsonify(UserAttended(many=True).dump(course.registrations))

    @restricted
    def post(self: None, course_id: int) -> List[User]:
        """Add multiple users to a course as an attendee

        Each user can have one registration record per course. This filters the user's current
        course registrations before creating a record.

        Single users can also be added at /courses/:course_id/registrations/:user_id

        Args:
            course_id (int): Event ID
            force (bool) optional: Allow a registration beyond the course_size cap
        """
        from app.static.assets.icons import left_arrow

        webhook_url = Config.CALENDAR_HOOK_URL
        args = parser.parse({"user_id": fields.List(fields.Int())}, location="form")
        override = parser.parse({"force": fields.Boolean()}, location="querystring")

        course = Course.query.get(course_id)
        if course is None:
            abort(404)

        # If the list is longer than the number of seats left, throw an error
        if len(args["user_id"]) > course.available_size() and not override['force']:
            abort(409)

        for user_id in args["user_id"]:
            user = User.query.get(user_id)

            # TODO: Handle NoneType IDs with an error?
            # Store NoneType IDs in an array and pass them back in a note that those users are NOT registered.
            if user is not None:
                current = [course.course.id for course in user.registrations]
                if course.id not in current:
                    course.registrations.append(
                        CourseUserAttended(course_id=course.id, user_id=user.id)
                    )

                import requests

                raw = {
                    "method": "patch",
                    "token": Config.CALENDAR_HOOK_TOKEN,
                    "userId": user.email,
                    "calendarId": Config.GOOGLE_CALENDAR_ID,
                    "eventId": course.ext_calendar,
                }

                requests.post(webhook_url, json=raw)

        db.session.commit()

        # Collect all the necessary info to repaint the course dashboard
        schema = CourseDetailSchema()

        course.available = course.available_size()
        course.description = html.escape(course.description)

        # Get the last registration activity
        ordered_regs = course.registrations.order_by(CourseUserAttended.created_at).all()
        if ordered_regs:
            last_reg = course.registrations.order_by(CourseUserAttended.created_at)[-1].created_at
            formatted_date = last_reg.strftime("%m/%d/%y, %I:%M %p")
        else:
            formatted_date = "-"

        # Add some calculated stats about the event
        data = [
            {
                'label': 'Registrations',
                'value': len(course.registrations.all())
            },
            {
                'label': 'Last Registration',
                'value': formatted_date
            }
        ]

        content = {
            'event': schema.dump(course),
            'data': data,
            'icon': left_arrow,
        }
        response = make_response(
            render_template('admin/partials/event-detail.html', **content)
        )
        response.headers.set('HX-Trigger', json.dumps({'showToast': 'Updated registrations successfully.'}))
        return response
        # return jsonify(UserAttended(many=True).dump(course.registrations))


class CourseAttendeeAPI(MethodView):
    def post(self: None, course_id: int) -> User:
        """Register a single user for a course

        Args:
            course_id (int)
            user_id (int)

        Returns:
            User: User registration
        """
        from app.models import UserAccommodation
        
        required_args = {
            "acc_required": fields.Bool(required=True),
            "acc_details": fields.Str()
        }

        args = parser.parse(required_args, location="form")

        course = Course.query.get(course_id)
        user = User.query.get(current_user.id)
        webhook_url = Config.CALENDAR_HOOK_URL

        # Catch errors if the user or course cannot be found.
        if course is None:
            abort(404, f"No course with id <{course_id}>")
        elif user is None:
            abort(404, f"No user with id <{current_user.id}>")
        
        if course.available_size() > 0:
            course.registrations.append(
                CourseUserAttended(course_id=course.id, user_id=user.id)
            )

        # If the accommodation param is not empty, create a new entry for this course
        # and insert it.
            if args['acc_required']:
                ua = UserAccommodation(required=args['acc_required'], note=args['acc_details'])
                db.session.add(ua)
                db.session.commit()

                course.accommodations.append(ua)

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

        course.available = course.available_size()

        # Determine the current state for the user
        if current_user.is_enrolled(course) and current_user.is_attended(course):
            course.state = 'attended'
            course.icon = attended
        elif current_user.is_enrolled(course) and not current_user.is_attended(course):
            course.state = 'registered'
            course.icon = registered
        else:
            course.state = 'available'
        
        response = make_response(render_template(
            'events/partials/event-card.html',
            event=SmallCourseSchema().dump(course)
        ))
        response.headers.set('HX-Trigger', json.dumps({'showToast': "Successfully registered for {}".format(course.title)}))

        return response

    @restricted
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

    @admin_or_self
    def delete(self: None, course_id: int) -> dict:
        """Remove a user from a course

        Args:
            course_id (int): valid event ID
            user_id (int): valid user ID

        Returns:
            dict: removal status.
        """
        course = Course.query.get(course_id)
        user = course.registrations.filter_by(user_id=current_user.id).first()
        webhook_url = Config.CALENDAR_HOOK_URL

        if user is None:
            abort(
                404,
                f"No user with id <{current_user.id}> registered for course with id <{course_id}>",
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

        # Determine the current state for the user
        if current_user.is_enrolled(course) and current_user.is_attended(course):
            course.state = 'attended'
            course.icon = attended
        elif current_user.is_enrolled(course) and not current_user.is_attended(course):
            course.state = 'registered'
            course.icon = registered
        else:
            course.state = 'available'
        
        response = make_response(render_template(
            'events/partials/event-card.html',
            event=SmallCourseSchema().dump(course)
        ))
        response.headers.set('HX-Trigger', json.dumps(
            {'showToast': "Successfully cancelled registration for {}".format(course.title)
        }))

        return response
