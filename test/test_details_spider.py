import unittest

import scrapy
from psycopg2.extras import Json
from pypika import Query

from gepris_crawler.spiders.details import DetailsSpider
from test.resources import responses, get_settings, get_test_database


class DetailsSpiderTest(unittest.TestCase):
    maxDiff = None

    def test_ids_parsing(self):
        # db setup
        self.settings = get_settings(database=True)
        self.db = get_test_database(self.settings)
        self.db.store_run('search_results', 'projekt')
        self.db.store_run('details', 'projekt')
        self.db.execute_sql(Query.into('available_items')
                            .insert(1, 'projekt', 1, 1, None, None, True)
                            .insert(2, 'projekt', 1, 1, None, None, True)
                            .insert(3, 'projekt', 1, 1, Json({'name_de': 'test3'}), 2, False)
                            .insert(4, 'projekt', 1, 1, Json({'name_de': 'test4'}), 2, False)
                            .get_sql()
                            )
        self.db.close()

        # parsing test
        spider = DetailsSpider(context='person', ids='[0,1]', settings=self.settings)
        self.assertIsInstance(spider.ids, set)
        self.assertListEqual(list(spider.ids),  [0, 1])

        spider = DetailsSpider(context='projekt', ids='db:needed:4', settings=self.settings)
        self.assertIsInstance(spider.ids, set)
        self.assertListEqual(list(spider.ids),  [1, 2])

        spider = DetailsSpider(context='projekt', ids='db:all:4', settings=self.settings)
        self.assertIsInstance(spider.ids, set)
        self.assertListEqual(list(spider.ids),  [1, 2, 3, 4])

    def test_projekt_without_result(self):
        expected_item = {
            'id': 289879542,
            'name_de': 'Intergiertes Graduiertenkolleg (MGK)',
            'beschreibung_de': 'Das Teilprojekt bietet qualitativ hochwertige Doktorandenausbildung für SFB-Forscher, '
                               'in Koordination mit der Saarbrücken Graduate School of Computer Science.',
            'attributes': {
                'foerderung_beginn': 2016,
                'foerderung_ende': 2019,
                'dfg_verfahren': 'Sonderforschungsbereiche',
                'teil_projekt': 272573906,
                'antragstellende_institutionen': [10335],
                'teilprojekt_leiter_personen': [1710561],
                'dfg_ansprechpartner': 'Dr. Andreas Raabe',
                'fachliche_zuordnungen': 'Softwaretechnik und Programmiersprachen',
                'male_personen': [1710561],
                'female_personen': []
            }
        }
        request = self._test_parse_german_projekt('projekt', 289879542, 'details/projekt_289879542_de_22102021.html')
        item = request.cb_kwargs['project_item']
        self.assertIsInstance(item, scrapy.Item)
        self.assertEqual(dict(item), expected_item)
        self.assertEqual(request.url, 'https://gepris.dfg.de/gepris/projekt/289879542?language=en')

        item = self._test_parse_german_projekt('projekt', 289879542, 'details/projekt_289879542_en_22102021.html',
                                               request=request)
        self.assertIsInstance(item, scrapy.Item)
        expected_item['name_en'] = 'Integrated Research Training Group (MGK)'
        expected_item['beschreibung_en'] = expected_item['beschreibung_de']
        self.assertEqual(dict(item), expected_item)

    def test_projekt_with_result(self):
        self.fail()

    def test_person(self):
        item = {
            'id': 215969423,
            'name_de': 'Professor Dr. Oliver Cornely',
            'verstorben': False,
            'gender': 'male',
            'attributes': {
                'adresse': 'Universitätsklinikum Köln, Zentrum für Klinische Studien Köln (ZKS),'
                           ' Herder Straße 52-54, 50931 Köln',
                'internet': 'tinyurl.com/cornelylab'
            }
        }
        result_dict = self._test_parse_german_non_projekt('person', 215969423,
                                                          'details/person_215969423_de_22102021.html')
        result_dict.pop('trees', None)
        self.assertDictEqual(result_dict, item)

    def test_institution(self):
        item = {
            'id': 12957,
            'name_de': 'Burg Giebichenstein Kunsthochschule Halle',
            'attributes': {
                'adresse': 'Neuwerk 7, 06108 Halle, Deutschland',
                'telefon': '+49 345 7751-510',
                'telefax': '+49 345 7751-509',
                'mail': 'kanzlerin@burg-halle.de',
                'internet': 'www.burg-halle.de'
            },
            'trees': {
                'normalised_subinstitutions': [
                    '980513',
                    {
                        '980512': ['981182']
                    },
                    '460342185'
                ]
            }
        }
        result_dict = self._test_parse_german_non_projekt('institution', 12957,
                                                          'details/institution_12957_de_22102021.html')
        result_dict['trees'].pop('projekteNachProgrammen', None)
        result_dict['trees'].pop('untergeordneteInstitutionen', None)
        self.assertDictEqual(result_dict, item)

    def _test_parse_german_non_projekt(self, context, element_id, file):
        spider = DetailsSpider(context=context, ids=f'[{element_id}]', settings=get_settings(database=False))
        response = responses.fake_response_from_file(file)
        self.assertEqual(response.meta['expected_language'], 'de')
        result = spider.parse_german(response, element_id)
        self.assertIsInstance(result, scrapy.Item)
        return dict(result)

    def _test_parse_german_projekt(self, context, element_id, file, request=None):
        spider = DetailsSpider(context=context, ids=f'[{element_id}]', settings=get_settings(database=False))
        response = responses.fake_response_from_file(file, request=request)
        if request is None:
            result = spider.parse_german(response, element_id)
            self.assertIsInstance(result, scrapy.Request)
            self.assertEqual(response.meta['expected_language'], 'de')
            self.assertEqual(result.meta['expected_language'], 'en')
        else:
            result = spider.parse_english_project(response, response.cb_kwargs['project_item'])
        return result
