from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView

from oauth_emailbackend.models import EmailClient
from oauth_emailbackend.utils import get_provider_instance

class OAuthCallbackView(TemplateView):
    template_name = 'oauth_emailbackend/callback.html'

    def get(self, request, **kwargs):
        provider = get_provider_instance(kwargs['provider'])
        provider.complete_callback(request.GET.copy())
        


        return super().get(request, **kwargs)
