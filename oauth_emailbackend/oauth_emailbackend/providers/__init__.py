


from abc import ABCMeta, abstractmethod
from django.http import QueryDict
from django.urls import reverse
from django.core.handlers.wsgi import WSGIRequest
from typing import ByteString, List, Tuple, TypeVar, Type, Optional
from django.db.models import Model
from django.conf import settings
from urllib.parse import urlparse
from oauth_emailbackend.models import EmailClient

T = TypeVar('T', bound=Model)


class ProviderInterface(metaclass=ABCMeta):
    @property
    @abstractmethod
    def provider_name(self):
        pass

    @property
    @abstractmethod
    def provider_key(self):
        pass

    def get_provider_name(self) -> str:
        return self.provider_name
    
    def get_callback_uri(self, request: Optional[WSGIRequest]) -> str:
        """
        콜백 URL을 반환한다.
        """
        host = getattr(settings, 'OAUTH_EMAILBACKEND_CALLBACK_HOST', None)
        if not host and request:
            # Callback url scheme must be https
            host = 'https://%s' % request.get_host()

        if not host:
            raise Exception('get_callback_uri has no "host"')
        
        return '%s%s' % (host, 
                         reverse('oauth_emailbackend:oauth2callback', kwargs={'provider_name': self.provider_key})
                        )
    
    @abstractmethod
    def get_authorization_url(self, 
                              request:WSGIRequest, 
                              emailclient: Type[T]) -> str:
        """
        OAuth 인증 URL을 리턴한다.
        """
        pass

    @abstractmethod
    def complete_callback(self, data: QueryDict):
        """
        콜백 정보를 받아 데이터베이스에 토큰을 저장한다.
        """
        pass


    @abstractmethod
    def refresh_access_token(self, emailclient: Type[T]) -> bool:
        """
        access token을 갱신한다.
        """
        return True

    def save_token(self, email_client_id, **atrribs):
        email_client = EmailClient.objects.get(id=email_client_id)
        for k in atrribs:
            setattr(email_client, k, atrribs[k])

        email_client.save(update_fields=atrribs.keys())

    @abstractmethod
    def sendmail(self, emailclient: Type[T], message_as_byte: ByteString, **kwargs):
        """
        API를 이용한 이메일 발송 구현 
        """
        pass