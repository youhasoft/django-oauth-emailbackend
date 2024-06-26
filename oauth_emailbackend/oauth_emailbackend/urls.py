from django.urls import path
from django.urls.conf import include
from oauth_emailbackend.views import OAuthCallbackDoneView, OAuthCallbackView

app_name = 'oauth_emailbackend'
urlpatterns = [
    path('oauth2callback/<str:provider_name>', OAuthCallbackView.as_view(), name='oauth2callback',),
    path('oauth2callback-done', OAuthCallbackDoneView.as_view(), name='oauth2callback-done',),
]
