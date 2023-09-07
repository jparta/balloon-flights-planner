import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore


basedir = Path(__file__).parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')\
        or 'postgresql://postgres:postgres@localhost:5432/planner'
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URI)
    }
    SCHEDULER_EXECUTORS = {
        'default': ProcessPoolExecutor(1)
    }
    SCHEDULER_MISFIRE_GRACE_TIME = 6 * 60 * 60
    SCHEDULER_COALESCING = True


class ConfigDevelopment(Config):
    pass
