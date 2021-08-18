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

    if request.json is not None:
        data = request.json
    
    if current_user.is_anonymous:
        user_id = 0
    else:
        user_id = current_user.id

    log = Log(
        user_id=user_id,
        source_uri=source_uri,
        endpoint=endpoint,
        method=method,
        json_data=json.dumps(data)
    )

    db.session.add(log)
    db.session.commit()
