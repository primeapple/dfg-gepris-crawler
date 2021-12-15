import scrapy
from itemloaders.processors import TakeFirst, Identity, MapCompose
from scrapy.loader import ItemLoader
from .normalisation import normalise_attributes
from ..data_transformations import extract_person_id, extract_institution_id, extract_projekt_id, keep_only_references, \
    get_reference_path, get_reference_value, split_comma_space, transform

# Personen References Keys
## Constants
### Antragsteller
ANTRAGSTELLER_PERSONEN = 'antragsteller_personen'
AUSLAENDISCHE_ANTRAGSTELLER_PERSONEN = 'auslaendische_antragsteller_personen'
EHEMALIGE_ANTRAGSTELLER_PERSONEN = 'ehemalige_antragsteller_personen'
MIT_ANTRAGSTELLER_PERSONEN = 'mit_antragsteller_personen'
### Sprecher
SPRECHER_PERSONEN = 'sprecher_personen'
AUSLAENDISCHE_SPRECHER_PERSONEN = 'auslaendische_sprecher_personen'
CO_SPRECHER_PERSONEN = 'co_sprecher_personen'
### Leiter
LEITER_PERSONEN = 'leiter_personen'
STELLVERTRETER_PERSONEN = 'stellvertreter_personen'
TEILPROJEKT_LEITER_PERSONEN = 'teilprojekt_leiter_personen'
### Gastgeber
GASTGEBER_PERSONEN = 'gastgeber_personen'
### Kooperationspartner
KOOPERATIONSPARTNER_PERSONEN = 'kooperationspartner_personen'
### Beteiligte
BETEILIGTE_PERSONEN = 'beteiligte_personen'
BETEILIGTE_WISSENSCHAFTLER_PERSONEN = 'beteiligte_wissenschaftler_personen'
### Mitverantwortliche
MIT_VERANTWORTLICHE_PERSONEN = 'mit_verantwortliche_personen'
### IGK Partner (Sprecher)
IGK_PERSONEN = 'igk_personen'

## List of all personen References
PERSONEN_REFERENCES = [
    ANTRAGSTELLER_PERSONEN,
    AUSLAENDISCHE_ANTRAGSTELLER_PERSONEN,
    EHEMALIGE_ANTRAGSTELLER_PERSONEN,
    MIT_ANTRAGSTELLER_PERSONEN,
    SPRECHER_PERSONEN,
    AUSLAENDISCHE_SPRECHER_PERSONEN,
    CO_SPRECHER_PERSONEN,
    LEITER_PERSONEN,
    STELLVERTRETER_PERSONEN,
    TEILPROJEKT_LEITER_PERSONEN,
    GASTGEBER_PERSONEN,
    KOOPERATIONSPARTNER_PERSONEN,
    BETEILIGTE_PERSONEN,
    BETEILIGTE_WISSENSCHAFTLER_PERSONEN,
    MIT_VERANTWORTLICHE_PERSONEN,
    IGK_PERSONEN
]

# Institutionen References Keys
## Constants
### Antragsteller
ANTRAGSTELLENDE_INSTITUTIONEN = 'antragstellende_institutionen'
MIT_ANTRAGSTELLENDE_INSTITUTIONEN = 'mit_antragstellende_institutionen'
### Beteiligte
BETEILIGTE_INSTITUTIONEN = 'beteiligte_institutionen'
BETEILIGTE_EINRICHTUNGEN_INSTITUTIONEN = 'beteiligte_einrichtungen_institutionen'
BETEILIGTE_HOCHSCHULE_INSTITUTIONEN = 'beteiligte_hochschule_institutionen'
### Partner
ANWENDUNGS_PARTNER_INSTITUTIONEN = 'partner_institutionen'
PARTNER_ORGANISATION_INSTITUTIONEN = 'partner_organisation_institutionen'
### Unternehmen
UNTERNEHMEN_INSTITUTIONEN = 'unternehmen_institutionen'
### Auslaendische
AUSLAENDISCHE_INSTITUTIONEN = 'auslaendische_institutionen'
### IGK Partner
IGK_INSTITUTIONEN = 'igk_institutionen'

## List of all institutionen References
INSTITUTIONEN_REFERENCES = [
    ANTRAGSTELLENDE_INSTITUTIONEN,
    MIT_ANTRAGSTELLENDE_INSTITUTIONEN,
    BETEILIGTE_INSTITUTIONEN,
    BETEILIGTE_EINRICHTUNGEN_INSTITUTIONEN,
    BETEILIGTE_HOCHSCHULE_INSTITUTIONEN,
    ANWENDUNGS_PARTNER_INSTITUTIONEN,
    PARTNER_ORGANISATION_INSTITUTIONEN,
    UNTERNEHMEN_INSTITUTIONEN,
    AUSLAENDISCHE_INSTITUTIONEN,
    IGK_INSTITUTIONEN
]

# Other Project Attributes:
## Constants
DFG_ANSPRECHPARTNER = 'dfg_ansprechpartner'
INTERNATIONALER_BEZUG = 'internationaler_bezug'
GROSS_GERAETE = 'gross_geraete'
GERAETEGRUPPE = 'geraetegruppe'
DFG_VERFAHREN = 'dfg_verfahren'
FACHRICHTUNGEN = 'fachrichtungen'
FACHLICHE_ZUORDNUNGEN = 'fachliche_zuordnungen'
WEBSEITE = 'webseite'
TEIL_PROJEKT = 'teil_projekt'
PROJEKT_KENNUNG = 'projekt_kennung'  # like "Deutsche Forschungsgemeinschaft (DFG) - Projektnummer ${ID}"
FOERDERUNG_ZEITRAUM = 'foerderung_zeitraum'  # like "Förderung von ABCD bis DEFG" or "Förderung seit ABCD"
FOERDERUNG_BEGINN = 'foerderung_beginn'
FOERDERUNG_ENDE = 'foerderung_ende'

## List of all other attributes
OTHER_PROJEKT_ATTRIBUTES = [
    DFG_ANSPRECHPARTNER,
    INTERNATIONALER_BEZUG,
    GROSS_GERAETE,
    GERAETEGRUPPE,
    DFG_VERFAHREN,
    FACHRICHTUNGEN,
    FACHLICHE_ZUORDNUNGEN,
    WEBSEITE,
    TEIL_PROJEKT,
    PROJEKT_KENNUNG,
    FOERDERUNG_ZEITRAUM,
    FOERDERUNG_BEGINN,
    FOERDERUNG_ENDE
]

PROJEKT_ATTRIBUTES_MAP = {
    'Antragstellende Institution': ANTRAGSTELLENDE_INSTITUTIONEN,
    'Antragsteller': ANTRAGSTELLER_PERSONEN,
    'Antragstellerin': ANTRAGSTELLER_PERSONEN,
    'Antragstellerinnen': ANTRAGSTELLER_PERSONEN,
    'Antragstellerinnen / Antragsteller': ANTRAGSTELLER_PERSONEN,
    'Anwendungspartner': ANWENDUNGS_PARTNER_INSTITUTIONEN,
    'Beteiligte Einrichtung': BETEILIGTE_EINRICHTUNGEN_INSTITUTIONEN,
    'Beteiligte Fachrichtungen': FACHRICHTUNGEN,
    'Beteiligte Hochschule': BETEILIGTE_HOCHSCHULE_INSTITUTIONEN,
    'Beteiligte Institution': BETEILIGTE_INSTITUTIONEN,
    'Beteiligte Person': BETEILIGTE_PERSONEN,
    'Beteiligte Personen': BETEILIGTE_PERSONEN,
    'Co-Sprecher': CO_SPRECHER_PERSONEN,
    'Co-Sprecherin': CO_SPRECHER_PERSONEN,
    'Co-Sprecherinnen': CO_SPRECHER_PERSONEN,
    'Co-Sprecherinnen / Co-Sprecher': CO_SPRECHER_PERSONEN,
    'DFG-Verfahren': DFG_VERFAHREN,
    # TODO: extract informations: from when, to when
    'Ehemalige Antragsteller': EHEMALIGE_ANTRAGSTELLER_PERSONEN,
    'Ehemalige Antragstellerin': EHEMALIGE_ANTRAGSTELLER_PERSONEN,
    'Ehemalige Antragstellerinnen': EHEMALIGE_ANTRAGSTELLER_PERSONEN,
    'Ehemalige Antragstellerinnen / Ehemalige Antragsteller': EHEMALIGE_ANTRAGSTELLER_PERSONEN,
    'Ehemaliger Antragsteller': EHEMALIGE_ANTRAGSTELLER_PERSONEN,
    'Fachliche Zuordnung': FACHLICHE_ZUORDNUNGEN,
    'Förderung': FOERDERUNG_ZEITRAUM,
    'Gastgeber': GASTGEBER_PERSONEN,
    'Gastgeberin': GASTGEBER_PERSONEN,
    'Gastgeberinnen': GASTGEBER_PERSONEN,
    'Gastgeberinnen / Gastgeber': GASTGEBER_PERSONEN,
    'Gerätegruppe': GERAETEGRUPPE,
    'Großgeräte': GROSS_GERAETE,
    'Internationaler Bezug': INTERNATIONALER_BEZUG,
    'Kooperationspartner': KOOPERATIONSPARTNER_PERSONEN,
    'Kooperationspartnerin': KOOPERATIONSPARTNER_PERSONEN,
    'Kooperationspartnerinnen': KOOPERATIONSPARTNER_PERSONEN,
    'Kooperationspartnerinnen / Kooperationspartner': KOOPERATIONSPARTNER_PERSONEN,
    'Leiter': LEITER_PERSONEN,
    'Leiterin': LEITER_PERSONEN,
    'Leiterinnen': LEITER_PERSONEN,
    'Leiterinnen / Leiter': LEITER_PERSONEN,
    'Mitantragstellende Institution': MIT_ANTRAGSTELLENDE_INSTITUTIONEN,
    'Mitantragsteller': MIT_ANTRAGSTELLER_PERSONEN,
    'Mitantragstellerin': MIT_ANTRAGSTELLER_PERSONEN,
    'Mitantragstellerinnen': MIT_ANTRAGSTELLER_PERSONEN,
    'Mitantragstellerinnen / Mitantragsteller': MIT_ANTRAGSTELLER_PERSONEN,
    'Mitverantwortlich': MIT_VERANTWORTLICHE_PERSONEN,
    'Mitverantwortlich(e)': MIT_VERANTWORTLICHE_PERSONEN,
    'Mitverantwortliche': MIT_VERANTWORTLICHE_PERSONEN,
    'Partnerorganisation': PARTNER_ORGANISATION_INSTITUTIONEN,
    'Projektkennung': PROJEKT_KENNUNG,
    'Sprecher': SPRECHER_PERSONEN,
    'Sprecherin': SPRECHER_PERSONEN,
    'Sprecherinnen': SPRECHER_PERSONEN,
    'Sprecherinnen / Sprecher': SPRECHER_PERSONEN,
    'Stellvertreter': STELLVERTRETER_PERSONEN,
    'Stellvertreterin': STELLVERTRETER_PERSONEN,
    'Stellvertreterinnen': STELLVERTRETER_PERSONEN,
    'Stellvertreterinnen / Stellvertreter': STELLVERTRETER_PERSONEN,
    'Teilprojekt zu': TEIL_PROJEKT,
    'Teilprojektleiter': TEILPROJEKT_LEITER_PERSONEN,
    'Teilprojektleiterin': TEILPROJEKT_LEITER_PERSONEN,
    'Teilprojektleiterinnen': TEILPROJEKT_LEITER_PERSONEN,
    'Teilprojektleiterinnen / Teilprojektleiter': TEILPROJEKT_LEITER_PERSONEN,
    'Unternehmen': UNTERNEHMEN_INSTITUTIONEN,
    'Webseite': WEBSEITE,
    'ausländ. Mitantragstelleirinnen': AUSLAENDISCHE_ANTRAGSTELLER_PERSONEN,
    'ausländ. Mitantragstelleirinnen / ausländische Mitantragsteller': AUSLAENDISCHE_ANTRAGSTELLER_PERSONEN,
    'ausländ. Mitantragstellerinnen': AUSLAENDISCHE_ANTRAGSTELLER_PERSONEN,
    'ausländ. Mitantragstellerinnen / ausländische Mitantragsteller': AUSLAENDISCHE_ANTRAGSTELLER_PERSONEN,
    'ausländ. Mitantragstellerin': AUSLAENDISCHE_ANTRAGSTELLER_PERSONEN,
    'ausländischer Mitantragsteller': AUSLAENDISCHE_ANTRAGSTELLER_PERSONEN,
    'ausländische Mitantragsteller': AUSLAENDISCHE_ANTRAGSTELLER_PERSONEN,
    'ausländische Institution': AUSLAENDISCHE_INSTITUTIONEN,
    'ausländischer Sprecher': AUSLAENDISCHE_SPRECHER_PERSONEN,
    'ausländische Sprecher': AUSLAENDISCHE_SPRECHER_PERSONEN,
    'ausländische Sprecherin': AUSLAENDISCHE_SPRECHER_PERSONEN,
    'ausländische Sprecherinnen': AUSLAENDISCHE_SPRECHER_PERSONEN,
    'ausländische Sprecherinnen / ausländische Sprecher': AUSLAENDISCHE_SPRECHER_PERSONEN,
    'beteiligte Wissenschaftler': BETEILIGTE_WISSENSCHAFTLER_PERSONEN,
    'beteiligte Wissenschaftlerin': BETEILIGTE_WISSENSCHAFTLER_PERSONEN,
    'beteiligte Wissenschaftlerinnen': BETEILIGTE_WISSENSCHAFTLER_PERSONEN,
    'beteiligte Wissenschaftlerinnen / beteiligte Wissenschaftler': BETEILIGTE_WISSENSCHAFTLER_PERSONEN,
    'beteiligter Wissenschaftler': BETEILIGTE_WISSENSCHAFTLER_PERSONEN,
    'fachliche DFG-Ansprechpartnerin': DFG_ANSPRECHPARTNER,
    'fachlicher DFG-Ansprechpartner': DFG_ANSPRECHPARTNER,
    'Sprecher (IGK-Partner)': IGK_PERSONEN,
    'Sprecherin (IGK-Partner)': IGK_PERSONEN,
    'IGK-Partnerinstitution': IGK_INSTITUTIONEN,
}

# Gender types
UNKNOWN = 'unknown'
FEMALE = 'female'
MALE = 'male'

PROJEKT_PERSON_GENDER_MAP = {
    'Antragsteller': MALE,
    'Antragstellerin': FEMALE,
    'Antragstellerinnen': FEMALE,
    'Antragstellerinnen / Antragsteller': UNKNOWN,
    'Beteiligte Person': UNKNOWN,
    'Beteiligte Personen': UNKNOWN,
    'Co-Sprecher': MALE,
    'Co-Sprecherin': FEMALE,
    'Co-Sprecherinnen': FEMALE,
    'Co-Sprecherinnen / Co-Sprecher': UNKNOWN,
    'Ehemalige Antragsteller': MALE,
    'Ehemalige Antragstellerin': FEMALE,
    'Ehemalige Antragstellerinnen': FEMALE,
    'Ehemalige Antragstellerinnen / Ehemalige Antragsteller': UNKNOWN,
    'Ehemaliger Antragsteller': MALE,
    'Gastgeber': MALE,
    'Gastgeberin': FEMALE,
    'Gastgeberinnen': FEMALE,
    'Gastgeberinnen / Gastgeber': UNKNOWN,
    'Kooperationspartner': MALE,
    'Kooperationspartnerin': FEMALE,
    'Kooperationspartnerinnen': FEMALE,
    'Kooperationspartnerinnen / Kooperationspartner': UNKNOWN,
    'Leiter': MALE,
    'Leiterin': FEMALE,
    'Leiterinnen': FEMALE,
    'Leiterinnen / Leiter': UNKNOWN,
    'Mitantragsteller': MALE,
    'Mitantragstellerin': FEMALE,
    'Mitantragstellerinnen': FEMALE,
    'Mitantragstellerinnen / Mitantragsteller': UNKNOWN,
    'Mitverantwortlich': MALE,
    'Mitverantwortlich(e)': FEMALE,
    'Mitverantwortliche': UNKNOWN,
    'Sprecher': MALE,
    'Sprecherin': FEMALE,
    'Sprecherinnen': FEMALE,
    'Sprecherinnen / Sprecher': UNKNOWN,
    'Stellvertreter': MALE,
    'Stellvertreterin': FEMALE,
    'Stellvertreterinnen': FEMALE,
    'Stellvertreterinnen / Stellvertreter': UNKNOWN,
    'Teilprojektleiter': MALE,
    'Teilprojektleiterin': FEMALE,
    'Teilprojektleiterinnen': FEMALE,
    'Teilprojektleiterinnen / Teilprojektleiter': UNKNOWN,
    'ausländ. Mitantragstelleirinnen': FEMALE,
    'ausländ. Mitantragstelleirinnen / ausländische Mitantragsteller': UNKNOWN,
    'ausländ. Mitantragstellerinnen': FEMALE,
    'ausländ. Mitantragstellerinnen / ausländische Mitantragsteller': UNKNOWN,
    'ausländ. Mitantragstellerin': FEMALE,
    'ausländischer Mitantragsteller': MALE,
    'ausländische Mitantragsteller': MALE,
    'ausländischer Sprecher': MALE,
    'ausländische Sprecher': MALE,
    'ausländische Sprecherin': FEMALE,
    'ausländische Sprecherinnen': FEMALE,
    'ausländische Sprecherinnen / ausländische Sprecher': UNKNOWN,
    'beteiligte Wissenschaftler': MALE,
    'beteiligte Wissenschaftlerin': FEMALE,
    'beteiligte Wissenschaftlerinnen': FEMALE,
    'beteiligte Wissenschaftlerinnen / beteiligte Wissenschaftler': UNKNOWN,
    'beteiligter Wissenschaftler': MALE,
    'Sprecher (IGK-Partner)': MALE,
    'Sprecherin (IGK-Partner)': FEMALE,
}


# Split functions, each has to return a dict with the item_field_names and the corresponding values
def _parse_foerderung_zeitraum(value):
    if value.startswith('Förderung von '):
        begin, end = value.removeprefix('Förderung von ').split(' bis ')
        return {FOERDERUNG_BEGINN: begin, FOERDERUNG_ENDE: end}
    elif value.startswith('Förderung seit '):
        return {FOERDERUNG_BEGINN: value.removeprefix('Förderung seit ')}
    elif value.startswith('Förderung in '):
        return {FOERDERUNG_BEGINN: value.removeprefix('Förderung in ')}
    elif value.startswith('Förderung: Bis '):
        return {FOERDERUNG_ENDE: value.removeprefix('Förderung: Bis ')}
    elif value == 'Befindet sich in der laufenden Förderung.':
        return {}
    else:
        raise ValueError(f'Expected parsable dates, but got {value}')


KEYS_TO_REMOVE = [PROJEKT_KENNUNG]

KEYS_TO_PROCESS = {
    FOERDERUNG_ZEITRAUM: _parse_foerderung_zeitraum
}


class ProjectAttributes(scrapy.Item):
    fields = {}
    # set Person References fields
    fields.update({k: {} for k in PERSONEN_REFERENCES})
    # set Institution References fields
    fields.update({k: {} for k in INSTITUTIONEN_REFERENCES})
    # set other fields
    fields.update({k: {} for k in OTHER_PROJEKT_ATTRIBUTES})
    male_personen = scrapy.Field()
    female_personen = scrapy.Field()


class ProjectAttributesLoader(scrapy.loader.ItemLoader):
    default_item_class = ProjectAttributes
    default_output_processor = Identity()

    # overriding init to dynamically set processors for Person and Institution References
    def __init__(self, **kwargs):
        for attribute in PERSONEN_REFERENCES:
            setattr(self, f'{attribute}_in',
                    MapCompose(keep_only_references, get_reference_path, extract_person_id, int))
        for attribute in INSTITUTIONEN_REFERENCES:
            setattr(self, f'{attribute}_in',
                    MapCompose(keep_only_references, get_reference_path, extract_institution_id, int))
        super().__init__(**kwargs)

    # Setting other attribute loaders
    teil_projekt_in = MapCompose(keep_only_references, get_reference_path, extract_projekt_id, int)
    teil_projekt_out = TakeFirst()
    dfg_ansprechpartner_in = MapCompose(lambda v: transform(v, get_reference_value, only_on_types=[dict]))
    dfg_ansprechpartner_out = TakeFirst()
    internationaler_bezug_in = MapCompose(split_comma_space)
    # empty MapCompose to create a list
    gross_geraete_in = MapCompose()
    geraetegruppe_in = MapCompose()
    dfg_verfahren_out = TakeFirst()
    fachrichtungen_in = MapCompose(split_comma_space)
    fachliche_zuordnungen_out = TakeFirst()
    webseite_in = MapCompose(get_reference_path)
    webseite_out = TakeFirst()
    foerderung_beginn_in = MapCompose(int)
    foerderung_beginn_out = TakeFirst()
    foerderung_ende_in = MapCompose(int)
    foerderung_ende_out = TakeFirst()


def _parse_for_gender(original_key):
    if PROJEKT_PERSON_GENDER_MAP[original_key] == MALE:
        return MALE
    elif PROJEKT_PERSON_GENDER_MAP[original_key] == FEMALE:
        return FEMALE
    elif PROJEKT_PERSON_GENDER_MAP[original_key] == UNKNOWN:
        return UNKNOWN


def normalise(unstructured_attributes_dict):
    item = normalise_attributes(unstructured_attributes_dict, ProjectAttributesLoader(),
                                keys_to_process=KEYS_TO_PROCESS, keys_to_remove=KEYS_TO_REMOVE,
                                attributes_map=PROJEKT_ATTRIBUTES_MAP)
    # the following adds male and female keys for persons which gender can be guessed by the person references keys
    male_personen = set()
    female_personen = set()
    seen_personen_keys = []
    for key in unstructured_attributes_dict.keys():
        normalised_key = PROJEKT_ATTRIBUTES_MAP.get(key)
        if normalised_key in PERSONEN_REFERENCES:
            # this is to check if there are multiple gepris attribute for the same normalised attributes keys
            # should never happen
            if normalised_key in seen_personen_keys:
                raise ValueError(
                    f'Normalised Key "{normalised_key}" for gepris key "{key}" exists multiples times in projekt attributes {unstructured_attributes_dict}')
            else:
                seen_personen_keys.append(normalised_key)
            if _parse_for_gender(key) == MALE:
                male_personen.update(item[normalised_key])
            elif _parse_for_gender(key) == FEMALE:
                female_personen.update(item[normalised_key])
    item['male_personen'] = list(male_personen)
    item['female_personen'] = list(female_personen)
    return item
