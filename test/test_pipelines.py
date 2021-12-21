from unittest import TestCase, skip
from unittest.mock import Mock, patch
from gepris_crawler.pipelines import EmailNotifierPipeline
from test.resources import get_settings, get_test_database, get_sample_dm_item


class ItemNotifierPipelineTest(TestCase):

    def setUp(self):
        self.settings = get_settings(database=True, mail=True)
        self.db = get_test_database(self.settings)

    def tearDown(self):
        self.db.close()

    def mock_spider(self, name, items_scraped, items_moved=None):
        def get_value_func(key, default_value):
            if key == 'item_scraped_count':
                return items_scraped
            elif key == 'item_moved_count' and items_moved is not None:
                return items_moved
            else:
                return default_value

        stats = Mock(get_value=Mock(side_effect=get_value_func), get_stats=Mock(return_value={}))
        spider = Mock(db=self.db, had_error=False, crawler=Mock(stats=stats))
        spider.name = name
        return spider

    def get_pipeline(self):
        return EmailNotifierPipeline.from_crawler(Mock(settings=self.settings))

    def test_had_error_flag(self):
        # setup
        spider = self.mock_spider('data_monitor', 1)
        pipeline = self.get_pipeline()
        spider.had_error = True
        with patch('gepris_crawler.pipelines.EmailNotifierPipeline._send') as mock_send:
            # test
            pipeline.close_spider(spider)
            # assertion
            mock_send.assert_called_once()
            self.assertEqual(mock_send.call_args.args[0], "Error - GeprisCrawler - Spider 'data_monitor' - 1 items")

    def test_data_monitor_mail_less_than_1_items(self):
        # setup
        pipeline = self.get_pipeline()
        spider = self.mock_spider('data_monitor', 0)
        with patch('gepris_crawler.pipelines.EmailNotifierPipeline._send') as mock_send:
            # test
            pipeline.close_spider(spider)
            # assertion
            mock_send.assert_called_once()
            self.assertEqual(mock_send.call_args.args[0],
                             "Warning - GeprisCrawler - Spider 'data_monitor' - 0 (-1) items")

    def test_data_monitor_mail_version_change(self):
        pipeline = self.get_pipeline()
        spider = self.mock_spider('data_monitor', 1)
        item = get_sample_dm_item()
        self.db.insert_data_monitor_run(item)
        new_item = get_sample_dm_item(version='18.5.7')
        with patch('gepris_crawler.pipelines.EmailNotifierPipeline._send') as mock_send:
            # test
            pipeline.process_item(new_item, spider)
            pipeline.close_spider(spider)
            # assertion
            mock_send.assert_called_once()
            self.assertEqual(mock_send.call_args.args[0],
                             "Warning - GeprisCrawler - Spider 'data_monitor' - 1 items - new gepris version 18.5.7")

    def test_data_monitor_no_mail(self):
        # setup
        pipeline = self.get_pipeline()
        spider = self.mock_spider('data_monitor', 1)
        with patch('gepris_crawler.pipelines.EmailNotifierPipeline._send') as mock_send:
            # test
            pipeline.close_spider(spider)
            # assertion
            mock_send.assert_not_called()

    def test_search_results_send_mail_less_projects_than_on_last_dm_run(self):
        # setup
        pipeline = self.get_pipeline()
        spider = self.mock_spider('search_results', 100)
        spider.context = 'projekt'
        self.db.insert_data_monitor_run(get_sample_dm_item(project=101))
        with patch('gepris_crawler.pipelines.EmailNotifierPipeline._send') as mock_send:
            # test
            pipeline.close_spider(spider)
            # assertion
            mock_send.assert_called_once()
            self.assertEqual(mock_send.call_args.args[0],
                             "Warning - GeprisCrawler - Spider 'search_results' - context 'projekt' - 100 (-1) items")

    def test_search_results_no_mail_less_person_than_on_last_dm_run(self):
        # setup
        pipeline = self.get_pipeline()
        spider = self.mock_spider('search_results', 100)
        spider.context = 'person'
        spider.total_items = 100
        self.db.insert_data_monitor_run(get_sample_dm_item(person=101))
        with patch('gepris_crawler.pipelines.EmailNotifierPipeline._send') as mock_send:
            # test
            pipeline.close_spider(spider)
            # assertion
            mock_send.assert_not_called()

    def test_search_results_send_mail_no_item_in_last_dm_run_and_less_than_total_items(self):
        # setup
        pipeline = self.get_pipeline()
        spider = self.mock_spider('search_results', 100)
        spider.total_items = 101
        spider.context = 'institution'
        with patch('gepris_crawler.pipelines.EmailNotifierPipeline._send') as mock_send:
            # test
            pipeline.close_spider(spider)
            # assertion
            mock_send.assert_called_once()
            self.assertEqual(mock_send.call_args.args[0],
                             "Warning - GeprisCrawler - Spider 'search_results' - context 'institution' - 100 (-1)"
                             " items")

    @skip('Disabled warning for institutions and persons because of buggy Gepris')
    def test_search_results_no_mail_equal_institutions_on_last_dm_run(self):
        # setup
        pipeline = self.get_pipeline()
        spider = self.mock_spider('search_results', 100)
        spider.context = 'institution'
        self.db.insert_data_monitor_run(get_sample_dm_item(institution=100))
        with patch('gepris_crawler.pipelines.EmailNotifierPipeline._send') as mock_send:
            # test
            pipeline.close_spider(spider)
            # assertion
            mock_send.assert_not_called()

    def test_details_send_mail_less_items_than_expected(self):
        # setup
        pipeline = self.get_pipeline()
        spider = self.mock_spider('details', 100)
        spider.ids = [i for i in range(101)]
        spider.context = 'projekt'
        with patch('gepris_crawler.pipelines.EmailNotifierPipeline._send') as mock_send:
            # test
            pipeline.close_spider(spider)
            # assertions
            mock_send.assert_called_once()
            self.assertEqual(mock_send.call_args.args[0],
                             "Warning - GeprisCrawler - Spider 'details' - context 'projekt' - 100 (-1) items")

    def test_details_send_mail_more_than_10000_items_scraped(self):
        # setup
        pipeline = self.get_pipeline()
        spider = self.mock_spider('details', 15000)
        spider.ids = [i for i in range(15000)]
        spider.context = 'projekt'
        with patch('gepris_crawler.pipelines.EmailNotifierPipeline._send') as mock_send:
            # test
            pipeline.close_spider(spider)
            # assertions
            mock_send.assert_called_once()
            self.assertEqual(mock_send.call_args.args[0],
                             "Success - GeprisCrawler - Spider 'details' - context 'projekt' - 15000 items")

    def test_details_no_mail_equal_items_items_as_expected(self):
        # setup
        pipeline = self.get_pipeline()
        spider = self.mock_spider('details', 100)
        spider.ids = [i for i in range(100)]
        spider.context = 'projekt'
        with patch('gepris_crawler.pipelines.EmailNotifierPipeline._send') as mock_send:
            # test
            pipeline.close_spider(spider)
            # assertions
            mock_send.assert_not_called()

    def test_details_no_mail_equal_items_items_as_expected_with_moved(self):
        # setup
        pipeline = self.get_pipeline()
        spider = self.mock_spider('details', 99, items_moved=1)
        spider.ids = [i for i in range(100)]
        spider.context = 'projekt'
        with patch('gepris_crawler.pipelines.EmailNotifierPipeline._send') as mock_send:
            # test
            pipeline.close_spider(spider)
            # assertions
            mock_send.assert_not_called()
