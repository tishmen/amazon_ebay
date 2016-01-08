import logging

from import_export import resources
from import_export.admin import ImportMixin

from django.contrib import admin, messages

from .models import AmazonSearch, AmazonItem
from .tasks import search_task

logger = logging.getLogger(__name__)


def get_message_bit(count, obj_name, obj_name_multiple=None):
    if count == 1:
        return '1 {}'.format(obj_name)
    else:
        if not obj_name_multiple:
            obj_name_multiple = obj_name + 's'
        return '{} {}'.format(count, obj_name_multiple)


class AmazonSearchResource(resources.ModelResource):

    class Meta:

        model = AmazonSearch
        exclude = ['date_searched']


@admin.register(AmazonSearch)
class AmazonSearchAdmin(ImportMixin, admin.ModelAdmin):

    resource_class = AmazonSearchResource
    list_display = ['query', 'date_searched']
    list_filter = ['date_searched']
    search_fields = ['query']
    actions = ['search']

    def search(self, request, queryset):
        count = queryset.count()
        search_task.delay(queryset)
        message = 'Running search task for {}'.format(
            get_message_bit(count, 'query', 'queries')
        )
        logger.info(message)
        self.message_user(request, message, level=messages.SUCCESS)

    search.short_description = 'Run search task for selected queries'


@admin.register(AmazonItem)
class AmazonItemAdmin(admin.ModelAdmin):

    list_display = ['title', 'url_', 'price', 'date_added']
    list_filter = ['date_added']
    search_fields = ['title', 'manufacturer', 'mpn']
