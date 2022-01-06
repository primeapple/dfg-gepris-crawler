from abc import ABC
from collections.abc import Iterable

import scrapy

from ..database import PostgresDatabase
from ..data_transformations import clean_string
from ..gepris_helper import check_valid_context
from datetime import datetime
from pytz import timezone


def current_datetime():
    return datetime.now(timezone('Europe/Berlin'))


class BaseSpider(scrapy.Spider, ABC):
    """
    This class contains a collection of methods used in spiders for the gepris crawler
    """

    def __init__(self, context=None, settings=None, *args, **kwargs):
        super(BaseSpider, self).__init__(*args, **kwargs)
        self.had_error = False
        self.db = None
        if not settings.getbool('NO_DB'):
            self.db = PostgresDatabase(settings)
            self.db.open()
        # it is none only for data_monitor
        if context is not None:
            self.context = context
            check_valid_context(self.context)
            if self.db is not None:
                self.run_id = self.db.store_run(self.name, self.context)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = cls(settings=crawler.settings, *args, **kwargs)
        spider._set_crawler(crawler)
        return spider

    def attributes_pairs_list(self, span_selector_list):
        """
        Transforms selector lists like:
         [<span class="name">key1</span>,
          <span class="value">value1</span>,
          <span class="name">key2</span>
          <span class="value">value2</span>,
          <span class="name">key3</span>,
          <span class="name">key4</span>,
          <span class="value">value4</span>,
          <span class="name2">value5</span>,
          <span class="value">value5</span>,
          <span class="name"></span>,
          <span class="value">value6</span>]
        to list like:
         [["key1", "value1"],
          ["key2", "value2"],
          ["key3", None],
          ["key4", "value4"],
          ["key5", "value5"]]

        We then build a sublist
        @param span_selector_list: this is a list of span selectors
        @return: List of lists, each with size 2, like [key, value]
        """
        attributes = []
        last_key = None
        for span in span_selector_list:
            span_class = span.attrib.get('class')
            # no class given, happens at person and institute details page for example
            if span_class is None:
                if last_key is not None:
                    self.logger.info(f'No class given for value span on url {self.sel_url(span)}')
                    self.logger.debug(
                        f'No class given for span {span.get()}, treating it as value for last key {last_key.get()}')
                    attributes.append([self.non_empty_text(last_key), self.extract_text_and_links(span)])
                    last_key = None
                else:
                    self.logger.warning(f'No class given for key span on url {self.sel_url(span)}')
                    self.logger.debug(f'No class given for span {span.get()}, we were expecting a key, ignoring it.')
            # this is a key
            elif span_class.startswith('name'):
                if last_key is not None:
                    self.logger.warning(f'To consecutive keys found on url {self.sel_url(span)}')
                    self.logger.debug(
                        f'Two keys behind each other found: {last_key.get()}, {span.get()}, returning the first with null value')
                    attributes.append([self.non_empty_text(last_key), None])
                last_key = span
            # this is a value
            elif span_class.startswith('value'):
                if last_key is None:
                    self.logger.warning(f'Wrong key value structure found on url {self.sel_url(span)}')
                    self.logger.debug(
                        f'We expect an element with class "nameX" directly before an element with class "valueX" but there was not for value: {span.get()}')
                elif last_key.attrib['class'][4:] != span_class[5:]:
                    self.logger.warning(f'Wrong key value structure found on url {self.sel_url(span)}')
                    self.logger.debug(
                        f'We expect an element with class "nameX" directly before an element with class "valueX" but "X" was different: {last_key.get()}, {span.get()}')
                else:
                    last_key_text = self.non_empty_text(last_key, err_none=False)
                    if last_key_text is None:
                        self.logger.warning(f'Wrong key value structure found on url {self.sel_url(span)}')
                        self.logger.warn(f'There was an key element without any text for value element on url: {self.sel_url(span)}')
                    else:
                        attributes.append([last_key_text, self.extract_text_and_links(span)])
                    last_key = None
            # this is something unexpected
            else:
                self.logger.warning(f'Wrong key value structure found on url {self.sel_url(span)}')
                self.logger.debug(
                    f'Neither element with css class "nameX" or "valueX" found, instead: {span_class}')
        if last_key is not None:
            self.logger.info(f'Empty key found on url {self.sel_url(span_selector_list)}')
            self.logger.debug(
                f'Empty key found: {last_key.get()}, returning it with null value')
            attributes.append([self.non_empty_text(last_key), None])
        return attributes

    def extract_text_and_links(self, selector):
        """
        This maps all text, <div>, <span>, <em> and <a> children of this selector, like map:
         <span>
           Something
           <br>
           Another Thing
           <div>
            Thing in between
            <a href='betweentest'>PathBetween</a>
           </div>
           <a href='test'>Path</a>
           Last Thing
         </span>
        to list like:
         ['Something',
          'Another Thing',
          'Thing in between',
          {text:'PathBetween', path:'betweentest'},
          {text:'Path', path:'test'},
          'Last Thing'
         ]
        @param selector: Span Selector
        @return: List of Strings and Hashes
        """
        values = []
        for child in selector.xpath('./*|./text()'):
            if isinstance(child.root, str):
                cleaned = clean_string(child.get())
                if cleaned != '':
                    values.append(cleaned)
            elif child.attrib.get('href') is not None:
                values.append(dict(value=self.non_empty_text(child, err_none=False, err_mult=False),
                                   path=child.attrib.get('href')))
            else:
                child_value = self.extract_text_and_links(child)
                if isinstance(child_value, list):
                    values.extend(child_value)
                else:
                    values.append(child_value)
        return values[0] if len(values) == 1 else values

    def get_content_div(self, response):
        """
        Returns the main content div:
        <div id="content_inside">...
        </div>
        @param response: The Response given by scrapy
        @return: The main Content Div
        """
        return response.css('div.content_inside')

    def extract_trees(self, content):
        """
        Extract all Element trees given in the content div:
        Trees are all divs that fit the following xpath:
        content.xpath('./div[@class="content_frame"]/div[not(@class)]')
        @param content: the main content div
        @return: A hash, where each value is a tree and each key is the id of the div that contains the key
        """
        trees = {}
        for tree_div in content.xpath('./div[@class="content_frame"]/div[not(@class)]'):
            trees[tree_div.attrib['id']] = self.handle_tree_nodes(tree_div.xpath('./ul/li'))
        return trees

    def handle_tree_nodes(self, nodes):
        """
        Calls itself recursively to extract all the data from the tree
        @param nodes: A list of childnodes from a former node
        @return: A list, where each node is mapped to either it's text value, if it is a leaf
        or another subtree, when it has any children itself
        """
        mapped_nodes = []
        for node in nodes:
            children = node.xpath('./ul/li')
            # we are at a leaf in the tree
            if len(children) == 0:
                mapped_nodes.append(self.extract_text_and_links(node))
            # we are at a branch node in the tree, add a hash
            else:
                mapped_nodes.append({
                    'value': self.non_empty_text(node.xpath('./a'), err_mult=False),
                    'path': node.xpath('./a').attrib.get('href'),
                    'children': self.handle_tree_nodes(children)
                })
        return mapped_nodes

    # Maybe we could rewrite this to map <br> to actual linebreaks?
    def non_empty_text(self, selector, err_mult=True, err_none=True):
        """
        Extracts non empty cleaned text children of this selector
        @param selector: The selector to return text nodes from
        @param err_mult: Raises an error if there were multiple non empty text nodes
        @param err_none: Raises an error if there are no non empty text nodes
        @return: Either the single non empty text node if there is only one or a list of all the non emtpty strings (if `err_mult` is false) or None (if `err_none` is false)
        """
        non_empty_text_nodes = [clean_string(text) for text in selector.xpath('.//text()[normalize-space()]').getall()
                                if clean_string(text) != '']
        if len(non_empty_text_nodes) == 0:
            self.logger.info(
                f'Found no non-empty textnodes on url {self.sel_url(selector)} , returning None')
            if err_none:
                raise ValueError(f'No non empty text nodes on url {self.sel_url(selector)}')
            else:
                return None
        elif len(non_empty_text_nodes) > 1:
            self.logger.info(
                f'Found multiple non-empty textnodes on url {self.sel_url(selector)} , returning them')
            if err_mult:
                raise ValueError(
                    f'Multiple non-empty textnodes found on url {self.sel_url(selector)}')
            else:
                return non_empty_text_nodes
        else:
            return non_empty_text_nodes[0]

    def sel_url(self, selector):
        if isinstance(selector, Iterable):
            if len(selector) > 0:
                return selector[0].root.base_url
            else:
                raise ValueError(f'Selectorlist {selector} is empty, cant give url')
        else:
            return selector.root.base_url

    def closed(self, spider):
        if self.db is not None:
            self.db.close()
