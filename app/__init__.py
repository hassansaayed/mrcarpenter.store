from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(get_remote_address)  # Initialize limiter here

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)  # ✅ init limiter *after* app is created

    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
