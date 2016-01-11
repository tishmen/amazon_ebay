from ckeditor.widgets import CKEditorWidget

from django import forms
from django.contrib.admin.helpers import ActionForm
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from .models import ItemReview


class ChangeReviewerActionForm(ActionForm):

    reviewer = forms.ModelChoiceField(
        queryset=User.objects.all(), required=False
    )


class CategorySearchWidget(forms.Widget):

    template_name = 'category_search_widget.html'

    def render(self, name, value, attrs=None):
        return mark_safe(
            render_to_string(self.template_name, {'options': None})
        )


class ItemReviewInlineForm(forms.ModelForm):

    html = forms.CharField(widget=CKEditorWidget())
    category = forms.CharField(widget=CategorySearchWidget)

    def __init__(self, *args, **kwargs):
        super(ItemReviewInlineForm, self).__init__(*args, **kwargs)
        self.fields['title'].help_text = '{} characters'.format(
            len(kwargs.get('initial', {}).get('title', ''))
        )

    class Meta:
        model = ItemReview
        fields = [
            'title', 'html', 'category', 'manufacturer', 'mpn', 'upc', 'note'
        ]


class BaseItemReviewInlineFormSet(forms.BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        self.__initial = kwargs.pop('initial', [])
        super(BaseItemReviewInlineFormSet, self).__init__(*args, **kwargs)

    def total_form_count(self):
        return len(self.__initial) + self.extra

    def _construct_forms(self):
        return forms.BaseFormSet._construct_forms(self)

    def _construct_form(self, i, **kwargs):
        if self.__initial:
            try:
                kwargs['initial'] = self.__initial[i]
            except IndexError:
                pass
        return forms.BaseFormSet._construct_form(self, i, **kwargs)


ItemReviewInlineFormSet = forms.formset_factory(
    ItemReviewInlineForm, formset=BaseItemReviewInlineFormSet
)
