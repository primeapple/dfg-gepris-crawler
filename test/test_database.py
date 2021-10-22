from unittest import TestCase
from unittest.mock import Mock
from gepris_crawler.database import PostgresDatabase
from pypika import Query, Table
from psycopg2.extras import Json
from datetime import datetime
from pytz import timezone

from gepris_crawler.items import SearchResultItem, ProjectItem, DataMonitorItem
from test.resources.settings import get_settings


class DatabaseTest(TestCase):

    def setUp(self):
        self.settings = get_settings(database=True)
        self.db = PostgresDatabase(self.settings)
        self.db.open()
        self.db.execute_sql('TRUNCATE spider_runs, data_monitor, projekte, personen, institutionen CASCADE')
        self.db.execute_sql('ALTER SEQUENCE spider_runs_id RESTART')

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

    def test_create_references_from_details_run(self):
        self.fail()

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

    def test_insert_data_monitor_run(self):
        dm = Table('data_monitor')
        spider = Mock()
        spider.name = 'data_monitor'
        spider.run_id = 1
        item = DataMonitorItem(last_update=datetime(2021, 10, 19).date(),
                               last_approval=datetime(2021, 8, 19).date(),
                               finished_project_count=34878,
                               project_count=136387,
                               person_count=87700,
                               institution_count=37527,
                               humanities_count=25080,
                               life_count=48347,
                               natural_count=35151,
                               engineering_count=25475,
                               infrastructure_count=11066,
                               gepris_version='18.5.6',
                               current_index_version='dd5213f6-d21e-4177-960f-0450db3fb750',
                               current_index_date=timezone('Europe/Berlin').localize(datetime(2021, 10, 19, 7, 47, 33)))
        self.db.insert_data_monitor_run(item)
        results = self.db.execute_sql(Query.from_(dm).select(dm.star).get_sql(), fetch=True)
        results_without_current_timestamp = [r[1:] for r in results]
        expected_values = [tuple(dict(item).values())]
        self.assertListEqual(results_without_current_timestamp, expected_values)
        self.assertIsInstance(results[0][0], datetime)

    def test_store_run(self):
        runs = Table('spider_runs')
        run_id = self.db.store_run('details', 'projekt')
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
