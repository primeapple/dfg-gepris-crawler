# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import pprint

from scrapy.mail import MailSender
from scrapy.exceptions import NotConfigured


class DatabaseInsertionPipeline:
    """
    This Pipeline currently only works for a crawler with only one spider at a time
    """

    @classmethod
    def from_crawler(cls, crawler):
        if crawler.settings.getbool('NO_DB'):
            raise NotConfigured
        else:
            return cls()

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        if spider.name == 'data_monitor':
            return

        spider.logger.info(f'Finishing run {spider.run_id} of {spider.name}, doing last database operations')
        scraped_items = spider.crawler.stats.get_value('item_scraped_count', 0)
        if spider.name == 'details':
            spider.db.update_run_result(spider.run_id, scraped_items)
            if spider.context == 'projekt':
                # TODO: also create non existing institutionen references from details run
                spider.db.create_personen_references_from_details_run(spider)
            else:
                spider.db.mark_detail_check_needed_on_projekts_for_moved_person_institution(spider)
                if spider.context == 'institution':
                    spider.db.mark_detail_check_needed_on_root_institutions_for_moved_sub_institution(spider)
        elif spider.name == 'search_results':
            spider.db.update_run_result(spider.run_id, scraped_items)
            spider.db.mark_not_found_available_items(spider)
        spider.logger.info('Database operations done')

    def process_item(self, item, spider):
        if spider.name == 'search_results':
            spider.db.upsert_available_item(item['id'], item, spider)
        elif spider.name == 'details':
            spider.db.upsert_available_item(item['id'], None, spider)
            spider.db.insert_detail_item(item['id'], item, spider, 'success')
        elif spider.name == 'data_monitor':
            spider.db.insert_data_monitor_run(item)
        return item


class EmailNotifierPipeline:
    latest_gepris_version = None
    new_gepris_version = None
    DETAIL_MAIL_SUCCESS_MIN_ITEMS = 10000

    def __init__(self, settings):
        self.mailer = MailSender.from_settings(settings)
        self.receiver = settings.get('MAIL_RECEIVER')

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        if not settings.get('MAIL_RECEIVER') \
                or not settings.get('MAIL_FROM') \
                or not settings.get('MAIL_USER') \
                or not settings.get('MAIL_PASS') \
                or not settings.get('MAIL_HOST') \
                or not settings.get('MAIL_PORT') \
                or settings.getbool('NO_DB'):
            raise NotConfigured
        else:
            return cls(settings)

    def open_spider(self, spider):
        if spider.name == 'data_monitor':
            self.latest_gepris_version = spider.db.get_latest_dm_stat('gepris_version')

    def process_item(self, item, spider):
        if spider.name == 'data_monitor' and item['gepris_version'] != self.latest_gepris_version:
            self.new_gepris_version = item['gepris_version']

    def close_spider(self, spider):
        scraped_items = spider.crawler.stats.get_value('item_scraped_count', 0) + \
                        spider.crawler.stats.get_value('item_moved_count', 0)
        expected_items = self._get_expected_items(spider)
        if spider.had_error:
            subject = self._build_subject(spider, 'Error', scraped_items, expected_items)
        elif scraped_items != expected_items:
            subject = self._build_subject(spider, 'Warning', scraped_items, expected_items)
        elif spider.name == 'data_monitor' and self.new_gepris_version is not None:
            subject = self._build_subject(spider, 'Warning', scraped_items, expected_items,
                                          f"new gepris version {self.new_gepris_version}")
        elif spider.name == 'details' and scraped_items > self.DETAIL_MAIL_SUCCESS_MIN_ITEMS:
            subject = self._build_subject(spider, 'Success', scraped_items, expected_items)
        else:
            return
        body = f"Summary stats from Scrapy spider: \n\n{pprint.pformat(spider.crawler.stats.get_stats())}"
        self._send(subject, body)

    def _build_subject(self, spider, status, actual_items, expected_items, additional_message=None):
        context_string = ''
        if spider.name != 'data_monitor':
            context_string = f" - context '{spider.context}'"
        difference = actual_items - expected_items
        if difference != 0:
            items_string = f" - {actual_items} ({difference}) items"
        else:
            items_string = f" - {actual_items} items"
        if additional_message is None:
            additional_message = ''
        else:
            additional_message = f" - {additional_message}"
        return f"{status} - GeprisCrawler - Spider '{spider.name}'" \
               f"{context_string}" \
               f"{items_string}" \
               f"{additional_message}"

    def _get_expected_items(self, spider):
        if spider.name == 'data_monitor':
            return 1
        elif spider.name == 'search_results':
            if spider.context == 'projekt':
                items = spider.db.get_latest_dm_stat('project_count')
                if items is not None:
                    return items
            # either persons or institutions that are bugged (not all entities can be found in search_results spider)
            # or there is no dm run yet
            return spider.total_items
        elif spider.name == 'details':
            return len(spider.ids)

    def _send(self, subject, body):
        self.mailer.send(to=[self.receiver], subject=subject, body=body)
