from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path

from .forms import EmailHostAdminForm, ProviderAdminForm
from .models import Provider, SendHistory, EmailHost
from django.utils.translation import gettext_lazy, gettext_lazy as _
from django.core.mail.message import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

# def resend_email(modeladmin, request, queryset):
#     """
#     이메일을 동일한 아이디로 재발송 시도합니다.
#     이메일에 수정된 내용은 없습니다.
#     """
#     # queryset.update(is_active=1)
#     for emaillog in queryset:
#         # print('%d -- %s -- %s' % (emaillog.pk, emaillog.recipients, emaillog.subject))
#         procemail = SimsaProcessEmail(process=None, 
#                                        manuscript=None, 
#                                        email_category=None,
#                                        site=emaillog.site)
#         history_pk  = emaillog.pk
#         attach      = None 
#         subject     = emaillog.subject
#         body_html   = emaillog.body
#         from_email  = None
#         to_email    = eval(emaillog.recipients)
#         lang    = None
            
#         procemail._send_mail(subject, body_html, lang, from_email, to_email, attach, history_pk)
        
#     messages.add_message(request, messages.INFO, '이메일을 %d건을 재발송하였습니다.' % queryset.count())

# resend_email.short_description = gettext_lazy(u"선택된 이메일을 재발송합니다.")



@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'client_id', 'created', )
    search_fields = ('name',  ) 
    form = ProviderAdminForm


@admin.register(SendHistory)
class SendHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'get_recipients', 'category', #'manuscript',  #'message_id', 
                    'arranged_time', 'sent_time', 'success', )
    search_fields = ('subject', 'recipients', 'message_id' ) #'manuscript__ms_number', 
    list_filter = (
        #    ('site', NameSortedRelatedDropdownFilter),
        #    ("sent_time", DateRangeFilterBuilder()),
           'site',
           'sent_time',
           'category', 
        )
    raw_id_fields = ('user', 'site') #'manuscript', 
    readonly_fields = ('arranged_time','sent_time',  'success', 'category',   #'manuscript',
                       'subject', 'user', 'recipients', 'site', 'body', 'message_id')
    
    # actions = [resend_email, ]
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return True
    
    def get_recipients(self, obj):
        try:
            return ', '.join(eval(obj.recipients))
        except:
            return obj.recipients
        


@admin.register(EmailHost)
class EmailHostAdmin(admin.ModelAdmin):
    list_display = ('site', 'host', 'send_method', 'provider', 'security_protocol', 'created', )
    search_fields = ('site__name', 'site__domain', 'host' )
    list_filter = (
           'site',
           'send_method',
           'provider',
        )
    raw_id_fields = ('site',) #'manuscript', 
    form = EmailHostAdminForm
    save_on_top = True
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

    # gcloud console 프로젝트 생성하여 OAuth 동의화면을 구성한다.
    https://console.cloud.google.com/apis/credentials/consent?project=gmailapi-415604
    """
    fieldsets = (
            (None, {
                'fields': ( 'is_active', 'database', 'site', 'host', 'user', 'send_method',  ),
            }),
            (mark_safe('''OAuth API  
                       '''), 
                       {
                'fields': ( 'provider', 'api_token', ),
                'classes': ('oauthapi-option',)
            }),
            ("SMTP", {
                'fields': ( 'security_protocol', 'port', 'password', ),
                'classes': ('smtp-option',)
            }),
            ("Email Addresses", {
                'fields': ( 'from_email', 'reply_to', 'cc', 'bcc' ),
            }),
    )

    def get_urls(self):
        return [
            path(
                '<id>/redirect2provider/<provider_id>',
                self.admin_site.admin_view(self.redirect2provider_view),
                name='redirect2oauthapi',
            ),
        ] + super().get_urls()

    def redirect2provider_view(self, request, id, provider_id):
        try:
            provider = Provider.objects.get(id=provider_id)
        except Exception as e:
            print(e)
            raise e

        return HttpResponseRedirect(provider.get_authorization_url(request))
