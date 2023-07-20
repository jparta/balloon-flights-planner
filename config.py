import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore


basedir = Path(__file__).parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')\
        or 'postgresql://postgres:postgres@localhost:5432/planner'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JOBS = [
        {
            'id': 'run_astra_sims',
            'func': 'planner.tasks:run_astra_sims',
            'trigger': 'cron',
            'hour': '1,7,13,19',
            'replace_existing': True,
            'timezone': 'UTC',
        },
    ]
    SCHEDULER_JOBSTORES = {
        'default': MemoryJobStore()
    }
    SCHEDULER_EXECUTORS = {
        'default': ProcessPoolExecutor(5)
    }


class ConfigDevelopment(Config):
    JOBS = [
        {
            'id': 'run_astra_sims_within_5_seconds',
            'func': 'planner.tasks:run_astra_sims',
            'trigger': 'date',
            'run_date': datetime.now(timezone.utc) + timedelta(seconds=5),
            'replace_existing': True,
            'timezone': 'UTC',
        },
    ]
