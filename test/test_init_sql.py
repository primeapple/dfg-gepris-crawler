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
        person_projekt_references = self.db.execute_sql('SELECT * FROM latest_person_projekt_references', fetch=True)
        institution_projekt_references = self.db.execute_sql('SELECT * FROM latest_institution_projekt_references',
                                                             fetch=True)

        # assertions
        self.assertCountEqual([(2, 1, 'antragsteller_personen'),
                               (3, 1, 'antragsteller_personen')], person_projekt_references)
        self.assertCountEqual([(4, 1, 'unternehmen_institutionen'),
                               (5, 1, 'partner_organisation_institutionen')], institution_projekt_references)

    def test_institutionen_hierarchy_view(self):
        # setup
        self.db.execute_sql(Query.into('spider_runs')
                            .insert(1, 'details', 'institution', datetime.now(), datetime.now(), 1)
                            .get_sql()
                            )
        self.db.execute_sql(Query.into('available_items')
                            .insert(1, 'institution', None, None, Json({'name_de': 'TestInstitution'}), 1, False)
                            .get_sql()
                            )
        self.db.execute_sql(Query.into('details_items_history')
                            .insert(1, 'institution', 1,
                                    Json({'name_de': 'Testprojekt',
                                          'trees': {
                                              'normalised_subinstitutions': [
                                                  '2',
                                                  {
                                                      '3': ['4', '5']
                                                  },
                                                  '6'
                                              ],
                                          }}),
                                    'success')
                            .get_sql()
                            )

        # setup
        institution_hierarchy = self.db.execute_sql('SELECT * FROM institution_hierarchy', fetch=True)

        # assertion
        self.assertCountEqual([(1, None, 1),
                               (2, 1, 1),
                               (3, 1, 1),
                               (4, 3, 1),
                               (5, 3, 1),
                               (6, 1, 1)
                               ], institution_hierarchy)
