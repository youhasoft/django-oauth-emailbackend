import json
from typing import Any, Mapping
from django import forms
from django.core.files.base import File
from django.db.models import Model
from django.forms import ModelForm, RadioSelect, Select
from django.forms.renderers import BaseRenderer
from django.forms.utils import ErrorList


class SendEmailForm(forms.Form):
    from_address = forms.fields.CharField()
    to_address = forms.fields.CharField()
    subject = forms.fields.CharField()
    body = forms.fields.CharField(widget=forms.widgets.Textarea)

    def __init__(self, request, **kwargs) -> None:
        self.request = request
        super().__init__(**kwargs)