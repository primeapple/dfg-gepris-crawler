import pickle
import dbm
from time import localtime
from scrapy.utils.request import request_fingerprint
from gepris_crawler.gepris_helper import details_url, details_request


def detail_request(element_id, context, language):
    return details_request(details_url(element_id, context), language)


def get_time_and_data(request, db):
    key = request_fingerprint(request)
    tkey = f'{key}_time'
    if tkey not in db:
        return  # not found
    tstr = db[tkey]
    return localtime(float(tstr)), pickle.loads(db[f'{key}_data'])


def delete_detail_cache(element_id, context, db):
    for language in ['de', 'en']:
        request = detail_request(element_id, context, language)
        request_key = request_fingerprint(request)
        for key in [f'{request_key}_time', f'{request_key}_data']:
            if key in db:
                print(f'Key (either time or data) for {element_id}, lang "{language}" exists, deleting it')
                del db[key]


def get_db(name='details', only_reading=True):
    if only_reading:
        flag = 'r'
    else:
        flag = 'w'
    return dbm.open(f'.scrapy/httpcache/{name}.db', flag=flag)


def write_body(data, filename='index.html'):
    with open(filename, 'w+b') as f:
        f.write(data['body'])
