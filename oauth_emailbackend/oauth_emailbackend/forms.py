from typing import Any, Mapping
from django.core.files.base import File
from django.db.models import Model
from django.forms import ModelForm, RadioSelect, Select
from django.forms.utils import ErrorList

from oauth_emailbackend.utils import get_provider_choices
from .models import EmailClient, OAuthAPI


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

        self.fields['api_token'].disabled = True
        self.fields['api_token'].widget.attrs['rows'] = 3


class OAuthAPIAdminForm(ModelForm):
    class Meta:
        model = OAuthAPI
        fields = '__all__'

        # widgets = {
        #     'provider': RadioSelect(choices = get_provider_choices())
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['client_id'].widget.attrs['style'] = 'width: 80%';
        self.fields['client_secret'].widget.attrs['style'] = 'width: 80%';
        self.fields['provider'].widget = Select(choices = get_provider_choices())