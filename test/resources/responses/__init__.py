import os

from scrapy.http import Request, TextResponse

from gepris_crawler import gepris_helper


def fake_response_from_file(file_name, request=None):
    """
    Create a Scrapy fake HTTP response from a HTML file
    @param file_name: The relative filename from the responses directory,
                      but absolute paths are also accepted.
    @param request: Use this request for the response, if None, create one from the file
    returns: A scrapy HTTP response which can be used for unittesting.
    """

    if not file_name[0] == '/':
        responses_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(responses_dir, file_name)
    else:
        file_path = file_name

    if request is None:
        request = generate_request(file_path)

    with open(file_path, 'r') as f:
        file_content = f.read()

    response = TextResponse(url=request.url,
                            request=request,
                            body=file_content,
                            encoding='utf-8')
    return response


def generate_request(file_path):
    spider_name, file_name = file_path.split('/')[-2:]
    if spider_name == 'data_monitor':
        return Request(url=gepris_helper.data_monitor_url())
    elif spider_name == 'search_results':
        file_name_without_type = file_name.split('.')[0]
        context, index, items_per_page, date = file_name_without_type.split('_')
        return gepris_helper.search_results_request(context, items_per_page, index, items_per_page)
    elif spider_name == 'details':
        file_name_without_type = file_name.split('.')[0]
        splitted = file_name_without_type.split('_')
        context, element_id, language = splitted[:3]
        url = gepris_helper.details_url(element_id, context)
        if context == 'projekt' and splitted[3] == 'finished':
            url += '/ergebnisse'
        return gepris_helper.details_request(url, language)
