# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import pprint

from scrapy.mail import MailSender
from itemadapter import ItemAdapter
from scrapy.exceptions import NotConfigured

class DatabaseInsertionPipeline:
    """
    This Pipeline currently only works for a crawler with only one spider at a time
    """

    def __init__(self):
        self.scraped_items = 0

    @classmethod
    def from_crawler(cls, crawler):
        if crawler.settings.getbool('NO_DB'):
            raise NotConfigured
        else:
            return cls()

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        if spider.name == 'details':
            spider.db.update_run_result(spider.run_id, self.scraped_items)
            if spider.context == 'projekt':
                spider.db.create_references_from_details_run(spider)
        elif spider.name == 'search_results':
            spider.db.update_run_result(spider.run_id, self.scraped_items)
            spider.db.mark_not_found_available_items(spider)

    def process_item(self, item, spider):
        if spider.name == 'search_results':
            spider.db.upsert_available_item(item['id'], item, spider)
        elif spider.name == 'details':
            spider.db.upsert_available_item(item['id'], None, spider)
            spider.db.insert_detail_item(item['id'], item, spider, 'success')
        elif spider.name == 'data_monitor':
            spider.db.insert_data_monitor_run(item)
        self.scraped_items += 1
        return item


class EmailNotifierPipeline:

    def __init__(self, settings):
        self.mailer = MailSender.from_settings(settings)
        self.receiver = settings.get('MAIL_RECEIVER')

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        if crawler.spider.name == 'data_monitor' \
                or settings.get('MAIL_RECEIVER') is None \
                or settings.get('MAIL_FROM') is None \
                or settings.get('MAIL_USER') is None \
                or settings.get('MAIL_PASS') is None \
                or settings.get('MAIL_HOST') is None \
                or settings.get('MAIL_PORT') is None:
            raise NotConfigured
        else:
            return cls(settings)

    def close_spider(self, spider):
        scraped_items = spider.crawler.stats.get_value('item_scraped_count')
        if scraped_items is None:
            scraped_items = 0
        if spider.name == 'details':
            expected_items = f" ({len(spider.ids)})"
        else:
            expected_items = ''
        subject = f"GeprisCrawler - Spider '{spider.name}' - '{spider.context}' finished, " \
                  f"{scraped_items}{expected_items} items"
        message = f"Summary stats from Scrapy spider: \n\n{pprint.pformat(spider.crawler.stats.get_stats())}"
        self.mailer.send(to=[self.receiver], subject=subject, body=message)
