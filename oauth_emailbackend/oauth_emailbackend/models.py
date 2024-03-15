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
    client_id = models.CharField('CLIENT_ID', max_length=255)
    client_secret = models.CharField('CLIENT_SECRET', max_length=255)
    remarks = models.TextField(_('Remarks'), null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = _('  OAuth API')
        db_table = 'oauthemailbackend_oauthapi'

    def __str__(self):
        if self.id:
            return "%s" % get_provider_name( self.provider )
        return super().__str__()
    
    def get_authorization_url(self, request: WSGIRequest, emailclient_id: int) -> str:
        # provider에 따라 인증 url을 생성한다.
        print('OAuthAPI.get_authorization_url()')

        provider_instance = get_provider_instance( self.provider )
        emailcleint = EmailClient.objects.get(id=emailclient_id)
        authorization_url = provider_instance.get_authorization_url(request, self, emailcleint)

        print("*** authorization_url = ", authorization_url)

        return authorization_url


class EmailClient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(_('Active'), default=True,
                                    help_text='언체크하면 settings.py에서 설성한 기본 계정으로 발송됩니다.')
    site = models.OneToOneField(Site, on_delete=models.CASCADE,)
    database = models.CharField('데이터베이스 이름', max_length=30, 
                                default=getattr(settings, 'OAUTH_EMAILBACKEND_DBNAME', 'default'), 
                                help_text='이메일 발송에 사용될 데이터베이스명입니다.')
    send_method = models.CharField('발송 방법', max_length=15, default='smtp', choices=EMAIL_SEND_METHODS)
    user = models.CharField("사용자 이메일", max_length=70, default=settings.EMAIL_HOST_USER)
    
    # google OAuth api
    # provider  = models.CharField(_('Provider'), max_length=20, choices=PROVIDERS, null=True, blank=True)
    oauthapi  = models.ForeignKey(OAuthAPI, null=True, blank=True, verbose_name=_('OAuth API'), on_delete=models.SET_NULL)
    api_token = models.TextField(_('API TOKEN'), null=True, blank=True)

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
        verbose_name = verbose_name_plural = _('Email Client')
        db_table = 'oauthemailbackend_emailclient'
    
    # def __str__(self):
    #     return super().__str__()
    

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