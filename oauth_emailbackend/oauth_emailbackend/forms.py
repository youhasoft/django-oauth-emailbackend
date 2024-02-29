from typing import Any, Mapping
from django.core.files.base import File
from django.db.models import Model
from django.forms import ModelForm, RadioSelect
from django.forms.utils import ErrorList

from .models import EmailHost, Provider


class EmailHostAdminForm(ModelForm):
    class Meta:
        model = EmailHost
        widgets = {
            "send_method": RadioSelect,
            "security_protocol": RadioSelect,
        }
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['api_token'].widget.attrs['rows'] = 3


class ProviderAdminForm(ModelForm):
    class Meta:
        model = Provider
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['client_id'].widget.attrs['style'] = 'width: 80%';
        self.fields['client_secret'].widget.attrs['style'] = 'width: 80%';