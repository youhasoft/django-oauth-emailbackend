from django.urls import path
from django.urls.conf import include
from oauth_emailbackend.views import OAuthCallbackView

app_name = 'oauth_emailbackend'
urlpatterns = [
    path('oauth2callback/<str:provider>', OAuthCallbackView.as_view(), name='oauth2callback',),
]
