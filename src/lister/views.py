from django.http import HttpResponse

from .utils import Ebay


def category_search_view(request, query=None):
    ebay = Ebay()
    if not (query and ebay.production_connection):
        return
    options = ''
    for category_id, category_name in ebay.category_search(query):
        options += '<option value="{}">{}</option>\n'.format(
            category_id, category_name
        )
    return HttpResponse(options.strip())
