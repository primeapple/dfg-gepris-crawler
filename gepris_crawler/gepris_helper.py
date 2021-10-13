import scrapy

BASE_URL = 'https://gepris.dfg.de/gepris'
SEARCH_URL = BASE_URL + '/OCTOPUS'
SEARCH_TASK = 'doSearchExtended'
DATA_MONITOR_TASK = 'showMonitor'
# different contexts to search for
CONTEXTS = ['projekt', 'person', 'institution']
LANGUAGES = ['de', 'en']
DATA_MONITOR_KEYS = {
    'Projekte mit Abschlussberichten': 'finished_project_count',
    'Projekt': 'project_count',
    'Person': 'person_count',
    'Institution': 'institution_count',
    'Geistes- und Sozialwissenschaften': 'humanities_count',
    'Lebenswissenschaften': 'life_count',
    'Naturwissenschaften': 'natural_count',
    'Ingenieurwissenschaften': 'engineering_count',
    'Infrastrukturförderung': 'infrastructure_count'
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


def data_monitor_url():
    return build_url(SEARCH_URL, params={'task': DATA_MONITOR_TASK})


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
