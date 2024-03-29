import math
from .base import BaseSpider
from ..gepris_helper import search_results_request
from ..items import SearchResultLoader


class SearchResultsSpider(BaseSpider):
    name = 'search_results'
    allowed_domains = ['gepris.dfg.de']
    # 2 Concurrent Request is fast enough, if we use a lot of items per page
    custom_settings = dict(
        CONCURRENT_REQUESTS=2,
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
            yield search_results_request(self.context, self.items_per_page, current_index, items_on_this_page)
            current_index += self.items_per_page

    def parse(self, response, items_on_page):
        # set total items if not set before
        # TODO: this should be done in a middleware
        # if it is not there the first time, stop the spider
        if self.total_items == math.inf:
            self.set_total_items(response)
            if self.had_error:
                return
        results_on_page = response.xpath('//*[@id="liste"]/div[@class!="pagination"]')
        # iterate over all results on page
        loaded_items = 0
        for result in results_on_page:
            result_link = result.xpath('.//h2/a')
            if result_link.attrib['href'] == f"/gepris/{self.context}/null":
                self.logger.warning(f"Found unexpected search_result without id: {result.get()}")
            else:
                loader = SearchResultLoader(selector=result)
                loader.add_xpath('id', './/h2/a/@href')
                loader.add_xpath('name_de', './/h2/a/text()')

                for item in self.context_load_function(loader, result):
                    loaded_items += 1
                    item_id = item['id']
                    if item_id in self.seen_ids:
                        self.logger.warning(f'Found ID {item_id} second time on page: {response.url}')
                    else:
                        self.seen_ids.add(item_id)
                    yield item
        if loaded_items != items_on_page:
            self.logger.warning(
                f'Expected {items_on_page} items on page but loaded {loaded_items} on url {response.url}')

    def set_total_items(self, response):
        self.logger.info('Trying to find total items')
        try:
            self.total_items = int(
                response.xpath('//*[@id=$total_result_id]', total_result_id='result-info')
                    .attrib['data-result-count'].replace('.', '')
            )
        except Exception as e:
            self.logger.error(f'{e} - Did not find total result count, setting it to 0')
            self.total_items = 0
            self.had_error = True

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
