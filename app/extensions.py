from flask_caching import Cache
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

import jinja_partials

db = SQLAlchemy()
cache = Cache()
cors = CORS()
lm = LoginManager()
migrate = Migrate()
partials = jinja_partials
