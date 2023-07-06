import atexit

from flask import Flask

from config import Config
from planner.extensions import db, migrate, scheduler


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions here
    db.init_app(app)
    migrate.init_app(app, db)

    scheduler.init_app(app)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))

    # Register blueprints here
    from planner.main import bp as main_bp
    from planner.commands import utils_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(utils_bp)

    @app.route('/test/')
    def test_page():
        return '<h1>Testing the Flask Application Factory Pattern</h1>'

    return app
