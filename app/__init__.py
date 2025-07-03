from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    migrate.init_app(app, db)

    from .routes.auth import auth_bp
    from .routes.review import review_bp
    from .routes.search import search_bp
    from .routes.billing import billing_bp
    from .routes.upload import upload_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(review_bp, url_prefix='/api/v1')
    app.register_blueprint(search_bp, url_prefix='/api/v1')
    app.register_blueprint(billing_bp, url_prefix='/webhook')
    app.register_blueprint(upload_bp, url_prefix='/api/v1')

    from . import models

    return app