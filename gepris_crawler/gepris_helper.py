import scrapy

BASE_URL = 'https://gepris.dfg.de/gepris'
OCTOPUS_URL = BASE_URL + '/OCTOPUS'
SEARCH_TASK = 'doSearchExtended'
DATA_MONITOR_TASK = 'showMonitor'
# different contexts to search for
CONTEXTS = ['projekt', 'person', 'institution']
LANGUAGES = ['de', 'en']
DATA_MONITOR_KEYS = {
    'Projekte mit Abschlussberichten': 'finished_project_count',
    'Projekte f�r die Abschlussberichtsdaten in GEPRIS vorliegen': 'finished_project_count',
    'Projekte für die Abschlussberichtsdaten in GEPRIS vorliegen': 'finished_project_count',
    'Projekt': 'project_count',
    'Projekte': 'project_count',
    'Person': 'person_count',
    'Personen': 'person_count',
    'Institution': 'institution_count',
    'Institutionen': 'institution_count',
    'Geistes- und Sozialwissenschaften': 'humanities_count',
    'Lebenswissenschaften': 'life_count',
    'Naturwissenschaften': 'natural_count',
    'Ingenieurwissenschaften': 'engineering_count',
    'Infrastrukturförderung': 'infrastructure_count',
    'Forschungsinfrastruktur': 'research_infrastructure_count'
}
GOOGLE_CACHE_BASE_URL = 'https://webcache.googleusercontent.com/search?q=cache:'


def check_valid_context(context):
    if context not in CONTEXTS:
        raise ValueError(f'Context must be one of {CONTEXTS}, but was "{context}"')


def search_list_params(context='project', results_per_site=1000, index=0):
    return {
        'context': context,
        'task': SEARCH_TASK,
        'hitsPerPage': str(results_per_site),
        'index': str(index)
    }


def google_cache_url(actual_url):
    return GOOGLE_CACHE_BASE_URL + actual_url


def data_monitor_request():
    return scrapy.FormRequest(
        OCTOPUS_URL,
        method='GET',
        formdata=dict(task=DATA_MONITOR_TASK),
        dont_filter=True,
        meta=dict(expected_language='de')
    )


def search_results_request(context, results_per_site, current_index, expected_items_on_page):
    # It is important to use dont_filter=True,
    # because the first request is redirected to itself, which makes scrapy filter this second request
    # see: https://stackoverflow.com/questions/59705305/scrapy-thinks-redirects-are-duplicate-requests
    return scrapy.FormRequest(
        OCTOPUS_URL,
        method='GET',
        formdata=search_list_params(context=context, results_per_site=results_per_site, index=current_index),
        dont_filter=True,
        cb_kwargs=dict(items_on_page=expected_items_on_page),
        meta=dict(expected_language='de')
    )


def details_request(url, language, refresh_cache=False, **kwargs):
    if language not in ['de', 'en']:
        raise ValueError(f'Language must be either "de" or "en", but was "{language}"')
    meta = dict(expected_language=language)
    if refresh_cache:
        meta = dict(meta, refresh_cache=True)
    return scrapy.FormRequest(url,
                              method='GET',
                              formdata=dict(language=language),
                              dont_filter=True,
                              meta=meta,
                              **kwargs)


def details_url(element_id, context):
    if context not in CONTEXTS:
        raise ValueError(f'Context must be one of {CONTEXTS}, but was "{context}"')
    return '/'.join([BASE_URL, context, str(element_id)])


def build_url(base, params={}):
    url = base
    if params:
        url += '?'
        url += '&'.join([f'{key}={value}' for key, value in params.items()])
    return url


def is_gepris_path(url_path, context_to_check=None):
    splits = url_path.split('/')
    if len(splits) == 4 and splits[1] == 'gepris':
        if context_to_check:
            return splits[2] == context_to_check
        return True
    return False
