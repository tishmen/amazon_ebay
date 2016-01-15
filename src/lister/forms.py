from ckeditor.widgets import CKEditorWidget

from django import forms
from django.contrib.admin.helpers import ActionForm
from django.contrib.auth.models import User

from .models import EbayItem


class ReviewerForm(ActionForm):

    reviewer = forms.ModelChoiceField(
        required=False, queryset=User.objects.all()
    )


class EbayItemForm(forms.ModelForm):

    html = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = EbayItem
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(EbayItemForm, self).__init__(*args, **kwargs)
        self.fields['html'].widget.attrs['readonly'] = "readonly"


class EbayItemInlineForm(forms.ModelForm):

    title = forms.CharField(max_length=80, widget=forms.Textarea)
    html = forms.CharField(widget=CKEditorWidget())
    category_search = forms.CharField(widget=forms.TextInput)
    category_id = forms.IntegerField(label='Category', widget=forms.Select)
    category_name = forms.CharField(widget=forms.HiddenInput)

    def set_readonly(self, *args, **kwargs):
        for _, field in self.fields.items():
            field.widget.attrs['readonly'] = 'readonly'

    def __init__(self, *args, **kwargs):
        super(EbayItemInlineForm, self).__init__(*args, **kwargs)
        if kwargs.get('initial', {}).get('readonly'):
            for _, field in self.fields.items():
                field.widget.attrs['readonly'] = 'readonly'
        title = kwargs.get('initial', {}).get('title')
        if title:
            self.fields['title'].help_text = '{} characters'.format(len(title))

    class Meta:
        model = EbayItem
        fields = '__all__'


class EbayItemInlineFormSet(forms.BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        super(EbayItemInlineFormSet, self).__init__(*args, **kwargs)
        try:
            item = kwargs['instance'].ebayitem_set.all()[0]
            self.initial = [{'readonly': item.is_listed}]
        except IndexError:
            self.initial = [
                {
                    'title': kwargs['instance'].title,
                    'price': kwargs['instance'].price_after_markup(),
                    'html': kwargs['instance'].html(),
                    'category_search': kwargs['instance'].search.query,
                    'manufacturer': kwargs['instance'].manufacturer,
                    'mpn': kwargs['instance'].mpn
                }
            ]
        self.extra += len(self.initial)
