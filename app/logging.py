import json
from flask import request
from app import db
from app.models import Log
from flask_login import current_user

def create_log():
    data = None
    endpoint = request.path
    source_uri = request.remote_addr
    method = request.method

    if request.json is not None:
        data = request.json

    log = Log(
        user_id=6,
        source_uri=source_uri,
        endpoint=endpoint,
        method=method,
        json_data=json.dumps(data)
    )

    db.session.add(log)
    db.session.commit()
