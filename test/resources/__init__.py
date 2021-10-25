import shlex
import subprocess
import os
from datetime import datetime
from pytz import timezone

from scrapy.utils.project import get_project_settings

from gepris_crawler.database import PostgresDatabase
from gepris_crawler.items import DataMonitorItem


def read_env_vars():
    # sourcing the environment variables from the 'outside_docker.sh' file
    command = shlex.split("env -i bash -c 'source outside_docker.sh && env'")
    proc = subprocess.run(command, capture_output=True, cwd='./..', text=True)
    for line in proc.stdout.split('\n'):
        if line == '':
            break
        key, value = line.split('=')
        os.environ[key] = value


def get_settings(database=False, mail=False):
    read_env_vars()
    settings = get_project_settings()
    if not database:
        settings.set('NO_DB', True)
    else:
        settings.set('NO_DB', False)
        settings.set('DATABASE_NAME', os.environ.get('POSTGRES_TEST_DB'))
    if mail:
        settings.set('MAIL_RECEIVER', 'test@localhost.com')
        settings.set('MAIL_FROM', 'test@localhost.com')
        settings.set('MAIL_USER', 'test@localhost.com')
        settings.set('MAIL_PASS', 'test@localhost.com')
        settings.set('MAIL_HOST', 'test@localhost.com')
        settings.set('MAIL_PORT', 123)
    return settings


def get_test_database(settings):
    db = PostgresDatabase(settings)
    db.open()
    db.execute_sql('TRUNCATE spider_runs, data_monitor, projekte, personen, institutionen CASCADE')
    db.execute_sql('ALTER SEQUENCE spider_runs_id RESTART')
    return db


def get_sample_dm_item(version='18.5.6', project=136387, person=87700, institution=37527):
    return DataMonitorItem(last_update=datetime(2021, 10, 19).date(),
                           last_approval=datetime(2021, 8, 19).date(),
                           finished_project_count=34878,
                           project_count=project,
                           person_count=person,
                           institution_count=institution,
                           humanities_count=25080,
                           life_count=48347,
                           natural_count=35151,
                           engineering_count=25475,
                           infrastructure_count=11066,
                           gepris_version=version,
                           current_index_version='dd5213f6-d21e-4177-960f-0450db3fb750',
                           current_index_date=timezone('Europe/Berlin').localize(datetime(2021, 10, 19, 7, 47, 33)))
