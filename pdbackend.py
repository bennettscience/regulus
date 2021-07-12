from app import app, db
from app.models import (
    Course,
    CourseLink,
    CourseLinkType,
    CourseType,
    CourseUserAttended,
    Location,
    Log,
    User,
    UserType,
)


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "CourseType": CourseType,
        "CourseUserAttended": CourseUserAttended,
        "CourseLinkType": CourseLinkType,
        "Location": Location,
        "UserType": UserType,
        "Course": Course,
        "CourseLink": CourseLink,
        "User": User,
        "Log": Log
    }
