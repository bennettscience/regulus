import json
from flask import jsonify
from app import app

@app.errorhandler(401)
def unauthorized(err):
    response = err.get_response()
    response.data = json.dumps(
        {
            "code": err.code,
            "name": "Wrong Authorization",
            "description": "Incorrect authorization credentials used in the request."
        }
    )
    response.content_type = "application/json"
    return response

@app.errorhandler(403)
def forbidden(err):
    response = err.get_response()
    response.data = json.dumps(
        {
            "code": err.code,
            "name": "Forbidden",
            "description": "You do not have permission to access this resource."
        }
    )
    response.content_type = "application/json"
    return response

@app.errorhandler(404)
def page_not_found(err):
    response = err.get_response()
    response.data = json.dumps(
        {
            "code": err.code,
            "name": "Address not found",
            "description": "You tried to get something that we can't find. Check the URL and try again.",
        }
    )
    response.content_type = "application/json"
    return response

@app.errorhandler(409)
def request_conflict(err):
    response = err.get_response()
    response.data = json.dumps(
        {
            "code": err.code,
            "name": err.name,
            "description": "There aren't enough seats left to register for the event."
        }
    )
    response.content_type = "application/json"
    return response

@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    # Catch errors from webargs and Marshmallow
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])
    if headers:
        return jsonify({"errors": messages}), err.code, headers
    else:
        return jsonify({"errors": messages}), err.code

@app.errorhandler(500)
def internal_error(e):
    response = e.get_response()
    response.data = json.dumps(
        {
            "code": e.code,
            "name": e.name,
            "description": "Something went wrong on our end. We'll get on that now. Sorry."
        }
    )
    response.content_type = "applicaton/json"
    return response
