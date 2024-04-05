from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, TemplateView

from oauth_emailbackend.models import EmailClient
from oauth_emailbackend.utils import get_provider_instance
from django.http import QueryDict

class OAuthCallbackView(TemplateView):
    # template_name = 'oauth_emailbackend/callback.html'

    def get(self, request, **kwargs):
        provider = get_provider_instance(provider_name=kwargs['provider_name'])

        # 프로바이더 레벌에서 인증과정을 완료한 다음 email_client_id, totken을 반환 / 저장 
        email_client_id, oauthdata = provider.complete_callback(request)
        provider.save_token(email_client_id, **oauthdata.get_emailclient_atrributes())

        # 인증전 폼 값 중 API관련 값만 저장한다. 
        form_data = request.COOKIES.get('oeb_form', None)
        if form_data:
            data =  QueryDict(form_data)
            eclient = EmailClient.objects.get(id=email_client_id)
            eclient.sender_name = data.get('sender_name', eclient.sender_name)
            eclient.site_id = data.get('site', eclient.site_id)
            eclient.is_active = True if data.get('is_active', True) in ('On', 'on', True) else False
            eclient.using = data.get('using', eclient.using)
            eclient.reply_to = data.get('reply_to', eclient.reply_to)
            eclient.cc = data.get('cc', eclient.cc)
            eclient.bcc = data.get('bcc', eclient.bcc)
            eclient.debug = True if data.get('debug', False) in ('On', 'on', True) else False

            eclient.save()

        # url이 노출되지 않도록 일반 url로 회송처리한다.
        return HttpResponseRedirect(reverse('oauth_emailbackend:oauth2callback-done'))


class OAuthCallbackDoneView(TemplateView):
    template_name = 'oauth_emailbackend/callback.html'
