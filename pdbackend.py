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

@app.cli.command('seed-events')
@click.argument('filename')
def seed_events(filename):
    import sys
    import csv
    from dateutil import parser
    if filename is None:
        print('Please provide a csv file for processing')
        sys.exit(1)
    
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            print('Checking for {}...'.format(row[3]))
            exists = Course.query.filter(Course.ext_calendar == row[9]).first()
            if exists is None:
                print('{} does not exist. Creating...'.format(row[3]))
                starts = parser.parse(row[5])
                ends = parser.parse(row[6])
                created_at = parser.parse(row[10])
                event = Course(
                    coursetype_id=row[0],
                    location_id=row[1],
                    course_size=row[2],
                    title=row[3],
                    description=row[4],
                    starts=starts,
                    ends=ends,
                    active=bool(row[7]),
                    occurred=bool(row[8]),
                    ext_calendar=row[9],
                    created_at=created_at
                )
                db.session.add(event)
    db.session.commit()
    print('Added events successfully.')
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

@app.cli.command('import-users')
@click.argument('filename')
def import_users(filename):
    import sys
    import csv

    if filename is None:
        print('Please provide a csv file for processing')
        sys.exit(1)
    
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            print('Checking for {}...'.format(row[3]))
            exists = User.query.filter(User.email == row[0]).first()
            if exists is None:
                print('{} does not exist. Creating...'.format(row[3]))
                
                user = User(
                    email=row[0],
                    name=row[1],
                    location_id=row[3],
                    usertype_id=4
                )
                db.session.add(user)
    db.session.commit()
    print('Added users successfully.')
    sys.exit()