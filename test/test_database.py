from unittest import TestCase
from unittest.mock import Mock
from pypika import Query, Table
from psycopg2.extras import Json
from datetime import datetime

from gepris_crawler.items import SearchResultItem, ProjectItem
from test.resources import get_settings, get_test_database, get_sample_dm_item


class DatabaseTest(TestCase):

    def setUp(self):
        self.settings = get_settings(database=True)
        self.db = get_test_database(self.settings)

    def tearDown(self):
        self.db.close()

    def test_get_ids(self):
        self.db.execute_sql(Query.into('spider_runs')
                            .insert(1, 'search_results', 'projekt', datetime.now(), datetime.now(), 4)
                            .insert(2, 'details', 'projekt', datetime.now(), datetime.now(), 1)
                            .insert(3, 'details', 'projekt', datetime.now(), datetime.now(), 1)
                            .get_sql()
                            )
        self.db.execute_sql(Query.into('available_items')
                            .insert(3, 'projekt', 1, 1, Json({'name_de': 'test3'}), 2, False)
                            .insert(4, 'projekt', 1, 1, Json({'name_de': 'test4'}), 1, True)
                            .insert(1, 'projekt', 1, 1, Json({'name_de': 'test1'}), None, True)
                            .insert(2, 'projekt', 1, 1, Json({'name_de': 'test2'}), None, True)
                            .get_sql()
                            )
        self.assertListEqual(self.db.get_ids('projekt'), [1, 2, 4, 3])
        self.assertListEqual(self.db.get_ids('projekt', limit=2), [1, 2])
        self.assertListEqual(self.db.get_ids('projekt', only_needed=True), [1, 2, 4])
        self.assertListEqual(self.db.get_ids('projekt', limit=2, only_needed=True), [1, 2])
        self.assertListEqual(self.db.get_ids('person', limit=2, only_needed=True), [])

    def test_upsert_available_items_search_results(self):
        self.db.execute_sql(Query.into('spider_runs')
                            .insert(1, 'search_results', 'projekt', datetime.now(), datetime.now(), 1)
                            .insert(2, 'search_results', 'projekt', datetime.now(), datetime.now(), 1)
                            .insert(3, 'search_results', 'projekt', datetime.now(), datetime.now(), 1)
                            .insert(4, 'details', 'projekt', datetime.now(), datetime.now(), 2)
                            .insert(5, 'search_results', 'projekt', datetime.now(), datetime.now(), 1)
                            .get_sql()
                            )
        items = Table('available_items')
        spider = Mock()
        spider.context = 'projekt'
        spider.run_id = 1
        spider.name = 'search_results'
        item = SearchResultItem(id=1, name_de='p1')

        self.db.upsert_available_item(1, item, spider)
        results = self.db.execute_sql(Query.from_(items).select(items.star).get_sql(), fetch=True)
        self.assertListEqual(results, [(1, 'projekt', 1, 1, dict(item), None, True)])

        spider.run_id = 2
        self.db.upsert_available_item(1, item, spider)
        results = self.db.execute_sql(Query.from_(items).select(items.star).get_sql(), fetch=True)
        self.assertListEqual(results, [(1, 'projekt', 2, 1, dict(item), None, True)])

        spider.run_id = 3
        item['name_de'] = 'p3'
        self.db.upsert_available_item(1, item, spider)
        results = self.db.execute_sql(Query.from_(items).select(items.star).get_sql(), fetch=True)
        self.assertListEqual(results, [(1, 'projekt', 3, 3, dict(item), None, True)])

        spider.run_id = 4
        spider.name = 'details'
        detail_item = ProjectItem(id=1, name_de='details_p1')
        self.db.upsert_available_item(1, detail_item, spider)
        results = self.db.execute_sql(Query.from_(items).select(items.star).get_sql(), fetch=True)
        self.assertListEqual(results, [(1, 'projekt', 3, 3, dict(item), 4, False)])

        detail_item['id'] = 2
        self.db.upsert_available_item(2, detail_item, spider)
        results = self.db.execute_sql(Query.from_(items).select(items.star).where(items.id.eq(2)).get_sql(), fetch=True)
        self.assertListEqual(results, [(2, 'projekt', None, None, None, 4, False)])

        spider.run_id = 5
        spider.name = 'search_results'
        item['id'] = 2
        self.db.upsert_available_item(2, item, spider)
        results = self.db.execute_sql(Query.from_(items).select(items.star).where(items.id.eq(2)).get_sql(), fetch=True)
        self.assertListEqual(results, [(2, 'projekt', 5, 5, dict(item), 4, False)])

    def test_create_personen_references_from_details_run(self):
        # set up
        self.db.execute_sql(Query.into('spider_runs')
                            .insert(0, 'search_results', 'projekt', datetime.now(), datetime.now(), 1)
                            .insert(1, 'details', 'projekt', datetime.now(), datetime.now(), 1)
                            .get_sql()
                            )
        spider = Mock(context='projekt', run_id=0)
        spider.name = 'search_results'
        self.db.upsert_available_item(100, SearchResultItem(id=100, name_de='test'), spider)
        self.db.insert_detail_item(100, ProjectItem(id=100, attributes={'antragsteller_personen': [200]}),
                                   Mock(context='projekt', run_id=1), 'success')

        # test
        self.db.create_personen_references_from_details_run(Mock(run_id=1))

        # assertion
        available_items = Table('available_items')
        created_person = self.db.execute_sql(Query.from_(available_items)
                                             .select(available_items.star)
                                             .where(available_items.id.eq(200))
                                             .get_sql(),
                                             fetch=True)[0]
        self.assertEqual((200, 'person', None, None, None, None, True), created_person)

    def test_mark_not_found_available_items(self):
        # set up
        self.db.execute_sql(Query.into('spider_runs')
                            .insert(1, 'search_results', 'projekt', datetime.now(), datetime.now(), 1)
                            .insert(2, 'search_results', 'projekt', datetime.now(), datetime.now(), 0)
                            .get_sql()
                            )
        items = Table('available_items')
        spider = Mock()
        spider.context = 'projekt'
        spider.run_id = 1
        spider.name = 'search_results'
        item = SearchResultItem(id=1, name_de='p1')
        self.db.upsert_available_item(1, item, spider)

        # test
        spider.run_id = 2
        self.db.mark_not_found_available_items(spider)
        results = self.db.execute_sql(Query.from_(items).select(items.star).get_sql(), fetch=True)
        self.assertListEqual(results, [(1, 'projekt', 1, 2, None, None, True)])

    def test_mark_detail_check_needed_for_moved_items(self):
        # set up
        self.db.execute_sql(Query.into('spider_runs')
                            .insert(0, 'search_results', 'projekt', datetime.now(), datetime.now(), 1)
                            .insert(1, 'details', 'projekt', datetime.now(), datetime.now(), 1)
                            .insert(2, 'search_results', 'institution', datetime.now(), datetime.now(), 1)
                            .insert(3, 'details', 'institution', datetime.now(), datetime.now(), 0)
                            .get_sql()
                            )
        # inserting test project to available items
        spider = Mock(context='projekt', run_id=0)
        spider.name = 'search_results'
        self.db.upsert_available_item(100, SearchResultItem(id=100, name_de='test'), spider)
        # adding details run for test project
        spider.name = 'details'
        spider.run_id = 1
        self.db.upsert_available_item(100, None, spider)
        self.db.insert_detail_item(100, ProjectItem(id=100, attributes={'unternehmen_institutionen': [200]}),
                                   Mock(context='projekt', run_id=1), 'success')
        # adding moved run for other project, that is referenced by test project
        spider.context = 'institution'
        spider.run_id = 2
        self.db.upsert_available_item(200, None, spider)
        self.db.insert_detail_item(200, None, Mock(context='institution', run_id=3), 'moved')

        # test
        self.db.mark_detail_check_needed_for_moved_items(Mock(context='institution', run_id=3))

        # assertions
        available_items = Table('available_items')
        detail_check_needed = self.db.execute_sql(Query.from_(available_items)
                                                  .select(available_items.detail_check_needed)
                                                  .where(available_items.id.eq(100))
                                                  .get_sql(),
                                                  fetch=True)[0][0]
        self.assertEqual(detail_check_needed, True)

    def test_insert_data_monitor_run(self):
        dm = Table('data_monitor')
        spider = Mock()
        spider.name = 'data_monitor'
        spider.run_id = 1
        item = get_sample_dm_item()
        self.db.insert_data_monitor_run(item)
        results = self.db.execute_sql(Query.from_(dm).select(dm.star).get_sql(), fetch=True)
        results_without_current_timestamp = [r[1:] for r in results]
        expected_values = [tuple(dict(item).values())]
        self.assertListEqual(results_without_current_timestamp, expected_values)
        self.assertIsInstance(results[0][0], datetime)

    def test_store_run(self):
        # setup
        runs = Table('spider_runs')

        # test
        run_id = self.db.store_run('details', 'projekt')

        # assert
        self.assertEqual(run_id, 1)
        results = self.db.execute_sql(Query.select(runs.star).from_(runs).get_sql(), fetch=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 1)
        self.assertEqual(results[0][1], 'details')
        self.assertEqual(results[0][2], 'projekt')
        self.assertIsInstance(results[0][3], datetime)
        self.assertEqual(results[0][4], None)
        self.assertEqual(results[0][5], None)

    def test_update_run_result(self):
        # set up
        runs = Table('spider_runs')
        self.db.store_run('details', 'projekt')

        # test
        self.db.update_run_result(1, 10)

        # assert
        results = self.db.execute_sql(Query.select(runs.run_ended_at, runs.total_scraped_items).from_(runs).get_sql(),
                                      fetch=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]), 2)
        self.assertIsInstance(results[0][0], datetime)
        self.assertEqual(results[0][1], 10)

    def test_get_latest_dm_stat(self):
        # setup
        self.db.insert_data_monitor_run(get_sample_dm_item(version='1.0.0'))
        self.db.insert_data_monitor_run(get_sample_dm_item(version='1.0.1'))
        # test
        latest_version = self.db.get_latest_dm_stat('gepris_version')
        # assert
        self.assertEqual(latest_version, '1.0.1')

    def test_get_latest_dm_stat_without_previous_run(self):
        # test
        latest_version = self.db.get_latest_dm_stat('gepris_version')
        # assert
        self.assertEqual(latest_version, None)
