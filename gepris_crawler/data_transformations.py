import re
from datetime import datetime
from pytz import timezone
from .gepris_helper import is_gepris_path

CEST = timezone('Europe/Berlin')


################ HELPERS ################
def extract_id(url_path):
    if is_gepris_path(url_path):
        return url_path.split('/')[-1]


def extract_person_id(url_path):
    if is_gepris_path(url_path, context_to_check='person'):
        return extract_id(url_path)


def extract_institution_id(url_path):
    if is_gepris_path(url_path, context_to_check='institution'):
        return extract_id(url_path)


def extract_projekt_id(url_path):
    if is_gepris_path(url_path, context_to_check='projekt'):
        return extract_id(url_path)


def is_list_with_single_string(value):
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], str):
        return value


def is_reference(value):
    return isinstance(value, dict) and 'value' in value and 'path' in value


def keep_only_references(value):
    if is_reference(value):
        return value


def get_reference_value(value):
    return value['value']


def get_reference_path(value):
    return value['path']


def get_reference_children(value):
    return value.get('children')


def split_comma_space(value):
    return value.split(', ')


def transform(value, func, only_on_types=None):
    if isinstance(only_on_types, list) and type(value) in only_on_types:
        return func(value)


def map_possible_types(values, func, possible_types):
    return map(lambda v: func(v) if type(v) in possible_types else v, values)


def filter_strings(value, *strings):
    if value not in strings:
        return value


def filter_empty_string(value):
    return filter_strings(value, '')


def filter_parenthesis(value):
    return filter_strings(value, '(', ')')


def filter_no_abstracts_found(value):
    return filter_strings(value, 'Keine Zusammenfassung vorhanden', 'No abstract available')


def filter_no_address_found(value):
    return filter_strings(value, 'Es liegt keine aktuelle Dienstanschrift vor.', 'No current work address.', 'null')


def to_list(value):
    return [value]


def to_datetime(value, dateformat, only_date=False, remove_timezone=False):
    if remove_timezone:
        value = re.sub(r'CES?T ', '', value)
    dt = CEST.localize(datetime.strptime(value, dateformat))
    return dt.date() if only_date else dt


def remove_http_prefix(value):
    return value.removeprefix('http://').removeprefix('https://')


def remove_crucifix_suffix(value):
    return value.removesuffix('(†)')


def has_crucifix_prefix(value):
    return value.endswith('(†)')


def guess_gender_from_title(value):
    first_word_in_name = value.split()[0]
    if first_word_in_name == 'Professor' or first_word_in_name == 'Privatdozent':
        return 'male'
    elif first_word_in_name == 'Professorin' or first_word_in_name == 'Privatdozentin':
        return 'female'
    else:
        return 'unknown'


def clean_string(string):
    """
    This removes all non printable characters (like '&nbsp;', '\n', ...), and strips whitespace in front and end of string.
    It also removes multiple whitespaces in between a string.
    @param string:
    @return: cleaned string
    """
    cleaned_str = ''.join(c for c in string if c.isprintable())
    cleaned_str = ' '.join(cleaned_str.split())
    return cleaned_str.strip()


def drop_search_result_attribute(value_list, attribute_key, wrap_in_list=True):
    if value_list[0] != attribute_key:
        if wrap_in_list:
            return to_list(value_list)
        else:
            return value_list


# for debugging purposes
def do_nothing(value):
    return value
