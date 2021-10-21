import unittest
import types

import scrapy

from gepris_crawler.spiders.search_results import SearchResultsSpider
import resources.settings as s
import resources.responses as r


class SearchResultsSpiderTest(unittest.TestCase):

    def test_projekt(self):
        first_item = {
            'id': 269379,
            'name_de': 'GRK 60: Molekularbiologische Analyse pathophysiologischer Prozesse',
            'project_attributes': {
                'DFG-Verfahren': 'Graduiertenkollegs',
                'Fachkollegium': 'Grundlagen der Biologie und Medizin',
                'Förderung': '1996 bis 2002',
                'Sprecher': 'Eberhard Günther'
            }
        }
        self._test_parse('projekt', 'search_results/projekt_10_5_21102021.html', 5, first_item)

    def test_person(self):
        first_item = {
            'id': 5132,
            'name_de': 'Abromeit, Heidrun',
            'addresse': [
                'Technische Universität Darmstadt',
                'Fachbereich Gesellschafts- und Geschichtswissenschaften',
                'Institut für Politikwissenschaft'
            ]
        }
        self._test_parse('person', 'search_results/person_0_1_21102021.html', 1, first_item)

    def test_institution(self):
        first_item = {
            'id': 28761,
            'name_de': 'Professur für Personalpolitik',
            'addresse': ['Hamburg', 'Deutschland'],
            'uebergeordnete_institution': {
                'id': 10196,
                'name_de': 'Helmut-Schmidt-Universität'
            }
        }
        self._test_parse('institution', 'search_results/institution_9290_10_21102021.html', 10, first_item)
        fifth_item = {
            'id': 28768,
            'name_de': 'Lehrstuhl für Strafrecht, Strafprozeßrecht, Rechtsphilosophie und Rechtssoziologie',
            'addresse': ['Frankfurt am Main', 'Deutschland'],
            'uebergeordnete_institution': {
                'id': 10206,
                'name_de': 'Goethe-Universität Frankfurt am Main'
            }
        }
        self._test_parse('institution', 'search_results/institution_9290_10_21102021.html', 10, fifth_item, expected_item_index=4)

    def _test_parse(self, context, file, items_per_page, expected_item, expected_item_index=0):
        spider = SearchResultsSpider(context=context, items=items_per_page, settings=s.get_settings(database=False))
        result = spider.parse(r.fake_response_from_file(file), items_per_page)
        self.assertIsInstance(result, types.GeneratorType)
        items = [i for i in result]
        self.assertEquals(len(items), items_per_page)
        for item in items:
            self.assertIsInstance(item, scrapy.Item)
        item = items[expected_item_index]
        self.assertDictEqual(dict(item), expected_item)
