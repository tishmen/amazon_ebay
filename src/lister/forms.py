from django import forms
from django.contrib.admin.helpers import ActionForm
from django.contrib.auth.models import User


class UpdateReviewerActionForm(ActionForm):

    reviewer = forms.ModelChoiceField(
        queryset=User.objects.all(), required=False
    )
