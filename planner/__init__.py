import os

from flask import Flask

from config import Config, ConfigDevelopment
from planner.extensions import db, migrate, scheduler


def create_app():
    app = Flask(__name__)
    environment = os.getenv('FLASK_ENV')
    if environment == 'production':
        app.config.from_object(Config)
    elif environment == 'development':
        app.config.from_object(ConfigDevelopment)
    else:
        raise ValueError(f"FLASK_ENV={environment} is not a valid environment. Use 'production' or 'development'")

    # Initialize Flask extensions here
    db.init_app(app)
    migrate.init_app(app, db)

    scheduler.init_app(app)
    scheduler.start()

    # Register blueprints here
    from planner.main import bp as main_bp
    from planner.commands import utils_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(utils_bp)

    @app.route('/test/')
    def test_page():
        return '<h1>Testing the Flask Application Factory Pattern</h1>'

    return app
