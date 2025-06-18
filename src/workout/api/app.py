# src/workout_importer/api/app.py
from flask import Flask
import os
from flask_cors import CORS
from ..abstracts import AbstractDatabaseManager
from .workout_routes import workout_bp
from ..config import config_by_name
from ..database.db_utils import get_db_manager, close_db_manager
from .error_handlers import register_api_error_handlers


def get_db_manager() -> AbstractDatabaseManager:
    pass

def close_db_manager(e=None):
    pass


def create_app(config_name='default'):
    """Flask 애플리케이션 팩토리 함수."""
    app = Flask(__name__)

    config_object = config_by_name.get(config_name)
    if config_object is None:
        raise ValueError(f"Invalid configuration name: {config_name}")

    app.config.from_object(config_object)

    CORS(app)

    app.get_db_manager = get_db_manager

    app.teardown_appcontext(close_db_manager)

    app.register_blueprint(workout_bp)

    register_api_error_handlers(workout_bp)

    return app