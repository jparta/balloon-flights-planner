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
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JOBS = [
        {
            'id': 'run_astra_sims',
            'func': 'planner.tasks:run_astra_sims_background',
            'trigger': 'cron',
            'hour': '1,7,13,19',
            'replace_existing': True,
            'timezone': 'UTC',
        },
    ]
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URI)
    }
    SCHEDULER_EXECUTORS = {
        'default': ProcessPoolExecutor(5)
    }
