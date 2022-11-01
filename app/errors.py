import json
from flask import jsonify, render_template


def unauthorized(err):
    return render_template("shared/errors/401.html"), 401


def forbidden(err):
    return render_template("shared/errors/403.html"), 403


def page_not_found(err):
    return render_template("shared/errors/404.html"), 404


def request_conflict(err):
    response = err.get_response()
    response.data = json.dumps(
        {
            "code": err.code,
            "name": err.name,
            "description": "There aren't enough seats left to register for the event.",
        }
    )
    response.content_type = "application/json"
    return response


def handle_error(err):
    # Catch errors from webargs and Marshmallow
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])
    if headers:
        return jsonify({"errors": messages}), err.code, headers
    else:
        return jsonify({"errors": messages}), err.code


def internal_error(e):
    response = e.get_response()
    response.data = json.dumps(
        {
            "code": e.code,
            "name": e.name,
            "description": "Something went wrong on our end. We'll get on that now. Sorry.",
        }
    )
    response.content_type = "applicaton/json"
    return response
