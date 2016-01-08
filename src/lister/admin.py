import logging

from import_export import resources
from import_export.admin import ImportMixin

from django.contrib import admin, messages
from django.db import models

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


class AmazonItemInline(admin.TabularInline):

    model = AmazonItem
    exclude = [
        'url', 'feature_list', 'image_list', 'manufacturer', 'mpn',
        'review_count'
    ]
    readonly_fields = ['title', 'url_', 'price', 'date_added']
    extra = 0
    max_num = 0
    can_delete = False


@admin.register(AmazonSearch)
class AmazonSearchAdmin(ImportMixin, admin.ModelAdmin):

    resource_class = AmazonSearchResource
    list_display = ['query', 'date_searched', 'result_count']
    list_filter = ['date_searched']
    search_fields = ['query']
    readonly_fields = ['query', 'date_searched']
    actions = ['search']
    inlines = [AmazonItemInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(models.Count('amazonitem'))
        return qs

    def result_count(self, obj):
        return obj.amazonitem__count

    def search(self, request, queryset):
        count = queryset.count()
        search_task.delay(queryset)
        message = 'Running search task for {}'.format(
            get_message_bit(count, 'query', 'queries')
        )
        logger.info(message)
        self.message_user(request, message, level=messages.SUCCESS)

    result_count.admin_order_field = 'amazonitem__count'
    search.short_description = 'Run search task for selected queries'


@admin.register(AmazonItem)
class AmazonItemAdmin(admin.ModelAdmin):

    list_display = ['title', 'url_', 'price', 'date_added']
    list_filter = ['date_added']
    search_fields = ['title', 'manufacturer', 'mpn']
    exclude = ['url', 'feature_list', 'image_list']
    readonly_fields = [
        'search', 'url_', 'title', 'feature_list_', 'image_list_', 'price',
        'manufacturer', 'mpn', 'review_count', 'date_added'
    ]
