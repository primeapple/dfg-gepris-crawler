# Scrapy settings for gepris_crawler project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import os
from gepris_crawler.proxylist import get_formatted_proxy_list

BOT_NAME = 'gepris_crawler'

SPIDER_MODULES = ['gepris_crawler.spiders']
NEWSPIDER_MODULE = 'gepris_crawler.spiders'

# Database specific credentials
DATABASE_NAME = os.environ.get('POSTGRES_DB')
DATABASE_USER = os.environ.get('POSTGRES_USER')
DATABASE_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
DATABASE_HOST = os.environ.get('POSTGRES_HOST')
DATABASE_PORT = os.environ.get('POSTGRES_PORT')

LOG_LEVEL = 'INFO'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'gepris_crawler by Toni Mueller (toni.mueller@student.uni-halle.de)'

# Seems they are slowing me down, try to be more anonymous by using fake useragent
FAKEUSERAGENT_PROVIDERS = [
    'scrapy_fake_useragent.providers.FakeUserAgentProvider',  # this is the first provider we'll try
    'scrapy_fake_useragent.providers.FakerProvider',  # if FakeUserAgentProvider fails, we'll use faker to generate a user-agent string for us
    'scrapy_fake_useragent.providers.FixedUserAgentProvider',  # fall back to USER_AGENT value
]
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0'
# USER_AGENT = 'gepris_crawler by Toni Mueller (toni.mueller@student.uni-halle.de)'

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
    'scrapy_fake_useragent.middleware.RetryUserAgentMiddleware': 401,
}

# Parameters for Proxy middleware
if os.environ.get('WEBSHARE_PROXY_LIST_URL') is not None:
    ROTATING_PROXY_LIST = get_formatted_proxy_list(os.environ.get('WEBSHARE_PROXY_LIST_URL'))
    PROXY_MIDDLEWARES = {
        'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
        'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
    }
    DOWNLOADER_MIDDLEWARES.update(PROXY_MIDDLEWARES)

# Parameters for email notifications
MAIL_RECEIVER = os.environ.get('NOTIFICATION_EMAIL_RECEIVER')
MAIL_FROM = os.environ.get('NOTIFICATION_EMAIL_SENDER')
MAIL_USER = os.environ.get('NOTIFICATION_EMAIL_USERNAME')
MAIL_PASS = os.environ.get('NOTIFICATION_EMAIL_PASSWORD')
MAIL_HOST = os.environ.get('NOTIFICATION_EMAIL_SMTP_SERVER')
MAIL_PORT = os.environ.get('NOTIFICATION_EMAIL_SMTP_PORT')

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
CONCURRENT_REQUESTS_PER_IP = 8

# Disable cookies (enabled by default)
COOKIES_ENABLED = True
# COOKIES_DEBUG = True

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# The priorities goes a following:
# Lower: Nearer to Engine: process_input is executed earlier
# Higher: Nearer to Spider: process_output is executed earlier
SPIDER_MIDDLEWARES = {
    'gepris_crawler.middlewares.ExceptionHandlerMiddleware': 501,
    'gepris_crawler.middlewares.DetailsPageExpectedStructureCheckMiddleware': 541,
    'gepris_crawler.middlewares.DetailsPageExistsCheckMiddleware': 542,
    'gepris_crawler.middlewares.LanguageCheckMiddleware': 543,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'gepris_crawler.pipelines.DatabaseInsertionPipeline': 299,
    'gepris_crawler.pipelines.EmailNotifierPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 2
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 30
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = True

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = False
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [500, 503, 504, 400, 403, 404, 408, 301, 302]
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.DbmCacheStorage'
HTTPCACHE_POLICY = 'gepris_crawler.middlewares.RefreshHttpCachePolicy'
HTTPCACHE_FORCE_REFRESH = False
