from flask import Blueprint, render_template
from app.static.assets.icons import (
    home,
    calendar
)

home_bp = Blueprint('home_bp', __name__)


# TODO: Look up the user permissions

@home_bp.get('/')
def home_route():
    items = [
        {
            'item': 'home',
            'label': 'Home',
            'href': '/',
            'icon': home
        },
        {
            'item': 'schedule',
            'label': 'My Schedule',
            'href': '/registrations',
            'icon': calendar
        }
    ]
    return render_template('home/index.html', menuitems=items)
