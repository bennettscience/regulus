from functools import wraps
from flask import abort, current_app, url_for
from flask_login import current_user

def restricted(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.is_anonymous:
            abort(401)
        if current_user.usertype_id == 3 or current_user.usertype_id == 4:
            abort(403)
        return func(*args, **kwargs)
    return wrapper

def admin_or_self(func):
    @wraps(func)
    def admin_or_self_wrapper(*args, **kwargs):
        if current_user.is_anonymous:
            abort(401)
        if current_user.usertype_id != 1 and current_user.id != kwargs['user_id']:
            abort(403)
        return func(*args, **kwargs)
    return admin_or_self_wrapper

def admin_only(func):
    @wraps(func)
    def admin_only_wrapper(*args, **kwargs):
        if current_user.is_anonymous:
            abort(401)
        if current_user.usertype_id != 1:
            abort(403)
        return func(*args, **kwargs)
    return admin_only_wrapper
