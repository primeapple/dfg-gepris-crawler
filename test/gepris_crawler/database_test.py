import unittest
import resources.settings as s
from gepris_crawler.database import PostgresDatabase
from pypika import Query, Table, Field
from psycopg2.extras import Json
from datetime import datetime


class DatabaseTest(unittest.TestCase):

    def setUp(self):
        self.settings = s.get_settings(database=True)
        self.db = PostgresDatabase(self.settings)
        self.db.open()
        self.db.execute_sql('TRUNCATE spider_runs, data_monitor, projekte, personen, institutionen CASCADE')

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
