import scrapy
import math
from .base import BaseSpider
from ..gepris_helper import search_list_params, SEARCH_URL
from ..items import SearchResultLoader


class SearchResultsSpider(BaseSpider):
    name = 'search_results'
    allowed_domains = ['gepris.dfg.de']
    # 1 Concurrent Request is fast enough, if we use a lot of items per page
    custom_settings = dict(
        CONCURRENT_REQUESTS=1,
        HTTPCACHE_ENABLED=False
    )
    items_per_page = 1000
    total_items = math.inf

    def __init__(self, context, items=1000, *args, **kwargs):
        super(SearchResultsSpider, self).__init__(context, *args, **kwargs)
        self.items_per_page = int(items)
        if self.context == 'person':
            self.context_load_function = self.load_person
        elif context == 'institution':
            self.context_load_function = self.load_institution
        elif context == 'projekt':
            self.context_load_function = self.load_project
        self.seen_ids = set()

    def start_requests(self):
        current_index = 0
        while current_index < self.total_items:
            items_on_this_page = min(self.items_per_page, self.total_items - current_index)
            self.logger.info(
                f'Starting Request for items {current_index} to {current_index + items_on_this_page} of total {self.total_items} items')
            # It is important to use dont_filter=True,
            # because the first request is redirected to itself, which makes scrapy filter this second request
            # see: https://stackoverflow.com/questions/59705305/scrapy-thinks-redirects-are-duplicate-requests
            yield scrapy.FormRequest(
                SEARCH_URL,
                method='GET',
                formdata=search_list_params(context=self.context, results_per_site=self.items_per_page, index=current_index),
                dont_filter=True,
                cb_kwargs=dict(items_on_page=items_on_this_page),
                meta=dict(expected_language='de')
            )
            current_index += self.items_per_page

    def parse(self, response, items_on_page):
        # set total items if not set before
        if self.total_items == math.inf:
            self.set_total_items(response)
        results_on_page = response.xpath('//*[@id="liste"]/div[@class!="pagination"]')
        # iterate over all results on page
        loaded_items = 0
        for result in results_on_page:
            loader = SearchResultLoader(selector=result)
            loader.add_xpath('id', './/h2/a/@href')
            loader.add_xpath('name_de', './/h2/a/text()')

            for item in self.context_load_function(loader, result):
                loaded_items += 1
                item_id = item['id']
                if item_id in self.seen_ids:
                    self.logger.warn(f'Found ID {item_id} second time on page: {response.url}')
                else:
                    self.seen_ids.add(item_id)
                yield item
        if loaded_items != items_on_page:
            self.logger.warn(
                f'Expected {items_on_page} items on page but loaded {loaded_items} on url {response.url}')

    def set_total_items(self, response):
        self.logger.info('Trying to find total items')
        self.total_items = int(
            response.xpath('//*[@id=$total_result_id]', total_result_id='result-info')
                    .attrib['data-result-count'].replace('.', '')
        )

    def load_project(self, loader, result_selector):
        for detail_line in result_selector.xpath('./div[@class="details"]/div'):
            detail_points = detail_line.xpath('./span')
            loader.add_value('project_attributes', self.attributes_pairs_list(detail_points))
        yield loader.load_item()

    def load_person(self, loader, result_selector):
        loader.add_value('addresse', self.extract_text_and_links(result_selector.xpath('./div[@class="beschreibung"]')))
        yield loader.load_item()

    def load_institution(self, loader, result_selector):
        parent_institution = loader.load_item()
        for sub_institution in result_selector.xpath('./div[@class="subInstitution"]'):
            sub_institution_loader = SearchResultLoader(selector=sub_institution)
            sub_institution_loader.add_xpath('id', './a/@href')
            sub_institution_loader.add_xpath('name_de', './a/text()')
            sub_institution_loader.add_xpath('addresse', './text()')
            sub_institution_loader.add_value('uebergeordnete_institution', parent_institution)
            sub_institution_item = sub_institution_loader.load_item()
            yield sub_institution_item
