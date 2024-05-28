import json
from typing import Any, Mapping
from django import forms
from django.core.files.base import File
from django.db.models import Model
from django.forms import ModelForm, RadioSelect, Select, ValidationError
from django.forms.utils import ErrorList
from django.utils.translation import gettext_lazy as _

from oauth_emailbackend.utils import get_provider_choices
from .models import EmailClient, OAuthAPI

class PrettyJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, indent, sort_keys, **kwargs):
        super().__init__(*args, indent=2, sort_keys=True, **kwargs)

class EmailClientAdminForm(ModelForm):
    class Meta:
        model = EmailClient
        widgets = {
            "send_method": RadioSelect,
            # "security_protocol": RadioSelect,
        }
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['access_token' ].disabled = True
        self.fields['access_token' ].widget.attrs['rows'] = 3
        self.fields['refresh_token'].disabled = True
        self.fields['refresh_token'].widget.attrs['rows'] = 3

    def clean_sender_name(self, ):
        sender_name =  self.cleaned_data['sender_name']
        if '@' in sender_name:
            raise ValidationError(_("@를 포함할 수 없습니다."))
        
        return sender_name




class OAuthAPIAdminForm(ModelForm):
    client_config = forms.JSONField(encoder=PrettyJSONEncoder)

    class Meta:
        model = OAuthAPI
        fields = '__all__'
        # widgets = {
        #     'provider': RadioSelect(choices = get_provider_choices())
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['client_config'].widget.attrs['style'] = 'width: 80%';
        self.fields['client_config'].widget.attrs['rows'] = 25;
        self.fields['provider'].widget = Select(choices = get_provider_choices())