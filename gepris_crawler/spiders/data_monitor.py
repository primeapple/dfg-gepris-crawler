from ..gepris_helper import data_monitor_url, DATA_MONITOR_KEYS
from ..items import DataMonitorLoader
from .base import BaseSpider


class DataMonitorSpider(BaseSpider):
    name = 'data_monitor'
    allowed_domains = ['gepris.dfg.de']
    start_urls = [data_monitor_url()]

    custom_settings = dict(HTTPCACHE_ENABLED=False)

    def __init__(self, *args, **kwargs):
        super(DataMonitorSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        loader = DataMonitorLoader()
        loader.add_value('last_update', self.extract_date(response, 'Letzte Aktualisierung der Daten: '))
        loader.add_value('last_approval', self.extract_date(response, 'Aktuellstes Bewilligungsdatum: '))
        loader.add_value('gepris_version', self.extract_index_data(response, r'aktuelle Gepris-Version: (.*)'))
        loader.add_value('current_index_version', self.extract_index_data(response, r'aktuelle Index-Version: (.*) \('))
        loader.add_value('current_index_date', self.extract_index_data(response, r'aktuelle Index-Version: (?:.*) \((.*)\)'))
        # iterate over all table rows on page
        for row in response.xpath('//tbody/tr'):
            page_key, value = row.xpath('./td/text()').getall()
            item_key = DATA_MONITOR_KEYS[page_key.strip()]
            loader.add_value(item_key, value)
        return loader.load_item()

    def extract_date(self, response, str_prefix):
        return response.xpath('//*[starts-with(text(),$text)]/text()', text=str_prefix).get().removeprefix(str_prefix)

    def extract_index_data(self, response, regex):
        return response.xpath('//*[@class="geprisversionsinfo"]/text()').re_first(regex)
