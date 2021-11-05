import os
import sys
import importlib
from unittest import TestCase

from scrapy.utils.project import get_project_settings


class SettingsTest(TestCase):

    def setUp(self) -> None:
        importlib.import_module('gepris_crawler.settings')

    def tearDown(self) -> None:
        os.environ.clear()

    def test_fake_user_agent_disable(self):
        os.environ['USER_AGENT'] = 'my useragent'
        importlib.reload(sys.modules['gepris_crawler.settings'])
        settings = get_project_settings()
        self.assertEqual('my useragent', settings.get('USER_AGENT'))
        self.assertEqual(None, settings.get('FAKEUSERAGENT_PROVIDERS'), None)
        self.assertDictEqual({}, dict(settings.get('DOWNLOADER_MIDDLEWARES')))

    def test_fake_user_agent_enable(self):
        importlib.reload(sys.modules['gepris_crawler.settings'])
        settings = get_project_settings()
        self.assertEqual('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0',
                         settings.get('USER_AGENT'))
        self.assertIsNotNone(settings.get('FAKEUSERAGENT_PROVIDERS'))
        dl_mw = settings.get('DOWNLOADER_MIDDLEWARES')
        self.assertIsNone(dl_mw.get('scrapy.downloadermiddlewares.useragent.UserAgentMiddleware'))
        self.assertIsNone(dl_mw.get('scrapy.downloadermiddlewares.retry.RetryMiddleware'))
        self.assertIsNotNone(dl_mw.get('scrapy_fake_useragent.middleware.RandomUserAgentMiddleware'))
        self.assertIsNotNone(dl_mw.get('scrapy_fake_useragent.middleware.RetryUserAgentMiddleware'))
