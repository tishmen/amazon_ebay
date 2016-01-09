from django import forms
from django.contrib.admin.helpers import ActionForm
from django.contrib.auth.models import User

from .models import ItemReview


class CreateReviewActionForm(ActionForm):

    reviewer = forms.ModelChoiceField(
        queryset=User.objects.all(), required=False
    )


class ItemReviewAdmin(forms.ModelForm):

    class Meta:

        model = ItemReview
        fields = '__all__'
