import shlex
import subprocess
import os

from scrapy.utils.project import get_project_settings


def read_env_vars():
    # sourcing the environment variables from the 'outside_docker.sh' file
    command = shlex.split("env -i bash -c 'source outside_docker.sh && env'")
    proc = subprocess.run(command, capture_output=True, cwd='./..', text=True)
    for line in proc.stdout.split('\n'):
        if line == '':
            break
        key, value = line.split('=')
        os.environ[key] = value


def get_settings(database=True):
    read_env_vars()
    settings = get_project_settings()
    if not database:
        settings.set('NO_DB', True)
    else:
        settings.set('NO_DB', False)
    return settings
