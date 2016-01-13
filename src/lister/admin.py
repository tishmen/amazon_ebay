import inspect
import itertools
import copy
import logging

from djcelery.models import (
    TaskState, WorkerState, PeriodicTask, IntervalSchedule, CrontabSchedule
)
from import_export import resources
from import_export.admin import ImportMixin

from django.contrib import admin, messages
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.functional import curry
from .forms import ReviewerForm, ItemReviewForm, ItemReviewFormSet
from .models import AmazonSearch, AmazonItem, ItemReview, EbayItem
from .tasks import search_task

admin.site.unregister(TaskState)
admin.site.unregister(WorkerState)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(PeriodicTask)

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
    extra = 0
    max_num = 0
    can_delete = False
    fieldsets = [[None, {'fields': ['title_', 'url_', 'price_']}]]
    readonly_fields = ['title_', 'url_', 'price_']


@admin.register(AmazonSearch)
class AmazonSearchAdmin(ImportMixin, admin.ModelAdmin):

    resource_class = AmazonSearchResource
    search_fields = ['query']
    actions = ['search']
    list_filter = ['date_searched']
    list_display = ['query', 'result_count', 'date_searched']

    def add_view(self, request, form_url='', extra_context=None):
        self.fieldsets = [[None, {'fields': ['query']}]]
        self.readonly_fields = None
        self.inlines = None
        return super(AmazonSearchAdmin, self).add_view(
            request, form_url, extra_context
        )

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.fieldsets = [[None, {'fields': ['query', 'date_searched']}]]
        self.readonly_fields = ['query', 'date_searched']
        obj = AmazonSearch.objects.get(id=object_id)
        if obj.amazonitem_set.all():
            self.inlines = [AmazonItemInline]
        return super(AmazonSearchAdmin, self).change_view(
            request, object_id, form_url, extra_context
        )

    # http://stackoverflow.com/questions/5086537/how-to-omit-object-name-from-djangos-tabularinline-admin-view
    # omit object name in TabularInline
    def render_change_form(self, request, context, *args, **kwargs):
        def get_queryset(original_func):
            def wrapped_func():
                if inspect.stack()[1][3] == '__iter__':
                    return itertools.repeat(None)
                return original_func()
            return wrapped_func
        for formset in context['inline_admin_formsets']:
            formset.formset.get_queryset = get_queryset(
                formset.formset.get_queryset
            )
        return super(AmazonSearchAdmin, self).render_change_form(
            request, context, *args, **kwargs
        )

    def get_queryset(self, request):
        queryset = super(AmazonSearchAdmin, self).get_queryset(request)
        queryset = queryset.annotate(models.Count('amazonitem'))
        return queryset

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


class ItemReviewInline(admin.StackedInline):

    model = ItemReview
    formset = ItemReviewFormSet
    form = ItemReviewForm
    extra = 0
    max_num = 1

    def get_formset(self, request, obj=None, **kwargs):
        formset = super(ItemReviewInline, self).get_formset(
            request, obj, **kwargs
        )
        try:
            review = obj.itemreview_set.all()[0]
            initial = [
                {
                    'is_listed': obj.is_listed,
                    'title': review.title,
                    'html': review.html,
                    'category_search': review.category_search,
                    'category_id': review.category_id,
                    'category_name': review.category_name,
                    'manufacturer': review.manufacturer,
                    'mpn': review.mpn,
                    'upc': review.upc,
                    'note': review.note
                }
            ]
        except IndexError:
            initial = [
                {
                    'is_listed': obj.is_listed,
                    'title': obj.title,
                    'html': obj.html(),
                    'category_search': obj.search.query,
                    'manufacturer': obj.manufacturer,
                    'mpn': obj.mpn
                }
            ]
        formset.__init__ = curry(formset.__init__, initial=initial)
        return formset


@admin.register(AmazonItem)
class AmazonItemAdmin(admin.ModelAdmin):

    search_fields = ['title', 'manufacturer', 'mpn']
    readonly_fields = [
        'url_', 'title', 'image', 'price_', 'review_count', 'feature_list_',
        'is_listed'
    ]
    item_fields = [
        'url_', 'title', 'image', 'price_', 'review_count', 'feature_list_',
        'is_listed', 'reviewer'
    ]
    fieldsets = [[None, {'fields': item_fields}]]
    inlines = [ItemReviewInline]
    action_form = ReviewerForm
    actions = ['change_reviewer']

    class Media:
        css = {'all': ['css/amazonitem_admin.css']}
        js = ['js/amazonitem_admin.js']

    def has_add_permission(self, request):
        return

    def get_list_display(self, request):
        list_display = ['title', 'url_', 'price_']
        if not request.user.is_superuser:
            return list_display + ['is_listed', 'date_added']
        return list_display + ['reviewer', 'is_listed', 'date_added']

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
        return ['is_listed', 'reviewer', 'date_added']

    def get_queryset(self, request):
        queryset = super(AmazonItemAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            return queryset.filter(reviewer=request.user)
        return queryset

    def get_actions(self, request):
        actions = super(AmazonItemAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            return
        return actions

    def get_form(self, request, obj=None, **kwargs):
        form = super(AmazonItemAdmin, self).get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            return form
        form.base_fields['reviewer'].widget.can_add_related = False
        form.base_fields['reviewer'].widget.can_change_related = False
        return form

    def change_reviewer(self, request, queryset):
        queryset.update(reviewer=request.POST.get('reviewer'))
        message = 'Changing reviewer for {}'.format(
            get_message_bit(queryset.count(), 'amazon item')
        )
        self.message_user(request, message, level=messages.SUCCESS)

    def image(self, obj):
        return mark_safe(obj.image())

    change_reviewer.short_description = 'Change reviewer for selected amazon '\
        'items'


@admin.register(EbayItem)
class EbayItemAdmin(admin.ModelAdmin):

    pass
