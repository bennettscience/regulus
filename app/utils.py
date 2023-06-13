from typing import List

import nh3

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
    logout,
)

# Possible navigation items for a given user.
permissions = {
    "User": ["schedule", "documents", "logout"],
    "Presenter": [
        "schedule",
        "documents",
        "admin",
        "create",
        "logout",
    ],
    "SuperAdmin": [
        "schedule",
        "documents",
        "admin",
        "users",
        "create",
        "logout",
    ],
}

# Store all of the navigation objects to use in a comprehension
navigation_items = [
    {
        "element": "presenter",
        "label": "Presenter Dashboard",
        "href": "/presenter",
        "icon": presenter,
    },
    {
        "element": "reports",
        "label": "Reports",
        "href": "/reports",
        "icon": reports,
    },
    {
        "element": "admin",
        "label": "Event Management",
        "href": "/admin/events",
        "icon": admin,
    },
    {
        "element": "users",
        "label": "User Management",
        "href": "/admin/users",
        "icon": users,
    },
    {
        "element": "create",
        "label": "Create Event",
        "href": "/create",
        "icon": create,
        "action": "on htmx:afterSwap call makeQuill() end",
    },
    {"element": "logout", "label": "Logout", "href": "/logout", "icon": logout},
]


def get_user_navigation_menu() -> List[dict]:
    user_type = current_user.role.name
    items = [
        menuitem
        for menuitem in navigation_items
        if menuitem["element"] in permissions[user_type]
    ]
    return items


def clean_escaped_html(value: str) -> str:
    """Remove non-whitelist HTML tags from user input.

    Update 6/13/2023
    The bleach package was deprecated in Jan, 2023. bleach_extras relied on
    that in order to clean html.
    https://github.com/mozilla/bleach/issues/698

    nh3 is a replacement which includes a kwarg to remove specific tag children.
    - https://github.com/messense/nh3
    - https://nh3.readthedocs.io/en/latest/

    Args:
        value (str): string containing HTML

    Returns:
        str: Sanitized HTML
    """
    clean = nh3.clean(
        unescape(value), tags={"br", "p", "strong", "em", "u", "ul", "ol", "li"}
    )
    return clean


def object_to_select(items):
    """Unpack a database class for the select partial

    Args:
        items (any): List of database objects

    Returns:
        list (object): [{text, value}, ...] formatted list
    """
    results = [{"text": item.name, "value": item.id} for item in items]

    return results


def get_user_navigation():
    """
    Page refreshes need to rebuild the user menu.
    This gets the current user and adds their
    menu options to the response before being sent back to the client.
    """
    if current_user.is_anonymous:
        nav_items = []
    else:
        nav_items = get_user_navigation_menu()

    # If the user session isn't fresh, they need to log in again.
    if not current_user.is_anonymous and session["_fresh"]:

        nav_items.insert(
            0,
            {
                "element": "schedule",
                "label": "My Schedule",
                "href": "/users/{}/registrations".format(current_user.id),
                "icon": calendar,
            },
        )
        nav_items.insert(
            1,
            {
                "element": "documents",
                "label": "My Account",
                "href": "/users/{}/documents".format(current_user.id),
                "icon": documents,
            },
        )

    return nav_items
