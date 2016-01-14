from django.http import HttpResponse

from .utils import Ebay


def category_search_view(request, query=None):
    ebay = Ebay()
    if not (request.is_ajax() and query and ebay.production_connection):
        return HttpResponse()
    options = ''
    for category_id, category_name in ebay.category_search(query):
        options += u'<option value="{}">{}</option>\n'.format(
            category_id, category_name
        )
    return HttpResponse(options.strip())
