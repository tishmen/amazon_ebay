from ckeditor.widgets import CKEditorWidget

from django import forms
from django.contrib.admin.helpers import ActionForm
from django.contrib.auth.models import User

from .models import ItemReview


class ReviewerForm(ActionForm):

    reviewer = forms.ModelChoiceField(
        required=False, queryset=User.objects.all()
    )


class ItemReviewForm(forms.ModelForm):

    title = forms.CharField(max_length=80, widget=forms.Textarea)
    html = forms.CharField(widget=CKEditorWidget())
    category_search = forms.CharField(widget=forms.TextInput)
    category_id = forms.IntegerField(label='Category', widget=forms.Select)
    category_name = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(ItemReviewForm, self).__init__(*args, **kwargs)
        self.fields['title'].help_text = '{} characters'.format(
            len(kwargs.get('initial', {}).get('title', ''))
        )
        category_id = kwargs.get('initial', {}).get('category_id')
        category_name = kwargs.get('initial', {}).get('category_name')
        if category_id and category_name:
            self.fields['category_id'] = forms.IntegerField(
                widget=forms.Select(choices=[(category_id, category_name)])
            )
        if kwargs.get('initial', {}).get('is_listed'):
            for _, field in self.fields.items():
                    field.widget.attrs['readonly'] = "readonly"

    class Meta:
        model = ItemReview
        fields = [
            'title', 'html', 'category_search', 'category_id', 'category_name',
            'manufacturer', 'mpn', 'upc', 'note'
        ]


class BaseItemReviewFormSet(forms.BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        self.__initial = kwargs.pop('initial', [])
        super(BaseItemReviewFormSet, self).__init__(*args, **kwargs)

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


ItemReviewFormSet = forms.formset_factory(
    ItemReviewForm, formset=BaseItemReviewFormSet
)
