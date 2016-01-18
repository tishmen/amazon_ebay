import logging

from import_export import resources
from import_export.admin import ImportMixin

from django.contrib import admin, messages
from django.db import models
from django.utils.safestring import mark_safe

from .forms import (
    ChangeReviewerForm, EbayItemInlineForm, EbayItemInlineFormSet, EbayItemForm
)
from .models import AmazonSearch, AmazonItem, EbayItem
from .tasks import search_task, list_task

logger = logging.getLogger(__name__)

BOOL_CHOICES = [(1, 'Yes'), (0, 'No')]


def get_message_bit(count, obj_name, obj_name_multiple=None):
    if count == 1:
        return '1 {}'.format(obj_name)
    if not obj_name_multiple:
        obj_name_multiple = obj_name + 's'
    return '{} {}'.format(count, obj_name_multiple)


class AmazonSearchResource(resources.ModelResource):

    class Meta:
        model = AmazonSearch
        exclude = ['date_searched']


class BoolFilter(admin.SimpleListFilter):

    def lookups(self, request, model_admin):
        return BOOL_CHOICES

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.exclude(**self.query)
        if self.value() == '1':
            return queryset.filter(**self.query)
        return queryset


class IsSearchedFilter(BoolFilter):

    title = 'is searched'
    parameter_name = 'is_searched'
    query = {'date_searched__isnull': False}


class IsReadyFilter(BoolFilter):

    title = 'is ready'
    parameter_name = 'is_ready'
    query = {'ebayitem__is_ready': True}


class IsListedFilter(BoolFilter):

    title = 'is listed'
    parameter_name = 'is_listed'
    query = {'ebayitem__is_listed': True}


class HasErrorFilter(BoolFilter):

    title = 'has error'
    parameter_name = 'has_error'
    query = {'ebayitem__error__isnull': False}


class AmazonItemInline(admin.TabularInline):

    model = AmazonItem
    readonly_fields = ['get_title', 'get_url', 'get_price']
    fieldsets = [[None, {'fields': readonly_fields}]]
    can_delete = False
    extra = 0
    max_num = 0


class EbayItemInline(admin.StackedInline):

    model = EbayItem
    formset = EbayItemInlineFormSet
    form = EbayItemInlineForm
    readonly_fields = ['get_error']
    can_delete = False
    extra = 0
    max_num = 1

    def get_fieldsets(self, request, obj):
        fields = [
            'title', 'price', 'html', 'category_search', 'category_id',
            'category_name', 'manufacturer', 'mpn', 'upc', 'is_ready',
            'note'
        ]
        fieldsets = [[None, {'fields': fields}]]
        item = obj.get_related_ebay_item()
        if item and item.error:
            fieldsets[0][1]['fields'] = ['get_error'] + \
                fieldsets[0][1]['fields']
        return fieldsets


@admin.register(AmazonSearch)
class AmazonSearchAdmin(ImportMixin, admin.ModelAdmin):

    resource_class = AmazonSearchResource
    search_fields = ['query']
    actions = ['search_action']
    list_filter = [IsSearchedFilter, 'date_searched']
    list_display = ['query', 'get_result_count', 'date_searched']

    def has_delete_permission(self, request, obj=None):
        pass

    def add_view(self, request, *args, **kwargs):
        self.fieldsets = [[None, {'fields': ['query']}]]
        self.readonly_fields = self.inlines = []
        return super(AmazonSearchAdmin, self).add_view(
            request, *args, **kwargs
        )

    def change_view(self, request, object_id, *args, **kwargs):
        self.readonly_fields = ['query', 'date_searched']
        self.fieldsets = [[None, {'fields': self.readonly_fields}]]
        if AmazonSearch.objects.get(id=object_id).amazonitem_set.count():
            self.inlines = [AmazonItemInline]
        return super(AmazonSearchAdmin, self).change_view(
            request, object_id, *args, **kwargs
        )

    def get_queryset(self, request):
        queryset = super(AmazonSearchAdmin, self).get_queryset(request)
        return queryset.annotate(models.Count('amazonitem'))

    def get_actions(self, request):
        actions = super(AmazonSearchAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_result_count(self, obj):
        return obj.amazonitem__count

    get_result_count.short_description = 'result count'
    get_result_count.admin_order_field = 'amazonitem__count'

    def search_action(self, request, queryset):
        search_task.delay(queryset)
        message = 'Searching for amazon {}'.format(
            get_message_bit(queryset.count(), 'search', 'searches')
        )
        logger.info(message)
        self.message_user(request, message, level=messages.SUCCESS)

    search_action.short_description = 'Search for selected amazon searches'


@admin.register(AmazonItem)
class AmazonItemAdmin(admin.ModelAdmin):

    search_fields = ['title', 'manufacturer', 'mpn']
    readonly_fields = [
        'get_url', 'title', 'get_image', 'get_price', 'review_count',
        'get_feature_list',
    ]
    fieldsets = [[None, {'fields': readonly_fields + ['reviewer']}]]
    inlines = [EbayItemInline]
    action_form = ChangeReviewerForm
    actions = ['list_action', 'change_reviewer_action']

    class Media:
        css = {'all': ['css/amazonitem_admin.css']}
        js = ['js/amazonitem_admin.js']

    def has_add_permission(self, request):
        pass

    def has_delete_permission(self, request, obj=None):
        pass

    def lookup_allowed(self, key, *args, **kwargs):
        if key in ['is_listed', 'reviewer', 'search__query', 'date_added']:
            return True
        return super(AmazonItemAdmin, self).lookup_allowed(
            key, *args, **kwargs
        )

    def get_list_display(self, request):
        list_display = [
            'title', 'get_url', 'get_price', 'get_is_ready',
            'get_has_error', 'get_is_listed', 'reviewer', 'date_added'
        ]
        if not request.user.is_superuser:
            list_display.remove('get_is_listed')
            list_display.remove('date_added')
            list_display.remove('reviewer')
        return list_display

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return [[None, {'fields': self.readonly_fields + ['reviewer']}]]
        return [[None, {'fields': self.readonly_fields}]]

    def get_list_filter(self, request):
        if request.user.is_superuser:
            return [
                IsReadyFilter, HasErrorFilter, IsListedFilter, 'reviewer',
                'search__query', 'date_added'
            ]
        return [IsReadyFilter, HasErrorFilter]

    def get_queryset(self, request):
        queryset = super(AmazonItemAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            return queryset.filter(reviewer=request.user)
        return queryset

    def get_actions(self, request):
        actions = super(AmazonItemAdmin, self).get_actions(request)
        if request.user.is_superuser and 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_form(self, request, obj=None, **kwargs):
        form = super(AmazonItemAdmin, self).get_form(request, obj, **kwargs)
        if request.user.is_superuser:
            form.base_fields['reviewer'].widget.can_add_related = False
            form.base_fields['reviewer'].widget.can_change_related = False
        return form

    def get_image(self, obj):
        return mark_safe(obj.get_image())

    get_image.short_description = 'image'

    def get_is_listed(self, obj):
        return bool(obj.get_related_ebay_item())

    get_is_listed.boolean = True
    get_is_listed.short_description = 'is listed'

    def get_is_ready(self, obj):
        try:
            return obj.get_related_ebay_item().is_ready
        except AttributeError:
            return False

    get_is_ready.boolean = True
    get_is_ready.short_description = 'is ready'

    def get_has_error(self, obj):
        try:
            return bool(obj.get_related_ebay_item().error)
        except AttributeError:
            return False

    get_has_error.boolean = True
    get_has_error.short_description = 'has error'

    def list_action(self, request, queryset):
        queryset = queryset.filter(ebayitem__is_listed=False)
        list_task.delay(queryset)
        message = 'Listing {}'.format(
            get_message_bit(queryset.count(), 'Amazon item') + ' on Ebay'
        )
        self.message_user(request, message, level=messages.SUCCESS)

    list_action.short_description = 'List selected amazon items on ebay'

    def change_reviewer_action(self, request, queryset):
        queryset.update(reviewer=request.POST.get('reviewer'))
        message = 'Changing reviewer for amazon {}'.format(
            get_message_bit(queryset.count(), 'item')
        )
        self.message_user(request, message, level=messages.SUCCESS)

    change_reviewer_action.short_description = 'Change reviewer for selected '\
        'amazon items'


@admin.register(EbayItem)
class EbayItemAdmin(admin.ModelAdmin):

    fields_ = [
        'get_url', 'title', 'get_image', 'get_price', 'category_name',
        'manufacturer', 'mpn', 'upc'
    ]

    list_display = [
        'title', 'get_ebay_url', 'get_amazon_url', 'get_price', 'date_listed'
    ]
    search_fields = ['title', 'manufacturer', 'mpn']
    fieldsets = [[None, {'fields': fields_}]]
    readonly_fields = fields_ + ['html']
    form = EbayItemForm

    def has_add_permission(self, request):
        pass

    def has_delete_permission(self, request, obj=None):
        pass

    def get_queryset(self, request):
        queryset = super(EbayItemAdmin, self).get_queryset(request)
        return queryset.filter(is_listed=True)

    def get_actions(self, request):
        actions = super(EbayItemAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_image(self, obj):
        return mark_safe(obj.get_image())

    get_image.short_description = 'image'
