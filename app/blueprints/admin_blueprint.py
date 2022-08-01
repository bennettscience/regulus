import html

from flask import abort, Blueprint, render_template
from flask_login import current_user
from webargs import fields
from webargs.flaskparser import parser

from app import cache
from app.models import Course, CourseLink, CourseUserAttended, Location, User, CourseLinkType
from app.schemas import CourseSchema, CourseDetailSchema, CourseLinkTypeSchema, TinyCourseSchema, UserSchema
from app.static.assets.icons import attended, close
from app.utils import object_to_select

from resources.courses import CourseAPI

course_view = CourseAPI.as_view('course_view')

admin_bp = Blueprint('admin_bp', __name__, url_prefix="/admin")

admin_bp.add_url_rule('/events/<int:course_id>', view_func=course_view, methods=["PUT"])

@cache.memoize(60)
def get_event(event_id):
    event = Course.query.get(event_id)
    event.available = event.available_size()

    return CourseSchema().dump(event)

@admin_bp.get("/events")
def index():
    args = parser.parse({
        'event_id': fields.Int(missing=False)
    }, location='querystring')

    if args['event_id']:
        template = 'admin/partials/event-detail.html'
        schema = CourseDetailSchema()
        result = Course.query.get(args['event_id'])

        result.available = result.available_size()
        result.description = html.escape(result.description)

        # Get the last registration activity
        ordered_regs = result.registrations.order_by(CourseUserAttended.created_at).all()
        if ordered_regs:
            last_reg = result.registrations.order_by(CourseUserAttended.created_at)[-1].created_at
            formatted_date = last_reg.strftime("%m/%d/%y, %I:%M %p")
        else:
            formatted_date = "-"

        # Add some calculated stats about the event
        data = [
            {
                'label': 'Registrations',
                'value': len(result.registrations.all())
            },
            {
                'label': 'Last Registration',
                'value': formatted_date
            }
        ]

        content = {
            'event': schema.dump(result),
            'data': data
        }

    else:
        schema = TinyCourseSchema(many=True)
        template = 'admin/index.html'
        
        if current_user.usertype_id == 1:
            result = Course.query.order_by(Course.starts).all()
        elif current_user.usertype_id == 2:
            result = current_user.presenting
        else:
            abort(403)

        content = {
            'events': schema.dump(result)
        }

    return render_template(template, **content)

@admin_bp.get("/events/<int:event_id>/edit")
def edit_event(event_id):
    locations = object_to_select(Location.query.all())
    event = get_event(event_id)

    if event is None:
        abort(404)

    print(locations)

    content = {
        'event': event,
        'data': {
            'locations': locations,
            'selected': event['location']['id']
        }
    }

    return render_template(
        'shared/partials/sidebar.html',
        partial='admin/forms/edit-event.html',
        **content
    )

@admin_bp.get("/events/<int:event_id>/copy")
def copy_event(event_id):
    event = get_event(event_id)

    if event is None:
        abort(404)

    return render_template(
        'shared/partials/sidebar.html',
        partial='admin/forms/duplicate-event.html',
        event=event
    )

@admin_bp.get("/events/<int:event_id>/presenters/edit")
def edit_event_presenters(event_id):
    from app.schemas import CoursePresenterSchema
    event = get_event(event_id)

    # Get a list of all available presenters
    presenters = User.query.filter(User.usertype_id == 2).all()

    # Map to a dict structure to pass to the select partial
    prepared = [{"value": user.id, "text": user.name} for user in presenters]

    content = {
        "event": event,
        "data": prepared
    }

    return render_template(
        'shared/partials/sidebar.html',
        partial='admin/forms/edit-presenters.html',
        **content
    )

@admin_bp.get("/events/<int:event_id>/links/edit")
def edit_event_links(event_id):
    event = get_event(event_id)

    linktypes = CourseLinkType.query.all()
    prepared = [{"value": linktype.id, "text": linktype.name} for linktype in linktypes]

    content = {
        "event": event,
        "data": prepared
    }

    return render_template(
        'shared/partials/sidebar.html',
        partial='admin/forms/edit-links.html',
        **content
    )

@admin_bp.get("/events/<int:event_id>/users/edit")
def edit_event_regisrations(event_id):
    # Add a user to the event manually
    event = get_event(event_id)

    # Return a list of users to register for the event
    query = User.query.order_by(User.name.asc()).all()

    content = {
        "event": {
            "title": event['title'],
            "id": event['id']
        },
        "data": UserSchema(many=True).dump(query)
    }

    return render_template(
        'shared/partials/sidebar.html',
        partial='admin/forms/edit-users.html',
        **content
    )

@admin_bp.get("/events/<int:event_id>/delete")
def delete_event(event_id):
    event = get_event(event_id)

    return render_template(
        'shared/partials/sidebar.html',
        partial='admin/forms/delete-event.html',
        event=event
    )