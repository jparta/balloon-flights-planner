import click
from flask import Blueprint


utils_bp = Blueprint('utils', __name__)

@utils_bp.cli.command('initdb')
def initdb():
    """Initialize the database."""
    click.echo('Init the db')
    from planner import models, db
    db.create_all()
    click.echo('Done')
