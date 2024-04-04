from typing import Any
from django.shortcuts import render
from django.views.generic import FormView
from django.core.mail import send_mail
from django.contrib import messages
from oauth_emailbackend.utils import get_use_celery
from testapp.forms import SendEmailForm
from django.utils.timezone import now
from django.apps import apps

class SendEmailView(FormView):
    form_class = SendEmailForm
    template_name = "testapp/send-email.html"

    def get_initial(self) -> dict[str, Any]:
        initial = super().get_initial()
        try:
            emailclient = self.request.site.emailclient
            if emailclient.send_method == 'api':
                email = emailclient.api_email
            else:
                email = emailclient.smtp_email

            initial['from_address'] = email
            initial['to_address']   = 'ssoizo@naver.com'
            initial['subject']      = 'OAuth Email Test %s' % now()
            initial['body']         = '''Hello me!\nOAuth Email Bod %s!\n
피로에 지친 교수들…병동 축소 이어 근무시간 줄이기
아주대 의대 교수협의회 비대위는 교수들에게 법정 근로 시간인 주 52시간에 맞춰 근무할 것을 권고하고 있다.
            ''' % now()
        except:
            pass

        return initial
    
    def get_success_url(self) -> str:
        return './'
    
    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request 

        return kwargs 
    
    def form_valid(self, form):
        # Send email
        data = form.cleaned_data 
        success = send_mail(data['subject'],  
                    data['body'], 
                    data['from_address'], 
                    [data['to_address']],
                    fail_silently=True
                    )
        
        print('-success: %s' % success)
        if success:
            if get_use_celery():
                messages.info(self.request, '이메일을 발송 예약하였습니다. 발송 내역을 확인하십시오.')
            else:
                messages.success(self.request, '이메일을 성공적으로 발송하였습니다.')
        else:
            messages.error(self.request, '이메일을 발송 중 오류가 발생하였습니다.')

        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, '아래 폼 에러를 수정하십시오.')
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context['use_celery'] = apps.get_app_config('oauth_emailbackend').use_celery
        return context 