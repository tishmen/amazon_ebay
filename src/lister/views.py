from django.http import HttpResponse
from .utils import Ebay


def category_search_view(request, query=None):
    if not (request.is_ajax() and query):
        return HttpResponse('')
    ebay = Ebay()
    if not ebay.production_connection:
        return []
    options = ''
    for value, text in ebay.category_search(query):
        options += '<option value="{}">{}</option>\n'.format(value, text)
    return HttpResponse(options.strip())
