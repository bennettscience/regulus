from functools import wraps
from flask import abort, current_app, url_for
from flask_login import current_user

from app import app
from authlib.integrations.flask_client import OAuth


def admin_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.is_anonymous:
            abort(401)
        if not current_user.usertype_id == 1:
            abort(403)
        return func(*args, **kwargs)
    return wrapper


class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config["OAUTH_CREDENTIALS"][provider_name]
        self.consumer_key = credentials["key"]
        self.consumer_secret = credentials["secret"]
        self.conf_url = credentials["conf_url"]

    def authorize(self):
        pass

    def callback(self):
        pass

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]


class GoogleSignIn(OAuthSignIn):
    def __init__(self):
        super(GoogleSignIn, self).__init__("google")
        self.oauth = OAuth(app)

        self.oauth.register(
            name="google",
            server_metadata_url=self.conf_url,
            client_id=self.consumer_key,
            client_secret=self.consumer_secret,
            client_kwargs={"scope": "openid email profile"},
        )

    def authorize(self):
        redirect_uri = url_for("callback", _external=True)
        return self.oauth.google.authorize_redirect(redirect_uri)

    def authorize_access_token(self):
        self.token = self.oauth.google.authorize_access_token()
        return self.token

    def parse_id_token(self, token):
        return self.oauth.google.parse_id_token(token, nonce=token['userinfo']['nonce'])
