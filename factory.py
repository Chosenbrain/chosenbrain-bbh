# factory.py
import os
from flask import Flask
from flask_wtf import CSRFProtect
from celery import Celery
from dotenv import load_dotenv
from flask_socketio import SocketIO
from config import Config
from extensions import db, migrate

# Load environment variables
load_dotenv()

# Initialize extensions
csrf = CSRFProtect()
socketio = SocketIO(cors_allowed_origins="*")  # ✅ Define socketio instance

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    socketio.init_app(app)  # ✅ Attach SocketIO to app

    from models import Report  # Only import relevant models
    return app

def make_celery(app=None):
    if app is None:
        app = create_app()

    celery = Celery(
        app.import_name,
        broker=app.config.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
