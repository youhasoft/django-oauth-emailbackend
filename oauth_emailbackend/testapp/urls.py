from django.urls import path
from django.urls.conf import include

from testapp.views import SendEmailView

app_name = 'testapp'
urlpatterns = [
    path('send-email/', SendEmailView.as_view(), name='send-edmail',),
]
