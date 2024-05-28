# django-oauth-emailbackend
Django emailbackend that using OAuth Gmail API or SMTP server. 


## Installation

First, install the python package.

```
pip install django-oauth-emailbackend
```

Then, add the following to the `settings.py` of your project:

```
INSTALLED_APPS = [
    ...
    'django.contrib.sites',
    'oauth_emailbackend',
    ...
]

#----- django-oauth-emailbackend settings -----#
# EMAIL_BACKEND를 OAuthEmailBackend 설정 
# Celery를 이용하여 발송하는 경우 CELERY_BROKER_URL 값을 설정하여야 합니다.
EMAIL_BACKEND                = 'oauth_emailbackend.backends.OAuthEmailBackend'

# 발송내역을 저장할 DATABASE_NAME
OAUTH_EMAILCLIENT_DBNAME     = 'default'

# OAuth 목록 
OAUTH_EMAILBACKEND_PROVIDERS = (
    'oauth_emailbackend.providers.gmail',
)
# 콜백 도메인을 현재 사이트 도메인과 다르게 지정하려면 설정. 예) https://domain.to
OAUTH_EMAILBACKEND_CALLBACK_HOST    = None
OAUTH_EMAILBACKEND_USE_CELERY       = True
OAUTH_EMAILBACKEND_CELERY_MAX_RETRY = 3 # default=3
# OS SMTP server name
OAUTH_EMAILBACKEND_MTA              = 'postfix' # [None|postfix]


#----- celery settings -----#
# Celery를 이용하여 발송할 경우 CELERY_BROKER_URL 세팅 
CELERY_BROKER_URL = "<broker url for celery>"
#
# * Test run celery in localhost
# celery -A config worker -l info -E

```

Additionally, add this to your project urls.py:

```
urlpatterns = [
    ...
    # Add OAuth Emailbackend urls
    path('oauth_emailbackend/', include('oauth_emailbackend.urls')),
    ...
]
```

## Post-Installation

In your Django root execute the command below to create your database tables:

`python manage.py migrate`


## Register API client on the admin page

Visit `https://<host>/admin/oauth_emailbackend/oauthapi/` and 
add OAuth API and Email Client app sequentially.

## Test

```
from django.core.mail import send_mail

send_mail("Subject here",  
            "Here is the message.", 
            "<sender-email-address>", 
            ["<recipient-email-address>"],
            fail_silently=False)
```


## Providers

### Gmail

- `https://developers.google.com/gmail/api/guides`
- `https://console.cloud.google.com/` API 개설
- 사용자 인증 정보 에서 `OAuth 2.0 클라이언트 ID` 생성 
- OAuth 동의 화면 구성 
- **승인된 리디렉션 URI**에는 `https://<host>/oauth_emailbackend/oauth2callback/gmail`을 입력