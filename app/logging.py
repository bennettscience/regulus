import json
from flask import request
from flask_migrate import current
from app import db
from app.models import Log
from flask_login import current_user, AnonymousUserMixin


def create_log():
    data = None
    endpoint = request.path
    source_uri = request.remote_addr
    method = request.method

    # requests are either JSON or form inputs. Update
    # to handle any data type.
    # See https://stackoverflow.com/questions/45590988/converting-flask-form-data-to-json-only-gets-first-value
    # for handling form input serialization for logs
    if method == "POST" or method == "PUT":
        if request.form is not None and request.is_json is False:
            data = json.dumps(request.form)
        elif request.json is not None:
            data = json.dumps(request.json)

    user_id = current_user.id

    log = Log(
        user_id=user_id,
        source_uri=source_uri,
        endpoint=endpoint,
        method=method,
        json_data=data,
    )

    db.session.add(log)
    db.session.commit()
