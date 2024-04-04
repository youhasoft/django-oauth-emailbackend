from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path
from oauth_emailbackend.utils import get_provider_name
from django.utils.translation import gettext_lazy, gettext_lazy as _
from django.core.mail.message import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from .forms import EmailClientAdminForm, OAuthAPIAdminForm
from .models import EmailClient, OAuthAPI, SendHistory, EmailClient

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



@admin.register(OAuthAPI)
class OAuthAPIAdmin(admin.ModelAdmin):
    list_display = ('provider_display', 'created', )
    search_fields = ('provider',  ) 
    form = OAuthAPIAdminForm

    def provider_display(self, obj):
        return "%s" % get_provider_name( obj.provider )
    provider_display.short_description = 'Provider'

@admin.register(SendHistory)
class SendHistoryAdmin(admin.ModelAdmin):
    list_display = ('message_id', 'success', 'retry_count', 'subject', 'sent_time',  )
    search_fields = ('subject', 'recipients', 'message_id' ) #'manuscript__ms_number', 
    list_filter = (
           'site',
           'sent_time',
        )
    raw_id_fields = ('site',) #'manuscript', 
    readonly_fields = ('arranged_time','sent_time',  'success', #'category',   #'manuscript',
                       'subject', 'recipients', 'site', 'raw', 'error_message', 'retry_count')
    
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
        


@admin.register(EmailClient)
class EmailClientAdmin(admin.ModelAdmin):
    list_display = ('site', 'send_method', 'oauthapi', 'security_protocol', 'created', )
    search_fields = ('site__name', 'site__domain', 'host' )
    list_filter = (
           'site',
           'send_method',
           'oauthapi',
        )
    raw_id_fields = ('site',) #'manuscript', 
    form =EmailClientAdminForm
    save_on_top = True
    """
    # gcloud console 프로젝트 생성하여 OAuth 동의화면을 구성한다.
    https://console.cloud.google.com/apis/credentials/consent?project=gmailapi-415604
    """
    fieldsets = (
            (None, {
                'fields': ( 'is_active', 'site', 'using', 'send_method', 'sender_name'),
            }),
            (mark_safe('''OAuth API  
                       '''), 
                       {
                'fields': ( 'api_email', 'oauthapi', 'access_token', 'refresh_token', 'token_expiry'),
                'classes': ('oauthapi-option',)
            }),
            ("SMTP", {
                'fields': ( 'smtp_email', 'smtp_host', 'security_protocol', 'port', 'password', ),
                'classes': ('smtp-option',)
            }),
            ("Email Addresses and Log", {
                'fields': ('reply_to', 'cc', 'bcc', 'debug'),
            }),
    )

    def get_urls(self):
        return [
            path(
                '<emailclient_id>/redirect2provider/<api_id>',
                self.admin_site.admin_view(self.redirect2provider_view),
                name='redirect2oauthapi',
            ),
        ] + super().get_urls()
    
    def redirect2provider_view(self, request, emailclient_id, api_id):
        try:
            oauthapi = OAuthAPI.objects.get(id=api_id)
        except Exception as e:
            print(e)
            raise e

        return HttpResponseRedirect(oauthapi.get_authorization_url(request, 
                                                                   emailclient_id=emailclient_id))
