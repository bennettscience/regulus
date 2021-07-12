import json

from app import app

@app.errorhandler(401)
def unauthorized(err):
    response = err.get_response()
    response.data = json.dumps(
        {
            "code": err.code,
            "name": err.name,
            "description": err.description

        }
    )
    response.content_type = "application/json"
    return response

@app.errorhandler(404)
def page_not_found(e):
    response = e.get_response()
    response.data = json.dumps(
        {
            "code": e.code,
            "name": e.name,
            "description": e.description,
        }
    )
    response.content_type = "application/json"
    return response

@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    response = err.get_response()
    messages = err.data.get("messages", ["Invalid request."])
    response.data = json.dumps(
        {
            "code": err.code,
            "name": err.name,
            "description": "Unprocessable request. See messages for details.",
            "messages": messages
        }
    )

    response.content_type = "application/json"
    return response

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
