import os
from pathlib import Path

basedir = Path(__file__).parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')\
        or 'sqlite:///' + str(basedir / 'planner.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
