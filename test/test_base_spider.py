import unittest
from test.resources import get_settings
from gepris_crawler.spiders.data_monitor import DataMonitorSpider


class DataMonitorSpiderTest(unittest.TestCase):

    def setUp(self):
        self.spider = DataMonitorSpider(settings=get_settings(database=False))

    def test_had_error(self):
        self.assertEqual(self.spider.had_error, False)
        self.spider.had_error = True
        self.assertEqual(self.spider.had_error, True)

