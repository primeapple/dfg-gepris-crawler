from unittest import TestCase
from pypika import Query
from psycopg2.extras import Json
from datetime import datetime

from test.resources import get_settings, get_test_database


class DatabaseTest(TestCase):

    def setUp(self):
        self.settings = get_settings(database=True)
        self.db = get_test_database(self.settings)

    def tearDown(self):
        self.db.close()

    def test_projekte_references_view(self):
        # setup
        self.db.execute_sql(Query.into('spider_runs')
                            .insert(1, 'details', 'projekt', datetime.now(), datetime.now(), 1)
                            .get_sql()
                            )
        self.db.execute_sql(Query.into('available_items')
                            .insert(1, 'projekt', None, None, Json({'name_de': 'Testprojekt'}), 1, False)
                            .get_sql()
                            )
        self.db.execute_sql(Query.into('details_items_history')
                            .insert(1, 'projekt', 1,
                                    Json({'name_de': 'Testprojekt',
                                          'attributes': {
                                              'antragsteller_personen': [2, 3],
                                              'unternehmen_institutionen': [4],
                                              'partner_organisation_institutionen': [5]
                                          }}),
                                    'success')
                            .get_sql()
                            )

        # setup
        person_projekt_references = self.db.execute_sql('select * from latest_person_projekt_references', fetch=True)
        institution_projekt_references = self.db.execute_sql('SELECT * FROM latest_institution_projekt_references', fetch=True)

        # assertions
        self.assertCountEqual([(2, 1, 'antragsteller_personen'),
                              (3, 1, 'antragsteller_personen')], person_projekt_references)
        self.assertCountEqual([(4, 1, 'unternehmen_institutionen'),
                              (5, 1, 'partner_organisation_institutionen')], institution_projekt_references)
