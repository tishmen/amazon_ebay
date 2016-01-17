from ckeditor.widgets import CKEditorWidget

from django import forms
from django.contrib.admin.helpers import ActionForm
from django.contrib.auth.models import User

from .models import EbayItem


class ChangeReviewerForm(ActionForm):

    reviewer = forms.ModelChoiceField(
        required=False, queryset=User.objects.all()
    )


class EbayItemForm(forms.ModelForm):

    html = forms.CharField(
        widget=CKEditorWidget(attrs={'readonly': 'readonly'})
    )

    class Meta:
        model = EbayItem
        fields = '__all__'


class EbayItemInlineForm(forms.ModelForm):

    title = forms.CharField(max_length=80, widget=forms.Textarea)
    html = forms.CharField(widget=CKEditorWidget())
    category_search = forms.CharField(widget=forms.TextInput)
    category_id = forms.IntegerField(label='Category', widget=forms.Select)
    category_name = forms.CharField(widget=forms.HiddenInput)

    def set_title_help_text(self, *args, **kwargs):
        title = kwargs.get('initial', {}).get('title')
        if title:
            self.fields['title'].help_text = '{} characters'.format(len(title))

    def set_category(self, *args, **kwargs):
        category_id = kwargs.get('initial', {}).get('category_id')
        category_name = kwargs.get('initial', {}).get('category_name')
        if category_id and category_name:
            self.fields['category_id'] = forms.IntegerField(
                label='Category',
                widget=forms.Select(choices=[(category_id, category_name)])
            )

    def set_readonly(self, *args, **kwargs):
        if kwargs.get('initial', {}).get('readonly'):
            for _, field in self.fields.items():
                field.widget.attrs['readonly'] = 'readonly'

    def __init__(self, *args, **kwargs):
        super(EbayItemInlineForm, self).__init__(*args, **kwargs)
        self.set_title_help_text(*args, **kwargs)
        self.set_category(*args, **kwargs)
        self.set_readonly(*args, **kwargs)

    class Meta:
        model = EbayItem
        fields = '__all__'


class EbayItemInlineFormSet(forms.BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        super(EbayItemInlineFormSet, self).__init__(*args, **kwargs)
        try:
            ebay_item = kwargs['instance'].ebayitem_set.all()[0]
            self.initial = [
                {
                    'readonly': ebay_item.is_listed,
                    'title': ebay_item.title,
                    'category_id': ebay_item.category_id,
                    'category_name': ebay_item.category_name,
                }
            ]
        except IndexError:
            amazon_item = kwargs['instance']
            self.initial = [
                {
                    'title': amazon_item.title,
                    'price': amazon_item.price_after_markup(),
                    'html': amazon_item.html(),
                    'category_search': amazon_item.search.query,
                    'manufacturer': amazon_item.manufacturer,
                    'mpn': amazon_item.mpn
                }
            ]
        self.extra += len(self.initial)
