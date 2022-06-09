from flask import abort, Blueprint, render_template
from webargs import fields
from webargs.flaskparser import parser

from app import cache
from app.models import Course
from app.schemas import CourseSchema, CourseDetailSchema
from app.static.assets.icons import attended, close
from app.utils import get_all_events

admin_bp = Blueprint('admin_bp', __name__, url_prefix="/admin")

# TODO: implement caching on first load
# TODO: Split DB query into it's own function?
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

        content = {
            'event': schema.dump(result),
            'attended': attended,
            'not_attended': close,
            'icons': {
                'attended': attended,
                'not_attended': close
            }
        }

    else:
        schema = CourseDetailSchema(many=True)
        result = Course.query.order_by(Course.starts).all()
        template = 'admin/index.html'

        content = {
            'events': schema.dump(result)
        }

    return render_template(template, **content)

@admin_bp.get("/events/<int:event_id>/edit")
@cache.cached()
def edit_event(event_id):
    event = Course.query.get(event_id)

    event.available = event.available_size()

    # breakpoint()

    if event is None:
        abort(404)

    return render_template(
        'shared/partials/sidebar.html',
        partial='admin/forms/edit-event.html',
        event=CourseSchema().dump(event)
    )
