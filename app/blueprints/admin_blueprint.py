import csv
import datetime as dt
import html
import pytz

# Set all time zones to Eastern for reporting
EST = pytz.timezone("US/Eastern")

from flask import abort, Blueprint, render_template, request, stream_with_context
from flask_login import current_user
from io import StringIO
from sqlalchemy import func
from webargs import fields
from webargs.flaskparser import parser
from werkzeug.wrappers import Response

from app.charts import Chart
from app.extensions import cache, db
from app.wrappers import restricted
from app.models import (
    Course,
    CourseLink,
    CourseUserAttended,
    Location,
    User,
    CourseLinkType,
    CourseType,
)
from app.schemas import (
    CourseSchema,
    CourseDetailSchema,
    CourseLinkTypeSchema,
    TinyCourseSchema,
    UserSchema,
)
from app.static.assets.icons import attended, close, left_arrow
from app.utils import get_user_navigation, object_to_select

from app.resources.courses import CourseAPI

course_view = CourseAPI.as_view("course_view")

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")

admin_bp.add_url_rule("/events/<int:course_id>", view_func=course_view, methods=["PUT"])


@cache.memoize(60)
def get_event(event_id):
    event = Course.query.get(event_id)
    event.available = event.available_size()

    return CourseSchema().dump(event)


@admin_bp.get("/events")
@restricted
def index():
    args = parser.parse(
        {"event_id": fields.Int(load_default=False)}, location="querystring"
    )

    if args["event_id"]:

        if request.headers.get("HX-Request"):
            template = "admin/partials/event-detail.html"
        else:
            template = "admin/event-detail.html"
        schema = CourseDetailSchema()
        result = Course.query.get(args["event_id"])

        result.available = result.available_size()
        result.description = html.escape(result.description)

        # Create a sparkline for the registration trends.
        # This gathers all the registrations in a list and then finds missing dates to
        # display as 0 in the chart.

        # BUG: func.DATE returns datetime.datetime as 'YYYY-MM-DD' strings, so they need
        # to be converted to datetime.date() objects before sorting on line 92
        dates = (
            db.session.query(CourseUserAttended.created_at, func.count())
            .group_by(func.DATE(CourseUserAttended.created_at))
            .filter(CourseUserAttended.course_id == args["event_id"])
            .all()
        )

        # Find the range of dates between when the course was created and today
        # If the event is in the past, stop at the event start date instead
        today = dt.datetime.today().date()
        created_at = result.created_at.date()

        if today > result.starts.date():
            last = result.starts.date()
        else:
            last = today

        # date_set = set(created_at + dt.timedelta(x) for x in range((last - created_at).days))

        # # Turn the dates_only list into set of datetime.date objects for comparison
        # dates_only = set(date[0].date() for date in dates)
        # missing = sorted(date_set - dates_only)

        # # Finally, push the results back into the original list
        # for item in missing:
        #     dates.append((dt.datetime.combine(item, dt.datetime.min.time()), 0))

        # chart = Chart(sorted(dates, key=lambda x: x[0]))
        # image = chart.sparkline()

        # Add some calculated stats about the event
        data = [
            {
                "type": "text",
                "label": "Registrations",
                "value": len(result.registrations.all()),
            }
        ]

        # Only create a chart if there are registrations to report
        if len(result.registrations.all()) > 0:
            confirmed = result.registrations.filter(
                CourseUserAttended.attended == True
            ).all()

            attendance = [
                len(confirmed),
                (len(result.registrations.all()) - len(confirmed)),
            ]

            chart = Chart(attendance, ["attended", "not attended"])
            image = chart.pie()

            data.append({"type": "image", "label": "Attendance", "value": image})

        content = {
            "event": schema.dump(result),
            "data": data,
            "icon": left_arrow,
        }

    else:
        today = dt.date.today()
        schema = TinyCourseSchema(many=True)

        if request.headers.get("HX-Request"):
            template = "admin/index-partial.html"
        else:
            template = "admin/index.html"

        if current_user.usertype_id == 1:
            upcoming = (
                Course.query.filter(Course.starts > today).order_by(Course.starts).all()
            )
            past = (
                Course.query.filter(Course.starts < today).order_by(Course.starts).all()
            )
        elif current_user.usertype_id == 2:
            upcoming = (
                current_user.presenting.filter(Course.starts > today)
                .order_by(Course.starts)
                .all()
            )
            past = (
                current_user.presenting.filter(Course.starts < today)
                .order_by(Course.starts)
                .all()
            )
        else:
            abort(403)

        # Find the number of registrations before serializing
        for result in upcoming:
            result.reg_length = len(result.registrations.all())

        for result in past:
            result.reg_length = len(result.registrations.all())

        content = {
            "past": schema.dump(past),
            "upcoming": schema.dump(upcoming),
        }

    return render_template(template, **content)


@admin_bp.get("/events/<int:event_id>/edit")
@restricted
def edit_event(event_id):
    locations = object_to_select(Location.query.all())
    types = object_to_select(CourseType.query.all())
    event = get_event(event_id)

    if event is None:
        abort(404)

    content = {
        "event": event,
        "data": {
            "locations": locations,
            "types": types,
            "location_selected": event["location"]["id"],
            "type_selected": event["type"]["id"],
        },
    }

    return render_template(
        "shared/partials/sidebar.html", partial="admin/forms/edit-event.html", **content
    )


@admin_bp.get("/events/<int:event_id>/copy")
def copy_event(event_id):
    event = get_event(event_id)

    if event is None:
        abort(404)

    return render_template(
        "shared/partials/sidebar.html",
        partial="admin/forms/duplicate-event.html",
        event=event,
    )


@admin_bp.get("/events/<int:event_id>/registrations/save")
@restricted
def get_roster(event_id):

    course = Course.query.get(event_id)
    if not course:
        abort(404)

    @stream_with_context
    def generate():
        data = StringIO()
        w = csv.writer(data)

        w.writerow(("Name", "Email", "Location", "Attended", "Created At"))
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        for reg in course.registrations.all():

            if not reg.user.location:
                location = "Not specified"
            else:
                location = reg.user.location.name

            w.writerow(
                (
                    reg.user.name,
                    reg.user.email,
                    location,
                    reg.attended,
                    reg.created_at.isoformat(),
                )
            )
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    response = Response(generate(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=registrations.csv"

    return response


@admin_bp.get("/events/<int:event_id>/presenters/edit")
@restricted
def edit_event_presenters(event_id):
    from app.schemas import CoursePresenterSchema

    event = get_event(event_id)

    # Get a list of all available presenters
    presenters = User.query.filter(User.usertype_id == 2).all()

    # Map to a dict structure to pass to the select partial
    prepared = [{"value": user.id, "text": user.name} for user in presenters]

    content = {"event": event, "data": prepared}

    return render_template(
        "shared/partials/sidebar.html",
        partial="admin/forms/edit-presenters.html",
        **content
    )


@admin_bp.get("/events/<int:event_id>/links/edit")
@restricted
def edit_event_links(event_id):
    event = get_event(event_id)

    linktypes = CourseLinkType.query.all()
    prepared = [{"value": linktype.id, "text": linktype.name} for linktype in linktypes]

    content = {"event": event, "data": prepared}

    return render_template(
        "shared/partials/sidebar.html", partial="admin/forms/edit-links.html", **content
    )


@admin_bp.get("/events/<int:event_id>/users/edit")
@restricted
def edit_event_regisrations(event_id):
    # Add a user to the event manually
    event = get_event(event_id)

    # Return a list of users to register for the event
    query = User.query.order_by(User.name.asc()).all()

    content = {
        "event": {"title": event["title"], "id": event["id"]},
        "data": UserSchema(many=True).dump(query),
    }

    return render_template(
        "shared/partials/sidebar.html", partial="admin/forms/edit-users.html", **content
    )


@admin_bp.get("/events/<int:event_id>/delete")
@restricted
def delete_event(event_id):
    event = get_event(event_id)

    return render_template(
        "shared/partials/sidebar.html",
        partial="admin/forms/delete-event.html",
        event=event,
    )
