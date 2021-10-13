import json
import scrapy

from .base import BaseSpider
from ..gepris_helper import details_url, details_request, google_cache_url
from ..items import PersonDetailsLoader


class PersonDetailsSpider(BaseSpider):
    """
    This spider works similarly to the details spider, but tries to use google webcache instead
    """
    name = 'person_details'
    allowed_domains = ['gepris.dfg.de', 'webcache.googleusercontent.com']
    custom_settings = dict(
        # google normally forbids crawling their webcache
        ROBOTSTXT_OBEY=False
    )

    def __init__(self, ids=None, ids_file=None, *args, **kwargs):
        super(PersonDetailsSpider, self).__init__(*args, **kwargs)
        # ids as comma seperated value string
        if ids is not None:
            if isinstance(ids, str):
                ids = [int(element_id) for element_id in ids.split(',')]
        # ids_file as json
        elif ids_file is not None:
            with open(ids_file) as f:
                ids = [p['id'] for p in json.load(f)]
        else:
            raise ValueError('Either "ids" or "ids_file" argument have to be not none')
        self.ids_set = set(ids)
        if len(self.ids_set) < len(ids):
            self.logger.info('There are duplicates in the given ids, making them unique')

    def start_requests(self):
        for element_id in self.ids_set:
            yield self.google_cache_request(element_id)

    def google_cache_request(self, element_id):
        return scrapy.Request(google_cache_url(details_url(element_id, 'person')),
                              cb_kwargs=dict(element_id=element_id),
                              errback=self.google_cache_request_failed,
                              # use custom user agent, to hide who we are
                              # better option would be to use user agent faker middleware
                              headers={
                                  'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:77.0) Gecko/20190101 Firefox/77.0'}
                              )

    def gepris_request(self, element_id):
        return details_request(details_url(element_id, 'person'), language='de',
                               cb_kwargs=dict(element_id=element_id))

    def parse(self, response, element_id):
        loader = PersonDetailsLoader()
        loader.add_value('id', element_id)
        loader.add_value('name_de', response.xpath('//h1[@class="facelift"]/text()').get())
        content = self.get_content_div(response)
        details_div = content.xpath('./div[@class="details"]')
        for row in details_div.xpath('./p'):
            loader.add_value('details', self.details_pairs_list(row.xpath('./span')))
        loader.add_value('trees', self.extract_trees(content))
        return loader.load_item()

    def google_cache_request_failed(self, failure):
        element_id = failure.request.cb_kwargs["element_id"]
        self.logger.warn(f'Request to google failed for id {element_id}')
        yield self.gepris_request(element_id)
