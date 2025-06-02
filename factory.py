# factory.py
import os
from flask import Flask
from flask_wtf import CSRFProtect
from celery import Celery
from dotenv import load_dotenv

from config     import Config
from extensions import db, migrate

# load .env into os.environ before reading Config
load_dotenv()

# CSRF for any forms you might use
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    from models import Report  # ✅ Only import what's still relevant

    csrf.init_app(app)
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
