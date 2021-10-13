import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose
from .normalisation import normalise_attributes

ERSTELLUNG_RESULT = 'ergebnis_erstellungsjahr'
PROJEKT_RESULT_ATTRIBUTES_MAP = {
    'Erstellungsjahr': ERSTELLUNG_RESULT
}


class ProjectResultAttributes(scrapy.Item):
    ergebnis_erstellungsjahr = scrapy.Field()


class ProjectResultAttributesLoader(scrapy.loader.ItemLoader):
    default_item_class = ProjectResultAttributes
    default_output_processor = TakeFirst()
    ergebnis_erstellungsjahr_in = MapCompose(int)


def normalise(unstructured_attributes_dict):
    return normalise_attributes(unstructured_attributes_dict, ProjectResultAttributesLoader(), PROJEKT_RESULT_ATTRIBUTES_MAP)
