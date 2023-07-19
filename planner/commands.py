import click
from flask import Blueprint


utils_bp = Blueprint('utils', __name__)

@utils_bp.cli.command('init_db')
def init_db():
    """Initialize the database."""
    click.echo('Initializing the db')
    from planner import models, db
    db.create_all()
    click.echo('Done')

@utils_bp.cli.command('wipe_db')
def wipe_db():
    """Drop everything."""
    click.echo('Wiping the db')
    from planner import models, db
    db.drop_all()
    click.echo('Done')
