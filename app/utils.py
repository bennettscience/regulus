from typing import List

import bleach_extras

from flask import abort, session
from flask_login import current_user
from html import unescape

from app.models import Course
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
    "User": ['schedule', 'documents', 'logout'],
    "Presenter": [
        'schedule',
        'documents',
        'admin',
        'create',
        'logout',
    ],
    "SuperAdmin": [
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
        "href": '/admin/events',
        "icon": admin,
    },
    {
        "element": 'users',
        "label": 'User Management',
        "href": '/admin/users',
        "icon": users,
    },
    {
        "element": 'create',
        "label": 'Create Event',
        "href": '/create',
        "icon": create,
        "action": 'on htmx:afterSwap call makeQuill() end'
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

def clean_escaped_html(value: str) -> str:
    """ Remove non-whitelist HTML tags from user input.

    On the frontend, Jodit escapes HTML characters on the fly, sending unicode strings. Those need
    to be removed before processing with bleach to remove non-whitelisted tags.

    This is a little goofy because the escaped HTML needs to be parsed back into unicode characters
    to be removed correctly by bleach.

    The bleach_extras package removes non-whitelisted tag children elements as well as the tags.

    This solution is a combination of approaches from 
      - https://stackoverflow.com/questions/701704/convert-html-entities-to-unicode-and-vice-versa
      - https://github.com/jvanasco/bleach_extras

    Args:
        value (str): string containing HTML

    Returns:
        str: Sanitized HTML
    """
    clean = bleach_extras.clean_strip_content(unescape(value), tags=['p', 'strong', 'em', 'u', 'br', 'ul', 'ol', 'li'])
    return clean

def object_to_select(items):
    """ Unpack a database class for the select partial

    Args:
        items (any): List of database objects
    
    Returns:
        list (object): [{text, value}, ...] formatted list
    """
    results = [{"text": item.name, "value": item.id} for item in items]

    return results

def get_user_navigation():
    """ Page refreshes need to rebuild the user menu. This gets the current user and adds their
        menu options to the response before being sent back to the client.
    """
    if current_user.is_anonymous:
        nav_items = []
    else:
        nav_items = get_user_navigation_menu()
    
    # If the user session isn't fresh, they need to log in again.
    if not current_user.is_anonymous and session['_fresh']:

        nav_items.insert(0, {
            "element": 'schedule',
            "label": "My Schedule",
            "href": "/users/{}/registrations".format(current_user.id),
            "icon": calendar
        })
        nav_items.insert(1, {
            "element": 'documents',
            "label": 'Account & Documents',
            "href": '/users/{}/documents'.format(current_user.id),
            "icon": documents,
        })

    return nav_items
