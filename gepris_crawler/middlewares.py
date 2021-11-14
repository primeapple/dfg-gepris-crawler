# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.exceptions import NotConfigured
from scrapy.utils.httpobj import urlparse_cached
from .custom_exceptions import UnexpectedLanguageError, PageDoesNotExistAnymoreError, UnexpectedDetailsPageStructure

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class ExceptionHandlerMiddleware:

    def process_spider_exception(self, response, exception, spider):
        meta = dict(response.request.meta, refresh_cache=True)
        if isinstance(exception, UnexpectedLanguageError):
            new_request_or_none = get_retry_request(
                response.request.replace(meta=meta),
                spider=spider,
                reason='Received Language did not fit expectation'
            )
        elif isinstance(exception, ValueError) and "error='UnexpectedFieldError:" in exception.args[0]:
            new_request_or_none = get_retry_request(
                response.request.replace(meta=meta),
                spider=spider,
                reason='Unexpected Field found'
            )
        elif isinstance(exception, PageDoesNotExistAnymoreError):
            spider.logger.warn(f'{exception} - Marking it as moved in the database')
            spider.crawler.stats.inc_value('item_moved_count')
            if self._insert_details_error(spider):
                spider.db.upsert_available_item(response.cb_kwargs['element_id'], None, spider)
                spider.db.insert_detail_item(response.cb_kwargs['element_id'], None, spider, 'moved')
            return []
        elif isinstance(exception, UnexpectedDetailsPageStructure):
            new_request_or_none = get_retry_request(
                response.request.replace(meta=meta),
                spider=spider,
                reason='Unexpected DetailsPageStructure'
            )
            if new_request_or_none is None and self._insert_details_error(spider):
                spider.logger.error(f'{exception} - Unknown DetailsPageStructure')
                spider.db.upsert_available_item(response.cb_kwargs['element_id'], None, spider)
                spider.db.insert_detail_item(response.cb_kwargs['element_id'], None, spider, 'error')
        else:
            return None
        # retry the request
        if new_request_or_none is not None:
            return [new_request_or_none]
        # do not process the request further (usually after 3 retries)
        else:
            return []

    def _insert_details_error(self, spider):
        return not spider.settings.getbool('NO_DB') and spider.name == 'details'


class DetailsPageExpectedStructureCheckMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        if crawler.spider.name != 'details':
            raise NotConfigured
        else:
            return cls()

    def process_spider_input(self, response, spider):
        # just trying to get something that should always be there
        context_title = response.css('*.h2-context-title::text').get()
        if context_title is None:
            raise UnexpectedDetailsPageStructure(f'Details Page {response.url} has an unexpected structure')
        else:
            return None


class DetailsPageExistsCheckMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        if crawler.spider.name != 'details':
            raise NotConfigured
        else:
            return cls()

    def process_spider_input(self, response, spider):
        context_title = response.css('*.h2-context-title::text').get()
        if context_title == 'Die angeforderte Seite konnte nicht gefunden werden.' or\
                context_title == 'The requested page was not found.':
            raise PageDoesNotExistAnymoreError(f'Page on {response.url} used to exist but was probably moved')
        else:
            return None


class LanguageCheckMiddleware:

    def process_spider_input(self, response, spider):
        if response.request.meta.get('expected_language') == 'en' and response.css('[title="Language"]::text').get() != 'Deutsch':
            raise UnexpectedLanguageError(f'Expected english language on page {response.url} but was german')
        elif response.request.meta.get('expected_language') == 'de' and response.css('[title="Sprache"]::text').get() != 'English':
            raise UnexpectedLanguageError(f'Expected german language on page {response.url} but was english')
        else:
            return None


# idea from https://stackoverflow.com/a/41774157
class RefreshHttpCachePolicy:

    def __init__(self, settings):
        self.ignore_schemes = settings.getlist('HTTPCACHE_IGNORE_SCHEMES')
        self.ignore_http_codes = [int(x) for x in settings.getlist('HTTPCACHE_IGNORE_HTTP_CODES')]

    def should_cache_request(self, request):
        return urlparse_cached(request).scheme not in self.ignore_schemes

    def should_cache_response(self, response, request):
        return response.status not in self.ignore_http_codes

    def is_cached_response_fresh(self, response, request):
        if 'refresh_cache' in request.meta:
            return False
        return True

    def is_cached_response_valid(self, cachedresponse, response, request):
        if 'refresh_cache' in request.meta:
            return False
        return True
