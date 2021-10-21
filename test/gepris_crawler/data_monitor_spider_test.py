import unittest
from datetime import datetime

import scrapy
from pytz import timezone
from gepris_crawler.spiders.data_monitor import DataMonitorSpider
import resources.settings as s
import resources.responses as r


class DataMonitorSpiderTest(unittest.TestCase):

    def setUp(self):
        self.spider = DataMonitorSpider(settings=s.get_settings(database=False))

    def test(self):
        result = self.spider.parse(r.fake_response_from_file('data_monitor/21102022.html'))
        self.assertIsInstance(result, scrapy.Item)
        expected = {
            'last_update': datetime(2021, 10, 19).date(),
            'last_approval': datetime(2021, 8, 19).date(),
            'gepris_version': '18.5.6',
            'current_index_version': 'dd5213f6-d21e-4177-960f-0450db3fb750',
            'current_index_date': timezone('Europe/Berlin').localize(datetime(2021, 10, 19, 7, 47, 33)),
            'finished_project_count': 34878,
            'project_count': 136387,
            'person_count': 87700,
            'institution_count': 37527,
            'humanities_count': 25080,
            'life_count': 48347,
            'natural_count': 35151,
            'engineering_count': 25475,
            'infrastructure_count': 11066
        }
        self.assertDictEqual(dict(result), expected)
