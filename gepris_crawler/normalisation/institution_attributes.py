import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join, Compose
from .normalisation import normalise_attributes
from ..data_transformations import transform, get_reference_path, remove_http_prefix, filter_no_address_found,\
    is_list_with_single_string

ADRESSE = 'adresse'
MAIL = 'mail'
INTERNET = 'internet'
TELEFAX = 'telefax'
TELEFON = 'telefon'

INSTITUTION_ATTRIBUTES_MAP = {
    'Adresse': ADRESSE,
    'E-Mail': MAIL,
    'Internet': INTERNET,
    'Telefax': TELEFAX,
    'Telefon': TELEFON
}


class InstitutionAttributes(scrapy.Item):
    adresse = scrapy.Field()
    mail = scrapy.Field()
    internet = scrapy.Field()
    telefax = scrapy.Field()
    telefon = scrapy.Field()


class InstitutionAttributesLoader(scrapy.loader.ItemLoader):
    default_item_class = InstitutionAttributes
    default_output_processor = TakeFirst()
    adresse_in = Compose(lambda v: filter_no_address_found(v[0]) if is_list_with_single_string(v) else v)
    # we could also use the array, but joining it makes it more readable at the moment
    adresse_out = Join(', ')
    # do we really want to remove http and https?
    internet_in = MapCompose(lambda v: transform(v, get_reference_path, only_on_types=[dict]), remove_http_prefix)


def normalise(unstructured_attributes_dict):
    return normalise_attributes(unstructured_attributes_dict, InstitutionAttributesLoader(), INSTITUTION_ATTRIBUTES_MAP)
