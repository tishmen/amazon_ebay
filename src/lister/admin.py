import copy
import logging

from import_export import resources
from import_export.admin import ImportMixin

from django.contrib import admin, messages
from django.db import models
from django.utils.safestring import mark_safe

from .models import AmazonSearch, AmazonItem, ItemReview
from .tasks import search_task
from .forms import ChangeReviewerActionForm, ItemReviewForm

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
        'reviewer', 'url', 'feature_list', 'image_list', 'manufacturer', 'mpn',
        'review_count', 'date_added', 'price'
    ]
    readonly_fields = ['title', 'url_', 'price_']
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
    inlines = [AmazonItemInline]
    actions = ['search']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(models.Count('amazonitem'))
        return queryset

    def search(self, request, queryset):
        count = queryset.count()
        search_task.delay(queryset)
        message = 'Delayed search task for {}'.format(
            get_message_bit(count, 'query', 'queries')
        )
        logger.info(message)
        self.message_user(request, message, level=messages.SUCCESS)

    def result_count(self, obj):
        return obj.amazonitem__count

    result_count.admin_order_field = 'amazonitem__count'
    search.short_description = 'Delay search task for selected queries'


class ItemReviewInline(admin.StackedInline):

    model = ItemReview
    form = ItemReviewForm
    extra = 0
    max_num = 1


@admin.register(AmazonItem)
class AmazonItemAdmin(admin.ModelAdmin):

    search_fields = ['title', 'manufacturer', 'mpn']
    readonly_fields = [
        'search', 'url_', 'image', 'title', 'feature_list_', 'image_list_',
        'price_', 'manufacturer', 'mpn', 'review_count', 'date_added'
    ]
    inlines = [ItemReviewInline]
    action_form = ChangeReviewerActionForm
    actions = ['change_reviewer']
    fields_ = [
        'url_', 'title', 'image', 'price_', 'review_count',
        ('feature_list_', 'image_list_'), ('manufacturer', 'mpn'), 'reviewer'
    ]
    fieldsets = [[None, {'fields': fields_}]]

    def get_list_display(self, request):
        list_display = ['title', 'url_', 'price_']
        if not request.user.is_superuser:
            return list_display
        return list_display + ['reviewer', 'date_added']

    def get_fieldsets(self, request, obj=None):
        fieldsets = copy.deepcopy(super().get_fieldsets(request))
        if not request.user.is_superuser:
            fieldsets[0][1]['fields'].remove('reviewer')
        return fieldsets

    def get_list_filter(self, request):
        if not request.user.is_superuser:
            return
        return ['reviewer', 'date_added']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            return queryset.filter(reviewer=request.user)
        return queryset

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            return
        return actions

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            return form
        reviewer = form.base_fields['reviewer']
        reviewer.widget.can_add_related = False
        reviewer.widget.can_change_related = False
        return form

    def change_reviewer(self, request, queryset):
        count = queryset.count()
        reviewer = request.POST['reviewer']
        queryset.update(reviewer=reviewer)
        message = 'Changing reviewer for {}'.format(
            get_message_bit(count, 'amazon item')
        )
        self.message_user(request, message, level=messages.SUCCESS)

    def image(self, obj):
        return mark_safe(obj.image())

    change_reviewer.short_description = 'Change reviewer for selected amazon '\
        'items'
