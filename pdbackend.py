import click

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

@app.cli.command('seed-location')
@click.argument('filename')
def seed_location(filename):
    import sys
    import csv
    if filename is None:
        print('Please provide a csv file for processing')
        sys.exit(1)  

    with open(filename, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            loc = Location.query.filter(Location.name == row[0]).first()
            if loc is None:
                print('Adding {}'.format(row[0]))
                db.session.add(Location(name=row[0], address=row[2]))
            else:
                print('Location {} already exists, updating address'.format(row[0]))
                loc.address = row[2]
    
    db.session.commit()
    sys.exit()


@app.cli.command('seed-role')
def seed_role():
    import sys
    print('Creating all roles')
    site_roles = [
        UserType(name='SuperAdmin'),
        UserType(name='Presenter'),
        UserType(name='Observer'),
        UserType(name='User')
    ]
    db.session.add_all(site_roles)
    db.session.commit()
    print('Successfully created all roles.')
    sys.exit()

