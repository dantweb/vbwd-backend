from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from concurrent.futures import ThreadPoolExecutor
import os

db = SQLAlchemy()
socketio = SocketIO()
executor = ThreadPoolExecutor(max_workers=10)


def create_app(config_name=None):
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://vbwd:vbwd@postgres:5432/vbwd'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Only use pool options for non-SQLite databases
    if not app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 5,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }

    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app, async_mode='threading', cors_allowed_origins='*')

    # Register blueprints
    from src.routes.user import user_bp
    from src.routes.admin import admin_bp
    from src.routes.health import health_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # Register WebSocket handlers
    from src.routes.websocket import register_socket_handlers
    register_socket_handlers(socketio)

    return app
