from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from builtins import isinstance
from django.utils.timezone import now
from django.conf import settings
# from simsaprocess import proc_choices
# from manuscript.models import Manuscript
# from servermgt.utils import send_itsm_incident_message

User = get_user_model()

class SendHistory(models.Model):
    """
    비동기 이메일 발송내역...
    """
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
    # manuscript = models.ForeignKey('manuscript.Manuscript', 
    #                                on_delete=models.SET_NULL, 
    #                                null=True, 
    #                                blank=True)
    
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
PROVIDERS = (
    ('Gmail', 'Gmail'),
    ('Outlook', 'Outlook'),
)

class Provider(models.Model):
    name = models.CharField(_('Provider Name'), max_length=40, unique=True, choices=PROVIDERS)
    client_id = models.CharField('CLIENT_ID', max_length=255)
    client_secret = models.CharField('CLIENT_SECRET', max_length=255)
    remarks = models.TextField(_('Remarks'), null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = _('Provider')
        db_table = 'oauthemailbackend_provider'

    def __str__(self):
        if self.id:
            return self.name 
        
        return super().__str__()
    
    def get_authorization_url(self, request):
        # 인자 확인: https://developers.google.com/identity/protocols/oauth2/web-server#python
        if self.name == 'Gmail':
            oauth2endpoint = 'https://accounts.google.com/o/oauth2/v2/auth';
            redirect_uri = 'https://dev.youhasoft.com/oauth_emailbackend/oauth2callback/Gmail';

            # https://accounts.google.com/o/oauth2/auth/oauthchooseaccount
            authorization_url = f"{oauth2endpoint}?client_id={self.client_id}" \
                                "&scope=https://www.googleapis.com/auth/gmail.send" \
                                "&response_type=code" \
                                "&access_type=offline" \
                                "&approval_prompt=force" \
                                "&flowName=GeneralOAuthFlow" \
                                f"&redirect_uri={redirect_uri}" \
                                f"&state=OAuthCallback_gmail%40objectId_{self.id}" 

        print("*authorization_url= ", authorization_url)

        return authorization_url

    """
    # https://accounts.google.com/o/oauth2/auth/oauthchooseaccount
    ?client_id=
    &scope=email https://www.googleapis.com/auth/gmail.send
    &response_type=code
    &access_type=offline
    &approval_prompt=force
    &redirect_uri=https%3A%2F%2Fupdate.synology.com%2Fgmail_notification%2Fredirect.php
    &state=_mailFormOAuthCallback_gmail%40https%3A%2F%2F192-168-0-138.youhakr.direct.quickconnect.to%3A5001%2Fwebman%2Fmodules%2FPersonalSettings%2Findex_ds.php%40use_pkce
    &code_challenge=MfEPDocNeduELozJMp5HoeaJDisTT5FiWd6W_JU4bts
    &code_challenge_method=S256
    &service=lso
    &o2v=1
    &theme=glif
    &flowName=GeneralOAuthFlow
    """

class EmailHost(models.Model):
    is_active = models.BooleanField(_('Active'), default=True,
                                    help_text='언체크하면 settings.py에서 설성한 기본 계정으로 발송됩니다.')
    database = models.CharField('데이터베이스 이름', max_length=30, 
                                default=getattr(settings, 'OAUTH_EMAILBACKEND_DBNAME', 'default'), 
                                help_text='이메일 발송에 사용될 데이터베이스명입니다.')
    site = models.OneToOneField(Site, on_delete=models.CASCADE,)
    host = models.CharField("이메일 발송 호스트", max_length=50, default=settings.EMAIL_HOST, help_text=settings.EMAIL_HOST)
    send_method = models.CharField('발송 방법', max_length=15, default='smtp', choices=EMAIL_SEND_METHODS)
    user = models.CharField("이메일", max_length=70, default=settings.EMAIL_HOST_USER)
    
    # google OAuth api
    # provider  = models.CharField(_('Provider'), max_length=20, choices=PROVIDERS, null=True, blank=True)
    provider  = models.ForeignKey(Provider, null=True, blank=True, verbose_name=_('Provider'), on_delete=models.SET_NULL)
    api_token = models.TextField(_('API TOKEN'), null=True, blank=True)

    # smtp option
    security_protocol = models.CharField('보안 프로토콜', max_length=15, null=True, blank=True, choices=EMAIL_SECURITY_PROTOCOL)
    port = models.PositiveSmallIntegerField(null=True, blank=True, help_text=settings.EMAIL_PORT)
    password = models.CharField("비밀번호", max_length=30, null=True, blank=True)

    # 기타 메일 정보  
    from_email = models.CharField('보내일 메일', max_length=120, null=True, blank=True)
    reply_to = models.CharField('반송 메일', max_length=120, null=True, blank=True)
    cc = models.CharField('참조', max_length=220, null=True, blank=True, help_text='컴마로 구분합니다.')
    bcc = models.CharField('숨은 참조', max_length=220, null=True, blank=True, help_text='컴마로 구분합니다.')
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = verbose_name_plural = _('Email Host')
        db_table = 'oauthemailbackend_emailhost'
    
    def __str__(self):
        return super().__str__()

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