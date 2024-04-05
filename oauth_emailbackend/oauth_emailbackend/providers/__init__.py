


from abc import ABCMeta, abstractmethod
from django.http import QueryDict
from django.urls import reverse
from django.core.handlers.wsgi import WSGIRequest
from typing import ByteString, Dict, List, Tuple, TypeVar, Type, Optional
from django.db.models import Model
from django.conf import settings
from urllib.parse import urlparse
from oauth_emailbackend.models import EmailClient
# from datetime import datetime
from django.utils.timezone import now, make_aware
import datetime

T = TypeVar('T', bound=Model)

UTC = datetime.timezone(datetime.timedelta(hours=0))

class OAuthData:
    _token_expiry = None 

    def __init__(self, access_token: str, 
                 refresh_token: str, 
                 token_expiry: datetime.datetime, 
                 extra_attribs: Dict) -> None:
        
        self._access_token = access_token
        self._refresh_token = refresh_token

        if token_expiry:
            self._token_expiry = make_aware( token_expiry, timezone = UTC )

        self._extra_attribs = extra_attribs

    @property 
    def access_token(self):
        return self._access_token
    
    @property 
    def refresh_token(self):
        return self._refresh_token
    
    @property 
    def token_expiry(self):
        return self._token_expiry
    
    @property 
    def extra_attribs(self):
        return self.extra_attribs
    
    def get_emailclient_atrributes(self) -> Dict:
        attribs = self._extra_attribs
        attribs['access_token']  = self.access_token
        if self.refresh_token:
            attribs['refresh_token'] = self.refresh_token
        if self.token_expiry:
            attribs['token_expiry']  = self.token_expiry

        return attribs


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
    def complete_callback(self, data: QueryDict) -> Tuple[str, OAuthData]:
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
        email_client.send_method = 'api'
        email_client.save(update_fields=atrribs.keys())

    @abstractmethod
    def sendmail(self, emailclient: Type[T], message_as_byte: ByteString, **kwargs):
        """
        API를 이용한 이메일 발송 구현 
        """
        pass
