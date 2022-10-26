from datetime import datetime

from app import db, lm
from flask_login import UserMixin


class Manager(object):
    def create(self, cls, data):
        item = cls(**data)
        db.session.add(item)
        db.session.commit()

        return item

    def update(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        db.session.commit()

    def delete(self):
        pass


# Many to many

course_presenters = db.Table(
    "course_presenters",
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "course_id",
        db.Integer,
        db.ForeignKey("course.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
)

user_locations = db.Table(
    "user_locations",
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "location_id",
        db.Integer,
        db.ForeignKey("location.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
)

course_locations = db.Table(
    "course_locations",
    db.Column(
        "course_id",
        db.Integer,
        db.ForeignKey("course.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "location_id",
        db.Integer,
        db.ForeignKey("location.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
)

course_accommodations = db.Table(
    "course_accommodations",
    db.Column(
        "course_id",
        db.Integer,
        db.ForeignKey("course.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "accommodation_id",
        db.Integer,
        db.ForeignKey("user_accommodation.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class CourseType(Manager, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(64))


class CourseLinkType(Manager, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(64))


class Location(Manager, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.String(255))
    address = db.Column(db.String(255))

    courses = db.relationship("Course", backref="location")
    users = db.relationship("User", backref="location")

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name


class UserType(Manager, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(255))


# One to Many tables


class Course(Manager, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    coursetype_id = db.Column(db.Integer, db.ForeignKey(CourseType.id))
    location_id = db.Column(db.Integer, db.ForeignKey(Location.id))
    course_size = db.Column(db.Integer)
    title = db.Column(db.String(64))
    description = db.Column(db.String(3000))
    starts = db.Column(db.DateTime, default=datetime.utcnow)
    ends = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    occurred = db.Column(db.Boolean, default=False)
    ext_calendar = db.Column(db.String(255), unique=True)

    type = db.relationship(CourseType, backref="course")
    links = db.relationship("CourseLink", uselist=True)
    presenters = db.relationship(
        "User",
        secondary=course_presenters,
        backref=db.backref("presenting", lazy="dynamic"),
        uselist=True,
    )
    registrations = db.relationship(
        "CourseUserAttended",
        backref="course",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    accommodations = db.relationship(
        "UserAccommodation",
        secondary=course_accommodations,
        backref="course",
        uselist=True,
    )

    # calculate the number of remaining seats
    def available_size(self):
        return self.course_size - len(self.registrations.all())

    def __eq__(self, other):
        return self.starts == other.starts

    def __lt__(self, other):
        return self.starts < other.starts


class UserAccommodation(Manager, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    required = db.Column(db.Boolean, default=False)
    note = db.Column(db.String(1500), nullable=True)


class CourseLink(Manager, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"))
    courselinktype_id = db.Column(db.Integer, db.ForeignKey("course_link_type.id"))
    name = db.Column(db.String(255))
    uri = db.Column(db.String(255))

    type = db.relationship(CourseLinkType)


class User(Manager, UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    location_id = db.Column(db.Integer, db.ForeignKey("location.id"))
    usertype_id = db.Column(db.Integer, db.ForeignKey("user_type.id"))

    role = db.relationship("UserType", backref="users")
    registrations = db.relationship(
        "CourseUserAttended",
        backref="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def is_enrolled(self, course):
        return (
            self.registrations.filter(CourseUserAttended.course_id == course.id).count()
            > 0
        )

    def is_attended(self, course):
        return (
            self.registrations.filter(CourseUserAttended.course_id == course.id)
            .first()
            .attended
        )

    def __eq__(self, other):
        return self.name.split(" ")[::-1][0] == other.name.split(" ")[::-1][0]

    def __lt__(self, other):
        return self.name.split(" ")[::-1][0] < other.name.split(" ")[::-1][0]


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    source_uri = db.Column(db.String(255))
    endpoint = db.Column(db.String(255))
    method = db.Column(db.String(64))
    json_data = db.Column(db.String(2500))
    occurred = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="actions")


class CourseUserAttended(Manager, db.Model):
    __tablename__ = "course_user_attended"
    course_id = db.Column(
        db.Integer,
        db.ForeignKey("course.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    attended = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
