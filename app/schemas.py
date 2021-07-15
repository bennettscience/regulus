from datetime import datetime
from marshmallow import INCLUDE, Schema, fields

# Override Marshmallow DateTime serilization functions
# https://stackoverflow.com/questions/60036286/flask-marshmallow-serialize-datetime-to-unix-timestamp
class DateTime(fields.DateTime):
    """
    Class extends marshmallow standard DateTime with "timestamp" format.
    """

    SERIALIZATION_FUNCS = \
        fields.DateTime.SERIALIZATION_FUNCS.copy()
    DESERIALIZATION_FUNCS = \
        fields.DateTime.DESERIALIZATION_FUNCS.copy()

    SERIALIZATION_FUNCS['timestamp'] = lambda x: int(x.timestamp()) * 1000
    DESERIALIZATION_FUNCS['timestamp'] = datetime.fromtimestamp


# Course Schemas
class CourseLocationSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str()
    address = fields.Str(missing="")
    users = fields.Nested("LocationUserSchema")
    courses = fields.Nested("LocationCourseSchema")


class CourseTypeSchema(Schema):
    id = fields.Int(dump_only=True)
    description = fields.Str()
    name = fields.Str()


class CoursePresenterSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    email = fields.Str()


class PublicCourseSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str()
    location = fields.Nested("LocationSchema")
    type = fields.Nested(CourseTypeSchema)
    description = fields.Str()
    starts = DateTime(format='timestamp')
    ends = DateTime(format='timestamp')
    presenters = fields.Nested(CoursePresenterSchema, many=True)
    links = fields.Nested("DisplayCourseLinkSchema", many=True)
    course_size = fields.Int()
    active = fields.Bool()
    available = fields.Int()


class NewCourseSchema(Schema):
    title = fields.Str(required=True)
    description = fields.Str(required=True)
    starts = fields.Float(required=True)
    ends = fields.Float(required=True)

    class Meta:
        unknown = INCLUDE


class CourseSchema(Schema):
    id = fields.Int(dump_only=True)
    created_at = DateTime(format='timestamp')
    location_id = fields.Int()
    coursetype_id = fields.Int()
    type = fields.Nested("CourseTypeSchema")
    location = fields.Nested("LocationSchema")
    course_size = fields.Int()
    title = fields.Str()
    description = fields.Str()
    starts = DateTime(format='timestamp')
    ends = DateTime(format='timestamp')
    active = fields.Bool(default=True)
    occurred = fields.Bool()
    ext_calendar = fields.Str()
    presenters = fields.Nested("CoursePresenterSchema", many=True)
    registrations = fields.Nested("UserAttended", many=True)
    links = fields.Nested("DisplayCourseLinkSchema", many=True)
    available = fields.Int()


class CourseRegistrationSchema(Schema):
    user = fields.Nested("UserAttended")


class CourseAttendingSchema(Schema):
    id = fields.Int(dump_only=True)
    starts = DateTime(format='timestamp')
    ends = DateTime(format='timestamp')
    location = fields.Nested("LocationSchema")
    title = fields.String()
    description = fields.String()
    type = fields.Nested(CourseTypeSchema)
    presenters = fields.Nested("CoursePresenterSchema", many=True)
    links = fields.Nested("DisplayCourseLinkSchema", many=True)
    total = fields.Int()
    available = fields.Int()


class NewCourseLinkSchema(Schema):
    courselinktype_id = fields.Int(required=True)
    name = fields.Str()
    uri = fields.Str(required=True)


class NewCourseLinkTypeSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str()


class CourseLinkTypeSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    description = fields.Str()


class DisplayCourseLinkSchema(Schema):
    name = fields.Str()
    uri = fields.Str()
    type = fields.Nested(CourseLinkTypeSchema)


# Location Schemas


class LocationUserSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    email = fields.Str()


class LocationCourseSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str()
    starts = fields.DateTime()


class LocationSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str()
    address = fields.Str(missing="")


# User Schemas


class NewUserSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Str(required=True)
    usertype_id = fields.Int(default=4)
    location_id = fields.Int(default=None)


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    email = fields.Str()
    location = fields.Nested(LocationSchema)
    role = fields.Nested("UserRoleSchema")


class UserAttended(Schema):
    user = fields.Nested(UserSchema)
    attended = fields.Bool()


class UserAttendingSchema(Schema):
    course = fields.Nested(CourseAttendingSchema)
    attended = fields.Bool()


class UserPresentingSchema(Schema):
    course = fields.Nested(CourseSchema)


class UserRoleSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()


class NewUserLocation(Schema):
    location_id = fields.Int(required=True)


class UserLocationSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    address = fields.Str()
