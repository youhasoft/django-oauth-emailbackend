
from datetime import timedelta
import datetime
from email import message_from_bytes
import os
from django.http import QueryDict
from django.utils.translation import gettext_lazy as _
from django.core.handlers.wsgi import WSGIRequest
from typing import ByteString, Optional, Tuple, TypeVar, Type
from django.db.models import Model

import google_auth_oauthlib
from oauth_emailbackend.models import EmailClient
import base64
import google.auth
# from googleapiclient.discovery import build
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from django.utils.timezone import now, make_aware
import logging

from oauth_emailbackend.utils import add_send_history, mark_send_history, update_message_id
from ..providers import ProviderInterface
# from google.oauth2.credentials import Credentials

# # api 로그 수준 조정 
# logging.getLogger('googleapicliet.discovery_cache').setLevel(logging.ERROR)

# [TODO]
# file_cache is only supported with oauth2client<4.0.0 로그 출력되지 않게 하기 


# 프로바이더 인증에 사용되는 추가 패키지 목록 
REQUIRED_PYPI_PACKAGES = (
    'google-api-python-client',
    'google-auth', 
    'google-auth-oauthlib', 
    'google-auth-httplib2',
)
OAUTH2ENDPOINT_URL = 'https://accounts.google.com/o/oauth2/v2/auth';

CALLBACK_STATE_SPLITTER = '||'
SCOPES = ['https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.metadata',
          "https://www.googleapis.com/auth/userinfo.email"]

os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

T = TypeVar('T', bound=Model)

UTC = datetime.timezone(datetime.timedelta(hours=0))

class OAuthProvider(ProviderInterface):
    provider_key = 'gmail'
    provider_name = _('Gmail (Google OAuth 2.0)')
    
    def _get_oauth_flow(self, emailclient_id, state=None, callback_uri=None):
        emailclient    = EmailClient.objects.get(id=emailclient_id)
        client_config  = emailclient.oauthapi.client_config

        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            state=state)
        if callback_uri:
            flow.redirect_uri = callback_uri

        return flow
        
    def get_authorization_url(self, 
                              request:WSGIRequest, 
                              emailclient: Type[T]) -> str:
        """
        OAuth 인증 URL을 리턴한다.
        """
        # 인자 확인: https://developers.google.com/identity/protocols/oauth2/web-server#python
        # https://accounts.google.com/o/oauth2/auth/oauthchooseaccount

        # state값을 세션에 저장
        state = f'emailclientId_{emailclient.id}||siteId_test'
        request.session['state'] = state

        emailclient_id = emailclient.id
        flow = self._get_oauth_flow(emailclient_id, state, self.get_callback_uri( request ))
        authorization_url, _state = flow.authorization_url(
                                        access_type='offline',
                                        include_granted_scopes='true')
        
        return authorization_url
    
    def complete_callback(self, request:WSGIRequest) -> Tuple[str, str, str]:
        """
        # 인증후 전송된 값을 받아 완료하고, EmailClient.id와 토큰을 반환한다.
        # callback에서
        https://developers.google.com/identity/protocols/oauth2/web-server

        Step 5: Exchange authorization code for refresh and access tokens
        After the web server receives the authorization code, it can exchange the authorization code for an access token.       
        """
        state = request.session['state']

        _state = {}
        for val in state.split(CALLBACK_STATE_SPLITTER):
            _key, _value = val.split('_', 1)
            _state[_key] = _value 

        emailclient_id = _state['emailclientId']
        flow = self._get_oauth_flow(emailclient_id, state, self.get_callback_uri( request ))
        
        # Flow.fetch_token(**kwargs)
        # Args:
        #     kwargs: Arguments passed through to
        #         :meth:`requests_oauthlib.OAuth2Session.fetch_token`. At least
        #         one of ``code`` or ``authorization_response`` must be specified.
        flow.fetch_token(code=request.GET.get('code'))
        credentials = flow.credentials

        # Get profile
        session = flow.authorized_session()
        profile_info = session.get('https://www.googleapis.com/userinfo/v2/me').json()

        attribs = { 'api_email': profile_info['email']}
        if credentials.refresh_token:
            attribs['refresh_token'] = credentials.refresh_token
        if credentials.expiry:
            # token의 기본 유효시간은 1시간이다.
            expiry = make_aware( credentials.expiry, timezone = UTC )
            attribs['token_expiry'] = expiry;  #now() + timedelta(seconds = credentials.expires_in )


        return (emailclient_id, credentials.token, attribs)

    def refresh_access_token(self, emailclient: Type[T]) -> bool:
        # [TODO]
        # https://stackoverflow.com/questions/27771324/google-api-getting-credentials-from-refresh-token-with-oauth2client-client
        # https://developers.google.com/identity/protocols/oauth2#expiration
        credentials = self._get_credentials(emailclient)
        
        print("+ Credentials.valid: ", credentials.valid)
        if not credentials.valid:
            request = google.auth.transport.requests.Request()
            credentials.refresh(request)
            
            if credentials.token != emailclient.access_token:
                emailclient.access_token = credentials.token
                if credentials.expiry:
                    expiry = make_aware( credentials.expiry, timezone = UTC )
                    emailclient.token_expiry = expiry; 

                emailclient.save(  )

        return True
    
    def _get_credentials(self, emailclient: Type[T]) -> google.oauth2.credentials.Credentials:
        client_config = emailclient.oauthapi.client_config['web']
        
        acct_creds = {
            'token': emailclient.access_token,
            'refresh_token': emailclient.refresh_token,
            'client_id': client_config['client_id'],
            'client_secret': client_config['client_secret'],
            'token_uri': client_config['token_uri'],
            'scopes': SCOPES,
            }
        credentials = google.oauth2.credentials.Credentials(**acct_creds)

        return credentials

    def sendmail(self, emailclient: Type[T], message_as_byte: ByteString, **kwargs) -> str:
        """
        각 이메일 backend의 connection에서 구현되는 메시지로 최종적으로 이메일이 발송되는 메쏘드임 
        """
        if emailclient.token_expiry <= now():
            self.refresh_access_token(emailclient)

        credentials = self._get_credentials(emailclient)
        service = discovery.build("gmail", "v1", credentials=credentials)

        userId = 'me'

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message_as_byte).decode()
        create_message = {"raw": encoded_message}
        send_message = (
            service.users()
                .messages()
                .send(userId=userId, body=create_message)
                .execute()
        )

        # mail = message_from_bytes(message_as_byte)
        # old_message_id = mail.get('Message-ID')

        # 최종 발송된 메일의 Message-ID를 확인하여 업데이트한다.
        messageId = send_message["id"]
        message_info = service.users().messages().get(id=messageId, userId=userId, format="metadata").execute()
        headers = dict([ (x['name'], x['value']) for x in message_info['payload']['headers']])
        new_message_id = headers.get('Message-Id', None)
        print('new_message_id#1=', new_message_id)

        return new_message_id