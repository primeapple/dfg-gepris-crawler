import unittest
import resources.settings as s
from gepris_crawler.database import PostgresDatabase
from pypika import Query, Table, Field
from datetime import datetime


class DatabaseTest(unittest.TestCase):

    def setUp(self):
        self.settings = s.get_settings(database=True)
        self.db = PostgresDatabase(self.settings)
        self.db.open()
        self._insert_sample_data()

    def tearDown(self):
        self.db.execute_sql('TRUNCATE spider_runs, data_monitor, projekte, personen, institutionen CASCADE')
        self.db.close()

    def test_get_ids(self):
        self.assertEquals(len(self.db.get_ids('projekt')), 0)

    def _insert_sample_data(self):
        self.db.execute_sql(Query.into('spider_runs')
                            .insert(1, 'search_results', 'projekt', datetime.now(), datetime.now(), 10)
                            .insert(2, 'search_results', 'person', datetime.now(), datetime.now(), 10)
                            .insert(3, 'search_results', 'person', datetime.now(), datetime.now(), 10)
                            .get_sql()
                            )

