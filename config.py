import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_RECORD_QUERIES = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID")
    CALENDAR_HOOK_TOKEN = os.environ.get("CALENDAR_HOOK_TOKEN")
    CALENDAR_HOOK_URL = os.environ.get("CALENDAR_HOOK_URL")

    OAUTH_CREDENTIALS = {
        'google': {
            'key': os.environ.get("GOOGLE_CLIENT_ID"),
            'secret': os.environ.get("GOOGLE_CLIENT_SECRET"),
            'conf_url': 'https://accounts.google.com/.well-known/openid-configuration'

        }
    }
