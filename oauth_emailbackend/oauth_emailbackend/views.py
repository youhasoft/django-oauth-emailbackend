from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, TemplateView

from oauth_emailbackend.models import EmailClient
from oauth_emailbackend.utils import get_provider_instance

class OAuthCallbackView(TemplateView):
    # template_name = 'oauth_emailbackend/callback.html'

    def get(self, request, **kwargs):
        provider = get_provider_instance(provider_name=kwargs['provider_name'])

        # 프로바이더 레벌에서 인증과정을 완료한 다음 email_client_id, totken을 반환 / 저장 
        email_client_id, access_token, atrribs = provider.complete_callback(request)
        if access_token:
            atrribs['access_token'] = access_token
        provider.save_token(email_client_id, **atrribs)

        # url이 노출되지 않도록 일반 url로 회송처리한다.
        return HttpResponseRedirect(reverse('oauth_emailbackend:oauth2callback-done'))


class OAuthCallbackDoneView(TemplateView):
    template_name = 'oauth_emailbackend/callback.html'
