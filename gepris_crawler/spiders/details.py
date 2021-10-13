import json
import re

from .base import BaseSpider
from ..gepris_helper import details_request, details_url
from ..items import ProjectItem, ProjectDetailsLoader, ProjectResultLoader, PersonDetailsLoader, \
    InstitutionDetailsLoader, ProjectResultItem
from w3lib.url import url_query_cleaner
from urllib.parse import urljoin


class DetailsSpider(BaseSpider):
    name = 'details'
    allowed_domains = ['gepris.dfg.de']

    def __init__(self, ids, context, *args, **kwargs):
        super().__init__(context, *args, **kwargs)
        self.ids = ids
        if self.context == 'person':
            self.context_loader_cls = PersonDetailsLoader
            self.context_load_function = self.load_person
        elif self.context == 'institution':
            self.context_loader_cls = InstitutionDetailsLoader
            self.context_load_function = self.load_institute
        elif self.context == 'projekt':
            self.context_loader_cls = ProjectDetailsLoader
            self.context_load_function = self.load_project

    def start_requests(self):
        # creating/reading ids
        if isinstance(self.ids, str) and self.ids.startswith('[') and self.ids.endswith(']'):
            # ids like "[1,2,3]"
            self.ids = {int(element_id) for element_id in self.ids[1:-1].split(',')}
        elif isinstance(self.ids, str) and self.ids.endswith('.json'):
            # ids like "projekts.json", a json file, that is an array where each child object has key 'id'
            with open(self.ids) as f:
                self.ids = {p['id'] for p in json.load(f)}
        elif isinstance(self.ids, str) and re.match(r'db:(all|needed):\d+', self.ids) and self.db is not None:
            limit = self.ids.split(':')[2]
            self.ids = self.db.get_ids(self.context, limit=int(limit))
            if self.ids.startswith('db:all'):
                # all ids of the context from the scrapy items table in the database
                self.ids = self.db.get_ids(self.context, limit=int(limit))
            elif self.ids.startswith('db:needed'):
                # all ids of the context from the scrapy items table in the database, that should be rescraped based on heuristics
                self.ids = self.db.get_ids(self.context, only_needed=True, limit=int(limit))
            else:
                raise ValueError('If you want the ids from the database please provide either "db:all:{NUMBER}" or '
                                 '"db:needed:{number}"')
        else:
            raise ValueError(
                f"Wrong format of the 'ids' argument, was {self.ids}, of type {type(self.ids)}, if you want to access "
                "the db, do not enable setting 'NO_DB'")

        for element_id in self.ids:
            yield details_request(details_url(element_id, self.context), 'de',
                                  refresh_cache=self.settings.getbool('HTTPCACHE_FORCE_REFRESH'),
                                  callback=self.parse_german, cb_kwargs=dict(element_id=element_id))

    def parse_german(self, response, element_id):
        loader = self.context_loader_cls()
        loader.add_value('id', element_id)
        return self.context_load_function(response, loader)

    # Project Stuff
    def load_project(self, response, loader):
        loader.add_value('name_de', self.get_name(response, accept_none=True, accept_mult=True))
        content = self.get_content_div(response)
        description_div = content.xpath('.//div[@id="projektbeschreibung"]')
        loader.add_value('beschreibung_de',
                         self.non_empty_text(description_div.xpath('./div[@id="projekttext"]'), err_mult=False))
        for row in description_div.xpath('./div[not(@id)]'):
            loader.add_value('attributes', self.attributes_pairs_list(row.xpath('./span')))

        attributes_div = content.xpath('./div[@class="details"]')
        for row in attributes_div.xpath('./div'):
            loader.add_value('attributes', self.attributes_pairs_list(row.xpath('./span')))

        return details_request(url_query_cleaner(response.url), 'en',
                               callback=self.parse_english_project, cb_kwargs=dict(project_item=loader.load_item()))

    def parse_english_project(self, response, project_item):
        project_loader = ProjectDetailsLoader()
        project_loader.add_value('name_en', self.get_name(response, accept_none=True, accept_mult=True))
        content = self.get_content_div(response)
        project_loader.add_value('beschreibung_en',
                                 self.non_empty_text(
                                     content.xpath('.//div[@id="projektbeschreibung"]/div[@id="projekttext"]'),
                                     err_mult=False))
        new_project_item = ProjectItem({**dict(project_item), **dict(project_loader.load_item())})
        if len(result_list := content.xpath('.//li[@id="tabbutton2"]/a')) == 1:
            return details_request(urljoin(url_query_cleaner(response.url), result_list.attrib['href']), 'de',
                                   callback=self.parse_project_result,
                                   cb_kwargs=dict(project_item=new_project_item))
        else:
            return new_project_item

    def parse_project_result(self, response, project_item, result_item=None):
        result_loader = ProjectResultLoader()
        result_content = response.css('#projektbeschreibung')
        summary = self.non_empty_text(result_content.xpath('./p'), err_mult=False)
        # this is the request for the english page, add the english summary to the result_loader
        # and set the result_item in the project_loader
        if result_item is not None:
            result_loader.add_value('ergebnis_zusammenfassung_en', summary)
            project_item['result'] = dict(ProjectResultItem(**dict(result_item), **dict(result_loader.load_item())))
            return project_item
        else:
            result_content = response.css('#projektbeschreibung')
            result_loader.add_value('ergebnis_zusammenfassung_de', summary)
            for div in result_content.xpath('./div'):
                result_loader.add_value('attributes', self.attributes_pairs_list(div.xpath('./span')))
            for publication in result_content.xpath('./ul[@class="publications"]/li'):
                result_loader.add_value('ergebnis_publikationen', self.extract_text_and_links(publication))
            # do the request for the english result page
            return details_request(url_query_cleaner(response.url), 'en', callback=self.parse_project_result,
                                   cb_kwargs=dict(project_item=project_item, result_item=result_loader.load_item()))

    # Person Stuff
    def load_person(self, response, loader):
        name = self.get_name(response, accept_none=False, accept_mult=False)
        loader.add_value('name_de', name)
        loader.add_value('verstorben', name)
        loader.add_value('gender', name)
        content = self.get_content_div(response)
        attributes_div = content.xpath('./div[@class="details"]')
        for row in attributes_div.xpath('./p'):
            loader.add_value('attributes', self.attributes_pairs_list(row.xpath('./span')))
        loader.add_value('trees', self.extract_trees(content))
        return loader.load_item()

    # Institution specific Stuff
    def load_institute(self, response, loader):
        loader.add_value('name_de', self.get_name(response, accept_none=False, accept_mult=True))
        content = self.get_content_div(response)
        attributes_div = content.xpath('.//div[@id="address_data"]')
        for row in attributes_div.xpath('./p'):
            loader.add_value('attributes', self.attributes_pairs_list(row.xpath('./span')))
        loader.add_value('trees', self.extract_trees(content))
        return loader.load_item()

    def get_name(self, response, accept_none=False, accept_mult=False):
        return self.non_empty_text(response.xpath('//h1[@class="facelift"]'), err_none=not accept_none,
                                   err_mult=not accept_mult)
