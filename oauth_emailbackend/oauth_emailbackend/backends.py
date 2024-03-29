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
from .tasks import celery_send_emails
from .utils import chunked, email_to_dict


 
class OAuthEmailBackend(SMTPEmailBackend):
    """
    ref: site-packages/django/core/mail/backends/smtp.py
    """
    def __init__(self, fail_silently=True, **kwd):
        super( ).__init__(**kwd)

        self.fail_silently  = fail_silently
        self.init_kwargs    = kwd

        self.cc             = None
        self.bcc            = None
        self.reply_to       = None

        self.emailclient_id   = kwd.get('emailclient_id', None)

        
    def get_site_email_client(self, site=None):
        if self.emailclient_id:
            return EmailClient.objects.get(id=self.emailclient_id)
        
        if site and site.emailclient and site.emailclient.is_active:
            return site.emailclient
        
        return EmailClient()

    def open(self, emailclient):
        if self.connection:
            return False
        
        if emailclient.provider_name == 'smtp':
            # smtp 방식인 경우 부모 클래스(SMTPEmailBackend) 위임 
            if emailclient.id:
                self.host = emailclient.smtp_host
                self.port = emailclient.port
                self.username = emailclient.smtp_email
                self.password = emailclient.password
                self.use_tls = emailclient.security_protocol == 'tls'

                # settings.py의 EMAIL_USE_SSL 값을 대신한다. 
                # use_tls이 참이면 use_ssl도 참으로 세팅한다. 
                self.use_ssl = emailclient.security_protocol == 'ssl' or self.use_tls 
                
                #
                self.css = emailclient.cc.split(",") if emailclient.cc else None
                self.bcc = emailclient.bcc.split(",") if emailclient.bcc else None
                self.reply_to = emailclient.reply_to.split(",") if emailclient.reply_to else None

            return super().open()
        else:
            # api 방식인 경우 emailclient를 connection 역할을 대신한다.
            self.connection = emailclient

            if emailclient.id:
                self.css = emailclient.cc.split(",") if emailclient.cc else None
                self.bcc = emailclient.bcc.split(",") if emailclient.bcc else None
                self.reply_to = emailclient.reply_to.split(",") if emailclient.reply_to else None
            return True

    def send_messages(self, email_messages, enable_celery=True):
        """
        Send one or more EmailMessage objects and return the number of email
        messages sent.
        @enable_celery : 가능하면 celery 이메일 발송을 허용한다.
        """
        if not email_messages:
            return 0
        
        with self._lock:
            site = None

            if not self.emailclient_id:
                site = getattr(email_messages[0], 'site', None)
                if not site:
                    site = Site.objects.get(id=settings.SITE_ID)

            emailclient = self.get_site_email_client(site)
            
            num_sent = 0
            new_conn_created = self.open(emailclient)
            if not self.connection or new_conn_created is None:
                return 0
            
            from_email = emailclient.api_email if emailclient.send_method == 'api' else emailclient.smtp_email
            if emailclient.sender_name:
                from_email = f'{emailclient.sender_name} <{from_email}>'

            for message in email_messages:
                message.from_email = from_email
                if self.css:
                    message.cc = self.css
                if self.bcc:
                    message.bcc = self.bcc
                if self.reply_to:
                    message.reply_to = self.reply_to
            
            if enable_celery and apps.get_app_config('oauth_emailbackend').use_celery:
                # Using celery.
                # 특정 데이터베이스와 이메일 호스트를 지정하여 이메일을 발송할 수 있도록 수정 
                celery_email_chunk_size = getattr(settings, "CELERY_EMAIL_CHUNK_SIZE", 10)
                
                # Celery에 이메일 발송 함수전달하기 위해 Dict로 변환 
                messages = [email_to_dict(msg) for msg in email_messages]
                
                for chunk in chunked(messages, celery_email_chunk_size):
                    celery_send_emails.delay(chunk, 
                                                emailclient.id, 
                                                emailclient.using,
                                                backend_kwargs=self.init_kwargs)
                num_sent += 1
            else:
                try:
                    for message in email_messages:
                        sent = self._send(message)
                        if sent:
                            num_sent += 1
                finally:
                    if new_conn_created:
                        self.close()
                        
        print('--num_sent= %d' % num_sent)
        return num_sent

    