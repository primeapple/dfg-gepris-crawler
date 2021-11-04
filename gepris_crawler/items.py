# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from abc import ABC

import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, Identity, MapCompose, Compose, Join
from .data_transformations import extract_id, filter_parenthesis, filter_no_abstracts_found, \
    filter_strings, to_list, filter_empty_string, to_datetime, clean_string, is_list_with_single_string, \
    has_crucifix_prefix, remove_crucifix_suffix, guess_gender_from_title
from .normalisation.project_attributes import normalise as nm_project
from .normalisation.project_result_attributes import normalise as nm_project_result
from .normalisation.person_attributes import normalise as nm_person
from .normalisation.institution_attributes import normalise as nm_institution
from .normalisation.trees import normalise_institution_trees, normalise_person_trees


################# ITEMS #################
class BasicItem(scrapy.Item):
    id = scrapy.Field()
    name_de = scrapy.Field()
    name_en = scrapy.Field()


class SearchResultItem(BasicItem):
    # only for project
    project_attributes = scrapy.Field()
    # only for person and institution
    addresse = scrapy.Field()
    # only for institution
    uebergeordnete_institution = scrapy.Field()


class ProjectItem(BasicItem):
    attributes = scrapy.Field()
    beschreibung_de = scrapy.Field()
    beschreibung_en = scrapy.Field()
    result = scrapy.Field()


class ProjectResultItem(scrapy.Item):
    # TODO: extract informations like the people, the name, the link and maybe the pages of the publications
    # At least the title should be fairly easy to get
    ergebnis_publikationen = scrapy.Field()
    ergebnis_zusammenfassung_de = scrapy.Field()
    ergebnis_zusammenfassung_en = scrapy.Field()
    attributes = scrapy.Field()


class PersonItem(BasicItem):
    attributes = scrapy.Field()
    trees = scrapy.Field()
    verstorben = scrapy.Field()
    gender = scrapy.Field()


class InstitutionItem(BasicItem):
    attributes = scrapy.Field()
    trees = scrapy.Field()


class DataMonitorItem(scrapy.Item):
    last_update = scrapy.Field()
    last_approval = scrapy.Field()
    # entries by context
    finished_project_count = scrapy.Field()
    project_count = scrapy.Field()
    person_count = scrapy.Field()
    institution_count = scrapy.Field()
    # entries by research_area
    humanities_count = scrapy.Field()
    life_count = scrapy.Field()
    natural_count = scrapy.Field()
    engineering_count = scrapy.Field()
    infrastructure_count = scrapy.Field()
    # meta informations
    gepris_version = scrapy.Field()
    current_index_version = scrapy.Field()
    current_index_date = scrapy.Field()


################# LOADERS ################
class BasicLoader(scrapy.loader.ItemLoader):
    default_item_class = BasicItem
    default_output_processor = TakeFirst()
    id_in = MapCompose(int)


# Loaders for Search Results Spider

class SearchResultLoader(BasicLoader):
    default_item_class = SearchResultItem
    id_in = MapCompose(extract_id, BasicLoader.id_in)
    project_attributes_in = MapCompose(to_list)
    project_attributes_out = Compose(dict)
    # TODO: normalise the name based on the strings
    name_de_in = MapCompose(clean_string)
    name_en_in = MapCompose(clean_string)
    addresse_in = MapCompose(clean_string, filter_empty_string)
    addresse_out = Identity()
    uebergeordnete_institution_out = Compose(TakeFirst(), dict)


# Loaders for Details Spider

class AbstractDetailsLoader(BasicLoader, ABC):
    attributes_in = MapCompose(to_list)
    attributes_out = Compose(dict)


class ProjectDetailsLoader(AbstractDetailsLoader):
    default_item_class = ProjectItem
    name_de_out = Join()
    name_en_out = Join()
    attributes_out = Compose(AbstractDetailsLoader.attributes_out, nm_project, dict)
    beschreibung_de_in = Compose(lambda v: filter_no_abstracts_found(v[0]) if is_list_with_single_string(v) else v,
                                 MapCompose(clean_string))
    beschreibung_de_out = Join()
    beschreibung_en_in = Compose(lambda v: filter_no_abstracts_found(v[0]) if is_list_with_single_string(v) else v,
                                 MapCompose(clean_string))
    beschreibung_en_out = Join()
    # we get info about "teilprojekte" in the attributes of the teilproject, so we don't have to collect them
    # within the parent project


class ProjectResultLoader(scrapy.loader.ItemLoader):
    default_item_class = ProjectResultItem
    default_output_processor = TakeFirst()
    ergebnis_publikationen_in = Compose(
        MapCompose(filter_parenthesis, lambda v: filter_strings(v, '(Siehe online unter')),
        to_list
    )
    ergebnis_publikationen_out = Identity()
    ergebnis_zusammenfassung_de_in = Compose(
        lambda v: filter_no_abstracts_found(v[0]) if is_list_with_single_string(v) else v,
        MapCompose(clean_string))
    ergebnis_zusammenfassung_de_out = Join()
    ergebnis_zusammenfassung_en_in = Compose(
        lambda v: filter_no_abstracts_found(v[0]) if is_list_with_single_string(v) else v,
        MapCompose(clean_string))
    ergebnis_zusammenfassung_en_out = Join()
    attributes_out = Compose(dict, nm_project_result, dict)


class PersonDetailsLoader(AbstractDetailsLoader):
    default_item_class = PersonItem
    name_de_in = MapCompose(remove_crucifix_suffix)
    verstorben_in = MapCompose(has_crucifix_prefix)
    gender_in = MapCompose(guess_gender_from_title)
    attributes_out = Compose(AbstractDetailsLoader.attributes_out, nm_person, dict)
    trees_out = Compose(TakeFirst(), normalise_person_trees)


class InstitutionDetailsLoader(AbstractDetailsLoader):
    default_item_class = InstitutionItem
    # do we really want to join here? we loose information but it is more readable
    # see https://gepris.dfg.de/gepris/institution/260863308 for an institution with multiple lines
    name_de_out = Join(', ')
    attributes_out = Compose(AbstractDetailsLoader.attributes_out, nm_institution, dict)
    trees_out = Compose(TakeFirst(), normalise_institution_trees)


# loader for other spiders

class DataMonitorLoader(scrapy.loader.ItemLoader):
    default_item_class = DataMonitorItem
    default_output_processor = Compose(TakeFirst(), int)
    last_update_out = Compose(TakeFirst(), lambda x: to_datetime(x, '%d.%m.%Y', only_date=True))
    last_approval_out = Compose(TakeFirst(), lambda x: to_datetime(x, '%d.%m.%Y', only_date=True))
    gepris_version_out = TakeFirst()
    current_index_version_out = TakeFirst()
    current_index_date_out = Compose(TakeFirst(), lambda x: to_datetime(x, '%a %b %d %H:%M:%S %Y',
                                                                        only_date=False, remove_timezone=True))
