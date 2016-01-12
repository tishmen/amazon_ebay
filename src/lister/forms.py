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

    class Media:
        js = ['js/category_search_widget.js']

    def render(self, name, value, attrs=None):
        context = {'category_search': self.category_search}
        return mark_safe(
            render_to_string(self.template_name, context)
        )


class ItemReviewInlineForm(forms.ModelForm):

    html = forms.CharField(widget=CKEditorWidget())
    category_search = forms.CharField(widget=CategorySearchWidget)
    category_id = forms.ChoiceField(label='Category')
    category_name = forms.CharField()

    class Meta:
        model = ItemReview
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ItemReviewInlineForm, self).__init__(*args, **kwargs)
        if kwargs.get('initial', {}).get('readonly'):
            self.fields['category_search'].widget = forms.HiddenInput()
            self.fields['category_id'].widget = forms.HiddenInput()
            for _, value in self.fields.items():
                value.widget.attrs['readonly'] = True
        else:
            self.fields['category_name'].widget = forms.HiddenInput()
            self.fields['category_search'].widget.category_search = (
                kwargs.get('initial', {}).get('category_search', '')
            )
            self.fields['category_id'].choices = [
                (
                    kwargs.get('initial', {}).get('category_id', ''),
                    kwargs.get('initial', {}).get('category_name', '')
                )
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
