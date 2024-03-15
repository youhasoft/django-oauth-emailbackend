


from abc import ABCMeta, abstractmethod
from django.http import QueryDict
from django.urls import reverse
from django.core.handlers.wsgi import WSGIRequest
from typing import List, TypeVar, Type, Optional
from django.db.models import Model
from django.conf import settings
from urllib.parse import urlparse

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
        host = getattr(settings, 'OAUTH_EMAILBACKEND_CALLBACK_HOST', None)
        if not host and request:
            # Callback url scheme must be https
            host = 'https://%s' % request.get_host()

        if not host:
            raise Exception('get_callback_uri has no "host"')
        
        return '%s%s' % (host, 
                         reverse('oauth_emailbackend:oauth2callback', kwargs={'provider': self.provider_key})
                        )
    
    @abstractmethod
    def get_authorization_url(self, 
                              request:WSGIRequest, 
                              oauthapi: Type[T],
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