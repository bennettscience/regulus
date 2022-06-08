from flask import Blueprint, render_template
from webargs import fields
from webargs.flaskparser import parser

from app.static.assets.icons import attended, close
from app.models import Course
from app.schemas import CourseSchema, CourseDetailSchema

admin_bp = Blueprint('admin_bp', __name__, url_prefix="/admin")

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
        result = sorted(Course.query.all())
        template = 'admin/index.html'

        content = {
            'events': schema.dump(result)
        }

    return render_template(template, **content)
