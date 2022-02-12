import unittest
import types

import scrapy

from gepris_crawler.spiders.search_results import SearchResultsSpider
from test.resources import responses, get_settings


class SearchResultsSpiderTest(unittest.TestCase):
    maxDiff = None

    def test_projekt(self):
        expected_item = {
            'id': 269379,
            'name_de': 'GRK 60: Molekularbiologische Analyse pathophysiologischer Prozesse',
            'project_attributes': {
                'DFG-Verfahren': 'Graduiertenkollegs',
                'Fachkollegium': 'Grundlagen der Biologie und Medizin',
                'Förderung': '1996 bis 2002',
                'Sprecher': 'Eberhard Günther'
            }
        }
        items = self._test_parse('projekt', 'search_results/projekt_10_5_21102021.html', 5)
        self.assertDictEqual(dict(items[0]), expected_item)

    def test_projekt_with_antragsteller_attribute(self):
        expected_item = {
            'id': 5076748,
            'name_de': 'Hochauflösende mm-Beobachtungen massereicher Protosterne',
            'project_attributes': {
                'DFG-Verfahren': 'Schwerpunktprogramme',
                'Fachliche Zuordnung': 'Astrophysik und Astronomie',
                'Förderung': '1997 bis 2002',
                'Teilprojekt zu': {
                    'path': "/gepris/projekt/5458045",
                    'value': "SPP 471"
                }
            }
        }
        items = self._test_parse('projekt', 'search_results/projekt_0_1_25112021.html', 1)
        self.assertDictEqual(dict(items[0]), expected_item)

    def test_projekt_with_antragsteller_innen_attribute(self):
        expected_item = {
            'id': 447999811,
            'name_de': 'Experimentelle und numerische Untersuchungen zu den Gründungen von Offshore-Windenergieanlagen in weichem marinem Taiwanesischem Ton unter kombinierter hochzyklischer und seismischer Belastung',
            'project_attributes': {
                'DFG-Verfahren': 'Sachbeihilfen',
                'Fachliche Zuordnung': 'Geotechnik, Wasserbau',
                'Förderung': 'Seit 2021'
            }
        }
        items = self._test_parse('projekt', 'search_results/projekt_0_1_28112021.html', 1)
        self.assertDictEqual(dict(items[0]), expected_item)

    def test_projekt_with_empty_item(self):
        items = self._test_parse('projekt', 'search_results/projekt_131490_5_03122021.html', 5, check_items_count=False)
        self.assertEqual(len(items), 4)

    def test_person(self):
        expected_item = {
            'id': 5132,
            'name_de': 'Abromeit, Heidrun',
            'addresse': [
                'Technische Universität Darmstadt',
                'Fachbereich Gesellschafts- und Geschichtswissenschaften',
                'Institut für Politikwissenschaft'
            ]
        }
        items = self._test_parse('person', 'search_results/person_0_1_21102021.html', 1)
        self.assertDictEqual(dict(items[0]), expected_item)

    def test_institution(self):
        expected_item = {
            'id': 28761,
            'name_de': 'Professur für Personalpolitik',
            'addresse': ['Hamburg', 'Deutschland'],
            'uebergeordnete_institution': {
                'id': 10196,
                'name_de': 'Helmut-Schmidt-Universität'
            }
        }
        items = self._test_parse('institution', 'search_results/institution_9290_10_21102021.html', 10)
        self.assertDictEqual(dict(items[0]), expected_item)

    def test_another_institution(self):
        expected_item = {
            'id': 28768,
            'name_de': 'Lehrstuhl für Strafrecht, Strafprozeßrecht, Rechtsphilosophie und Rechtssoziologie',
            'addresse': ['Frankfurt am Main', 'Deutschland'],
            'uebergeordnete_institution': {
                'id': 10206,
                'name_de': 'Goethe-Universität Frankfurt am Main'
            }
        }
        items = self._test_parse('institution', 'search_results/institution_9290_10_21102021.html', 10)
        self.assertDictEqual(dict(items[4]), expected_item)

    def test_set_total_items_success(self):
        spider = SearchResultsSpider(context='projekt', items=1, settings=get_settings(database=False))
        spider.set_total_items(responses.fake_response_from_file('search_results/projekt_0_1_12022022.html'))
        self.assertEqual(spider.total_items, 138127)

    def test_set_total_items_failure(self):
        spider = SearchResultsSpider(context='projekt', items=1, settings=get_settings(database=False))
        # response without any total items
        spider.set_total_items(responses.fake_response_from_file('data_monitor/03112021.html'))
        self.assertEqual(spider.total_items, 0)
        self.assertTrue(spider.had_error)

        # spider should not yield any results
        result = spider.parse(responses.fake_response_from_file('data_monitor/03112021.html'), 1)
        items = [i for i in result]
        self.assertListEqual(items, [])

    def _test_parse(self, context, file, items_per_page, check_items_count=True):
        spider = SearchResultsSpider(context=context, items=items_per_page, settings=get_settings(database=False))
        result = spider.parse(responses.fake_response_from_file(file), items_per_page)
        self.assertIsInstance(result, types.GeneratorType)
        items = [i for i in result]
        if check_items_count:
            self.assertEqual(len(items), items_per_page)
        for item in items:
            self.assertIsInstance(item, scrapy.Item)
        return items
