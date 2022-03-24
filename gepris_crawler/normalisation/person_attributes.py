import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join, Compose
from .normalisation import normalise_attributes
from ..data_transformations import filter_no_address_found, transform, get_reference_path, remove_http_prefix, \
    is_list_with_single_string, get_reference_value

ADRESSE = 'adresse'
MAIL = 'mail'
INTERNET = 'internet'
TELEFAX = 'telefax'
TELEFON = 'telefon'
ORCID_ID = 'orcid_id'

PERSON_ATTRIBUTES_MAP = {
    'Adresse': ADRESSE,
    'E-Mail': MAIL,
    'Internet': INTERNET,
    'Telefax': TELEFAX,
    'Telefon': TELEFON,
    'ORCID-ID': ORCID_ID
}


class PersonAttributes(scrapy.Item):
    adresse = scrapy.Field()
    mail = scrapy.Field()
    internet = scrapy.Field()
    telefax = scrapy.Field()
    telefon = scrapy.Field()
    orcid_id = scrapy.Field()


class PersonAttributesLoader(scrapy.loader.ItemLoader):
    default_item_class = PersonAttributes
    default_output_processor = TakeFirst()
    adresse_in = Compose(lambda v: filter_no_address_found(v[0]) if is_list_with_single_string(v) else v)
    # TODO: only keep numbers and '+' for telefon and telefax
    # we could also use the array, but joining it makes it more readable at the moment
    adresse_out = Join(', ')
    mail_out = Join('@')
    # do we really want to remove http and https?
    internet_in = MapCompose(lambda v: transform(v, get_reference_path, only_on_types=[dict]), remove_http_prefix)
    orcid_id_in = MapCompose(get_reference_value)


def normalise(unstructured_attributes_dict):
    return normalise_attributes(unstructured_attributes_dict, PersonAttributesLoader(), PERSON_ATTRIBUTES_MAP)
