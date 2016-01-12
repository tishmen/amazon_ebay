from ckeditor.widgets import CKEditorWidget

from django import forms
from django.contrib.admin.helpers import ActionForm
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from .models import AmazonItem


class ChangeReviewerActionForm(ActionForm):

    reviewer = forms.ModelChoiceField(
        queryset=User.objects.all(), required=False
    )


class CategorySearchWidget(forms.Widget):

    template_name = 'category_search_widget.html'

    def render(self, name, value, attrs=None):
        context = {'initial': self.initial}
        return mark_safe(render_to_string(self.template_name, context))


class AmazonItemForm(forms.ModelForm):

    new_title = forms.CharField(label='Title', max_length=80)
    html = forms.CharField(widget=CKEditorWidget())
    category_search = forms.CharField(widget=CategorySearchWidget)
    category_name = forms.CharField(widget=forms.HiddenInput)
    category_id = forms.ChoiceField(label='Category')
    new_manufacturer = forms.CharField(label='Manufacturer', max_length=65)
    new_mpn = forms.CharField(label='Mpn', max_length=65)
    upc = forms.CharField(required=False, max_length=12)
    note = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:

        model = AmazonItem
        fields = [
            'title', 'review_count', 'is_listed', 'reviewer', 'new_title',
            'html', 'category_search', 'category_name', 'category_id',
            'new_manufacturer', 'new_mpn', 'upc', 'note'
        ]
