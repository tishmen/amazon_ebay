from django import forms
from django.contrib.admin.helpers import ActionForm
from django.contrib.auth.models import User

from .models import ItemReview


class ChangeReviewerActionForm(ActionForm):

    reviewer = forms.ModelChoiceField(
        queryset=User.objects.all(), required=False
    )


class ItemReviewInlineForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].help_text = '{} characters'.format(
            len(kwargs.get('initial', {}).get('title', ''))
        )

    class Meta:
        model = ItemReview
        fields = '__all__'


class BaseItemReviewInlineFormSet(forms.BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        self.__initial = kwargs.pop('initial', [])
        super().__init__(*args, **kwargs)

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
