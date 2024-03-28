import smtplib
import threading
import ssl
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address
from django.utils.functional import cached_property

from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.core.mail import EmailMessage, get_connection
from django.contrib.sites.models import Site

from django.apps import apps
from oauth_emailbackend.models import EmailClient
# from .tasks import send_emails
# from .utils import chunked, email_to_dict


 
class OAuthEmailBackend(SMTPEmailBackend):
    """
    ref: site-packages/django/core/mail/backends/smtp.py
    """
    def __init__(self, fail_silently=True, **kwd):
        super( ).__init__(**kwd)
        self.fail_silently = fail_silently
        self.init_kwargs = kwd

        self.cc = None
        self.bcc = None
        self.reply_to = None
        
    def get_site_email_client(self, site):
        if site.emailclient and site.emailclient.is_active:
            return site.emailclient
        return EmailClient()

    def open(self, emailclient):
        if self.connection:
            return False
        
        if emailclient.provider_name == 'smtp':
            # 클라이언트 설정된 경우 
            if emailclient.id:
                self.host = emailclient.smtp_host
                self.port = emailclient.port
                self.username = emailclient.user
                self.password = emailclient.password
                self.use_tls = emailclient.security_protocol == 'tls'
                self.use_ssl = emailclient.security_protocol == 'ssl'
                
                #
                self.css = emailclient.cc.split(",") if emailclient.cc else None
                self.bcc = emailclient.bcc.split(",") if emailclient.bcc else None
                self.reply_to = emailclient.reply_to.split(",") if emailclient.reply_to else None

            return super().open()
        else:
            # emailclient를 대신 할당한다.
            self.connection = emailclient
            if emailclient.id:
                self.css = emailclient.cc.split(",") if emailclient.cc else None
                self.bcc = emailclient.bcc.split(",") if emailclient.bcc else None
                self.reply_to = emailclient.reply_to.split(",") if emailclient.reply_to else None
            return True


    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number of email
        messages sent.
        """
        if not email_messages:
            return 0
        
        with self._lock:
            site = getattr(email_messages[0], 'site', None)
            if not site:
                site = Site.objects.get(id=settings.SITE_ID)

            emailclient = self.get_site_email_client(site)
            num_sent = 0

            if not apps.get_app_config('oauth_emailbackend').use_celery:
                new_conn_created = self.open(emailclient)
                if not self.connection or new_conn_created is None:
                    # We failed silently on open().
                    # Trying to send would be pointless.
                    return 0
                
                try:
                    for message in email_messages:
                        if self.css:
                            message['cc'] = self.css
                        if self.bcc:
                            message['bcc'] = self.bcc
                        if self.bcc:
                            message['reply_to'] = self.reply_to

                        sent = self._send(message)
                        if sent:
                            num_sent += 1
                finally:
                    if new_conn_created:
                        self.close()
            else:
                # Use celery.
                pass 

        return num_sent

    

# class OAuthCeleryEmailBackend(BaseEmailBackend):
#     def __init__(self, fail_silently=False, **kwargs):
#         super( ).__init__(fail_silently)
#         self.init_kwargs = kwargs

#     def send_messages(self, email_messages):
#         #import inspect
#         #print(inspect.getmodule(send_emails).__name__)
        
#         ''' by odop 2018.11.14 '''
#         # site 특정하여 발송 가능하도록 처리 
#         site_id = settings.SITE_ID
        
#         test = email_messages[0]
#         if hasattr(test, 'site'):
#             site_id = test.site.id
            
#         ''' by odop 2019.8.24 '''
#         # 특정 데이터베이스와 이메일 호스트를 지정하여 이메일을 발송할 수 있도록 수정 
        
#         email_server_name = getattr( test, 'email_server_name', 'default')
#         email_server_database = getattr( test, 'email_server_database', getattr(settings, 'OAUTH_EMAILBACKEND_DBNAME', 'default')) 
        
#         result_tasks = []
#         messages = [email_to_dict(msg) for msg in email_messages]
#         for chunk in chunked(messages, settings.CELERY_EMAIL_CHUNK_SIZE):
#             result_tasks.append(send_emails.delay(chunk, site_id, 
#                                                   email_server_name=email_server_name,
#                                                   email_server_database=email_server_database,
#                                                   backend_kwargs=self.init_kwargs))
#         return result_tasks

