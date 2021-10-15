from scrapy.cmdline import execute
import subprocess
import os
import shlex

try:
    # sourcing the environment variables from the 'outside_docker.sh' file
    command = shlex.split("env -i bash -c 'source outside_docker.sh && env'")
    proc = subprocess.run(command, capture_output=True, text=True)
    for line in proc.stdout.split('\n'):
        if line == '':
            break
        key, value = line.split('=')
        os.environ[key] = value
    # actual scrapy command
    execute(
        [
            'scrapy',
            'crawl',
            # 'search_results',
            # 'details',
            'data_monitor',
            # '-O',
            # 'test.json',
            # '--loglevel=DEBUG',
            # '-s',
            # 'HTTPCACHE_ENABLED=False',
            # '-s',
            # 'HTTPCACHE_FORCE_REFRESH=True',
            # '-s',
            # 'NO_DB=True',
            # '-a',
            # 'context=person',
            # '-a',
            # 'items=1'
            # '-a',
            # 'ids=[215969423]'
        ]
    )
except SystemExit:
    pass
