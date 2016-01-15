import copy
import logging

from import_export import resources
from import_export.admin import ImportMixin

from django.contrib import admin, messages
from django.db import models
from django.utils.safestring import mark_safe

from .forms import (
    ReviewerForm, EbayItemInlineForm, EbayItemInlineFormSet, EbayItemForm
)
from .models import AmazonSearch, AmazonItem, EbayItem
from .tasks import search_task, list_task

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


class IsListedFilter(admin.SimpleListFilter):

    title = 'is listed'
    parameter_name = 'is_listed'

    def lookups(self, request, model_admin):
        return [('1', 'Yes'), ('0', 'No')]

    def queryset(self, request, queryset):
        lookup_value = self.value()
        if lookup_value:
            if lookup_value == '1':
                queryset = queryset.filter(ebayitem__is_listed=True)
            elif lookup_value == '0':
                queryset = queryset.filter(ebayitem__is_listed=None)
        return queryset


class HasErrorFilter(admin.SimpleListFilter):

    title = 'has error'
    parameter_name = 'has_error'

    def lookups(self, request, model_admin):
        return [('1', 'Yes'), ('0', 'No')]

    def queryset(self, request, queryset):
        lookup_value = self.value()
        if lookup_value:
            if lookup_value == '1':
                queryset = queryset.filter(ebayitem__error__isnull=0)
            elif lookup_value == '0':
                queryset = queryset.filter(ebayitem__error=None)
        return queryset


class AmazonItemInline(admin.TabularInline):

    model = AmazonItem
    readonly_fields = ['', 'title_', 'url_', 'price_']
    fieldsets = [[None, {'fields': readonly_fields}]]
    can_delete = False
    extra = 0
    max_num = 0


class EbayItemInline(admin.StackedInline):

    model = EbayItem
    formset = EbayItemInlineFormSet
    form = EbayItemInlineForm
    readonly_fields = ['error_']
    can_delete = False
    extra = 0
    max_num = 1

    def get_fieldsets(self, request, obj):
        fieldsets = [
            [
                None,
                {
                    'fields': [
                        'title', 'price', 'html', 'category_search',
                        'category_id', 'category_name', 'manufacturer', 'mpn',
                        'upc', 'note'
                    ]
                }
            ]
        ]
        item = obj.ebayitem_set.first()
        if item and item.error:
            fieldsets[0][1]['fields'] = (
                ['error_'] + fieldsets[0][1]['fields']
            )
        return fieldsets


@admin.register(AmazonSearch)
class AmazonSearchAdmin(ImportMixin, admin.ModelAdmin):

    resource_class = AmazonSearchResource
    search_fields = ['query']
    actions = ['search']
    list_filter = ['date_searched']
    list_display = ['query', 'result_count', 'date_searched']

    def has_delete_permission(self, request, obj=None):
        return

    def add_view(self, request, form_url='', extra_context=None):
        self.fieldsets = [[None, {'fields': ['query']}]]
        self.readonly_fields = []
        self.inlines = []
        return super(AmazonSearchAdmin, self).add_view(
            request, form_url, extra_context
        )

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.readonly_fields = ['query', 'date_searched']
        self.fieldsets = [[None, {'fields': self.readonly_fields}]]
        if AmazonSearch.objects.get(id=object_id).amazonitem_set.all():
            self.inlines = [AmazonItemInline]
        return super(AmazonSearchAdmin, self).change_view(
            request, object_id, form_url, extra_context
        )

    def get_queryset(self, request):
        queryset = super(AmazonSearchAdmin, self).get_queryset(request)
        queryset = queryset.annotate(models.Count('amazonitem'))
        return queryset

    def get_actions(self, request):
        actions = super(AmazonSearchAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def result_count(self, obj):
        return obj.amazonitem__count

    def search(self, request, queryset):
        search_task.delay(queryset)
        message = 'Searching for {}'.format(
            get_message_bit(
                queryset.count(), 'amazon search', 'amazon searches'
            )
        )
        logger.info(message)
        self.message_user(request, message, level=messages.SUCCESS)

    result_count.admin_order_field = 'amazonitem__count'
    search.short_description = 'Search for selected amazon searches'


@admin.register(AmazonItem)
class AmazonItemAdmin(admin.ModelAdmin):

    search_fields = ['title', 'manufacturer', 'mpn']
    readonly_fields = [
        'url_', 'title', 'image', 'price_', 'review_count', 'feature_list_',
    ]
    fieldsets = [[None, {'fields': readonly_fields + ['reviewer']}]]
    inlines = [EbayItemInline]
    action_form = ReviewerForm
    actions = ['list', 'change_reviewer']

    class Media:
        css = {'all': ['css/amazonitem_admin.css']}
        js = ['js/amazonitem_admin.js']

    def has_add_permission(self, request):
        return

    def has_delete_permission(self, request, obj=None):
        return

    def lookup_allowed(self, key, *args, **kwargs):
        if key in ['is_listed', 'reviewer', 'search__query', 'date_added']:
            return True
        return super(AmazonItemAdmin, self).lookup_allowed(
            key, *args, **kwargs
        )

    def get_list_display(self, request):
        list_display = ['title', 'url_', 'price_']
        if not request.user.is_superuser:
            return list_display + ['is_listed_', 'date_added']
        return list_display + ['reviewer', 'is_listed_', 'date_added']

    def get_fieldsets(self, request, obj=None):
        fieldsets = copy.deepcopy(
            super(AmazonItemAdmin, self).get_fieldsets(request)
        )
        if not request.user.is_superuser:
            fieldsets[0][1]['fields'].remove('reviewer')
        return fieldsets

    def get_list_filter(self, request):
        if not request.user.is_superuser:
            return
        return [
            HasErrorFilter, IsListedFilter, 'reviewer', 'search__query',
            'date_added'
        ]

    def get_queryset(self, request):
        queryset = super(AmazonItemAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            return queryset.filter(reviewer=request.user)
        return queryset

    def get_actions(self, request):
        actions = super(AmazonItemAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            return
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_form(self, request, obj=None, **kwargs):
        form = super(AmazonItemAdmin, self).get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            return form
        form.base_fields['reviewer'].widget.can_add_related = False
        form.base_fields['reviewer'].widget.can_change_related = False
        return form

    def image(self, obj):
        return mark_safe(obj.image())

    def is_listed_(self, obj):
        return bool(obj.ebayitem_set.filter(is_listed=True))

    def list(self, request, queryset):
        queryset = queryset.filter(ebayitem__is_listed=False)
        list_task.delay(queryset)
        message = 'Listing {}'.format(
            get_message_bit(queryset.count(), 'Amazon item') + ' on Ebay'
        )
        self.message_user(request, message, level=messages.SUCCESS)

    def change_reviewer(self, request, queryset):
        queryset.update(reviewer=request.POST.get('reviewer'))
        message = 'Changing reviewer for {}'.format(
            get_message_bit(queryset.count(), 'amazon item')
        )
        self.message_user(request, message, level=messages.SUCCESS)

    is_listed_.boolean = True
    list.short_description = 'List selected amazon items on ebay'
    change_reviewer.short_description = 'Change reviewer for selected amazon '\
        'items'


@admin.register(EbayItem)
class EbayItemAdmin(admin.ModelAdmin):

    form = EbayItemForm
    search_fields = ['title', 'manufacturer', 'mpn']
    list_display = ['title', 'ebay_url', 'amazon_url', 'price_', 'date_listed']
    readonly_fields = [
        'url_', 'title', 'image', 'price_', 'category_name', 'manufacturer',
        'mpn', 'upc', 'html'
    ]
    fieldsets = [
        [
            None,
            {'fields': readonly_fields[:3] + ['html'] + readonly_fields[4:-1]}
        ]
    ]

    def has_add_permission(self, request):
        return

    def has_delete_permission(self, request, obj=None):
        return

    def get_queryset(self, request):
        queryset = super(EbayItemAdmin, self).get_queryset(request)
        return queryset.filter(is_listed=True)

    def get_actions(self, request):
        actions = super(EbayItemAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def image(self, obj):
        return mark_safe(obj.image())
