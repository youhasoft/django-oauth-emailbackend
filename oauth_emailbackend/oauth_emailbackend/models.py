import uuid
from django.core.handlers.wsgi import WSGIRequest
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from builtins import isinstance
from django.utils.timezone import now
from django.conf import settings
from django.utils.encoding import smart_str
from oauth_emailbackend.utils import get_provider_instance, get_provider_name
# from simsaprocess import proc_choices
# from manuscript.models import Manuscript
# from servermgt.utils import send_itsm_incident_message

User = get_user_model()

class SendHistory(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    category = models.CharField('분류', max_length=20, null=True, blank=True, #default='default', choices=proc_choices.PROC_EMAIL_KEYS
                                )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    recipients = models.CharField('수신자들', max_length=1200, null=True, blank=True)
    
    subject = models.CharField('타이틀', max_length=200)
    body = models.TextField('본문', null=True, blank=True)
    
    arranged_time = models.DateTimeField("예약시간", auto_now_add=True)
    sent_time = models.DateTimeField("발송시간", null=True, blank=True)
    success = models.BooleanField(null=True,)
    
    # by odop 2021.10.14 / added
    # 이메일 메시지 아이디... 발송 이메일을 웹에서 확인하고자 할 때 키로 사용된다.
    message_id = models.UUIDField(null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = _('Email Sending History') 
        db_table = 'oauthemailbackend_emailsendhistory'
        
    def __str__(self):
        return self.subject


EMAIL_SEND_METHODS = (
    ('smtp', _('사용자 지정 SMTP 서버')),
    ('api', _('OAuth 이메일 API')),
)
EMAIL_SECURITY_PROTOCOL = (
    ('tls', 'TLS'),
    ('ssl', 'SSL'),
)

class OAuthAPI(models.Model):
    provider = models.CharField(_('Provider'), max_length=140, unique=True, )
    # client_id = models.CharField('CLIENT_ID', max_length=255)
    # client_secret = models.CharField('CLIENT_SECRET', max_length=255)
    client_config = models.JSONField("클라이언트 설정(JSON)", 
                                   null=True, 
                                   help_text="CLIENT_ID, CLIENT_SECRET이 포함된 보안 비밀번호 json 파일")
    remarks = models.TextField(_('Remarks'), null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = '   OAuth API'
        db_table = 'oauthemailbackend_oauthapi'

    def __str__(self):
        if self.id:
            return "%s" % get_provider_name( self.provider )
        return super().__str__()
    
    def get_authorization_url(self, request: WSGIRequest, emailclient_id: int) -> str:
        # provider에 따라 인증 url을 생성한다.
        emailcleint = EmailClient.objects.get(id=emailclient_id)
        authorization_url = self.provider_instance.get_authorization_url(request, emailcleint)

        return authorization_url
    
    @property
    def provider_instance(self):
        return get_provider_instance( self.provider )
    
    


class EmailClient(models.Model):
    """
    사이트별 이메일 발송에 사용할 클라이언트 
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(_('Active'), default=True,
                                    help_text='언체크하면 settings.py에서 설성한 기본 계정으로 발송됩니다.')
    site = models.OneToOneField(Site, on_delete=models.CASCADE,)
    database = models.CharField('데이터베이스 이름', max_length=30, 
                                default=getattr(settings, 'OAUTH_EMAILCLIENT_DBNAME', 'default'), 
                                help_text='이메일 발송 히스토리를 저장할 때 접속할 데이터베이스 이름입니다.')
    send_method = models.CharField('발송 방법', max_length=15, default='smtp', choices=EMAIL_SEND_METHODS)
    user = models.EmailField("사용자 이메일", )
    
    # google OAuth api
    # provider  = models.CharField(_('Provider'), max_length=20, choices=PROVIDERS, null=True, blank=True)
    oauthapi  = models.ForeignKey(OAuthAPI, null=True, blank=True, verbose_name=_('OAuth API'), on_delete=models.SET_NULL)
    access_token = models.TextField('접속 Token', null=True, blank=True)
    refresh_token = models.TextField('갱신 Token', null=True, blank=True)
    next_token_refresh_date = models.DateTimeField('다음 Token 갱신일', null=True, blank=True, help_text='갱신일 이전에 자동 갱신 시도합니다.')

    # smtp option
    smtp_host = models.CharField("SMTP 발송 호스트", max_length=50, null=True, blank=True)
    security_protocol = models.CharField('보안 프로토콜', max_length=15, null=True, blank=True, choices=EMAIL_SECURITY_PROTOCOL)
    port = models.PositiveSmallIntegerField(null=True, blank=True, help_text=settings.EMAIL_PORT)
    password = models.CharField("비밀번호", max_length=30, null=True, blank=True)

    # 기타 메일 정보  
    reply_to = models.CharField('반송 메일', max_length=120, null=True, blank=True)
    cc = models.CharField('참조', max_length=220, null=True, blank=True, help_text='컴마로 구분합니다.')
    bcc = models.CharField('숨은 참조', max_length=220, null=True, blank=True, help_text='컴마로 구분합니다.')
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = verbose_name_plural = 'Email Client'
        db_table = 'oauthemailbackend_emailclient'
    
    @property
    def provider_name(self):
        # Name of provider
        if self.send_method != 'smtp':
            return self.oauthapi.provider
        else:
            return 'smtp'
        
    def sendmail(self, from_email, recipients, message_as_byte):
        if not self.is_active or self.send_method == "smtp":
            raise Exception("Can not sendamil. is_active=%s, send_model=%s" % 
                            (self.is_active, self.send_method))
        kwd = {
            'from_email': from_email,
            'recipients': recipients,
        }
        provider = self.oauthapi.provider_instance
        provider.sendmail(emailclient=self,
                          message_as_byte=message_as_byte, 
                          **kwd)

    def quit(self):
        pass 

    def close(self):
        pass



def add_mail_history(site, category, user, recipients, subject, body, 
                     manuscript=None, 
                     message_id=None,
                     using='default'): 
    """
     발송히스토리를 생성한다.
    """
    obj = SendHistory.objects.using(using).create(
        site=site,
        category=category,
        user=user,
        recipients=recipients,
        subject=subject,
        body=body,
        message_id=message_id,
        )
    # if isinstance(manuscript, Manuscript):
    #     obj.manuscript = manuscript
    #     obj.save(update_fields=['manuscript'])
    
    return obj.pk
    
def mark_email_sent(pk, success):
    """
    실제발송시간을 마크한다.
    """
    try:
        obj = SendHistory.objects.filter(id=pk)
        obj.update(sent_time=now(), success=bool(success))
    except Exception as e:
        print("-mark_email_sent error for %r \n%r" % (pk, e))
        subject = '이메일 발송 기록 오류.\n\n%r' % (e,)
        # send_itsm_incident_message(subject, None, send_type='LM')