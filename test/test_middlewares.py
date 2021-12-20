from unittest import TestCase
from unittest.mock import Mock

from gepris_crawler.custom_exceptions import UnexpectedDetailsPageStructure
from gepris_crawler.middlewares import DetailsPageExpectedStructureCheckMiddleware
from test.resources import responses


class DetailsPageExpectedStructureCheckMiddlewareTest(TestCase):

    def test_unexpected_page_structure_failure(self):
        # setup
        middleware, spider = self._get_middleware_and_spider()
        response = responses.fake_response_from_file('details/projekt_441512655_de_17122021.html')
        # test/assertion
        self.assertRaises(UnexpectedDetailsPageStructure, middleware.process_spider_input, response, spider)

    def test_unexpected_page_structure_success(self):
        # setup
        middleware, spider = self._get_middleware_and_spider()
        response = responses.fake_response_from_file('details/projekt_491343583_de_12122021.html')
        # test
        result = middleware.process_spider_input(response, spider)
        # assertion
        self.assertIsNone(result)

    def _get_middleware_and_spider(self):
        spider = Mock()
        spider.name = 'details'
        middleware = DetailsPageExpectedStructureCheckMiddleware.from_crawler(Mock(spider=spider))
        return middleware, spider
