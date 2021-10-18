import re
from urllib.request import urlopen


def get_formatted_proxy_list(proxy_url, pattern=r'(.*):(.*):(.*):(.*)', replacement=r'http://\3:\4@\1:\2'):
    with urlopen(proxy_url) as f:
        proxy_list = [line.decode('utf-8').strip() for line in f if line.decode('utf-8').strip()]
    return [re.sub(pattern, replacement, url) for url in proxy_list]

