from typing import List
from flask import Blueprint, redirect, render_template, session, url_for
from flask_login import current_user


home_bp = Blueprint('home_bp', __name__)

from app.models import User
from app.static.assets.icons import (
    home,
    calendar,
    documents,
    presenter,
    reports,
    admin,
    users,
    create,
    logout
)

# Possible navigation items for a given user.
permissions = {
    "User": ['home', 'schedule', 'documents', 'logout'],
    "Presenter": [
        'home',
        'schedule',
        'documents',
        'presenter',
        'create',
        'logout',
    ],
    "SuperAdmin": [
        'home',
        'schedule',
        'documents',
        'admin',
        'users',
        'create',
        'logout',
    ],
}

# Store all of the navigation objects to use in a comprehension
navigation_items = [
    {
        "element": 'home',
        "label": 'Home',
        "href": '/',
        "icon": home
    },
    {
        "element": 'schedule',
        "label": 'My Schedule',
        "href": '/schedule',
        "icon": calendar,
    },
    {
        "element": 'documents',
        "label": 'Documents',
        "href": '/documents',
        "icon": documents,
    },
    {
        "element": 'presenter',
        "label": 'Presenter Dashboard',
        "href": '/presenter',
        "icon": presenter,
    },
    {
        "element": 'reports',
        "label": 'Reports',
        "href": '/reports',
        "icon": reports,
    },
    {
        "element": 'admin',
        "label": 'Event Management',
        "href": '/admin',
        "icon": admin,
    },
    {
        "element": 'users',
        "label": 'User Management',
        "href": '/people',
        "icon": users,
    },
    {
        "element": 'create',
        "label": 'Create Event',
        "href": '/create',
        "icon": create,
    },
    {
        "element": 'logout',
        "label": 'Logout',
        "href": '/logout',
        "icon": logout
    },
]

def get_user_navigation_menu() -> List[dict]:
    user_type = current_user.role.name
    items = [menuitem for menuitem in navigation_items if menuitem['element'] in permissions[user_type]]

    return items

@home_bp.get('/')
def index():
    is_admin = False
    nav_items = get_user_navigation_menu()
    # If the user session isn't fresh, they need to log in again.
    if not current_user.is_anonymous and session['_fresh']:
        if current_user.role.name == "SuperAdmin":
            is_admin = True

        return render_template('home/index.html', menuitems=nav_items)
    else:
        return render_template('auth/login.html')
