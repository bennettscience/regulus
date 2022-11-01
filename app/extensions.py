from flask_caching import Cache
from flask_cors import CORS
from flask_login import LoginManager
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

import jinja_partials

db = SQLAlchemy()
cache = Cache()
cors = CORS()
lm = LoginManager()
ma = Marshmallow()
migrate = Migrate()
partials = jinja_partials
