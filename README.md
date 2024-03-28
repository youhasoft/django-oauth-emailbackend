# django-celery-emailbackend
Django emailbackend with Celery that using IMAP and google OAuth api



# Third-party Packages

- google-api-python-client
- google-auth 
- google-auth-oauthlib 
- google-auth-httplib2


# Install 

```
pip install django-oauth-emailbackend
```

Add to INSTALLED_APPS in settings.py

```
INSTALLED_APPS = [
    ...
    # 'oauth_emailbackend.emailbackend',
    'oauth_emailbackend',
    ...
]
```

Add url in urls.py

```
urlpatterns = [
    ...
    # Add OAuth Emailbackend urls
    path('oauth_emailbackend/', include('oauth_emailbackend.urls')),
    ...
]
```


## Test

```
from django.core.mail import send_mail

send_mail("Subject here",  
            "Here is the message.", 
            "syl@youha.kr", 
            ["lee.soonyeon@gmail.com"],
            fail_silently=False)
```


