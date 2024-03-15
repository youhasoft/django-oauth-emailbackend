
from django.http import QueryDict
from django.utils.translation import gettext_lazy as _
from django.core.handlers.wsgi import WSGIRequest
from typing import Optional, TypeVar, Type
from django.db.models import Model

from ..providers import ProviderInterface

T = TypeVar('T', bound=Model)


# 프로바이더 인증에 사용되는 추가 패키지 목록 
REQUIRED_PYPI_PACKAGES = (
    'google-api-python-client',
    'google-auth', 
    'google-auth-oauthlib', 
    'google-auth-httplib2',
)
OAUTH2ENDPOINT_URL = 'https://accounts.google.com/o/oauth2/v2/auth';


class OAuthProvider(ProviderInterface):
    provider_key = 'gmail'
    provider_name = _('Gmail (Google OAuth 2.0)')

    def get_authorization_url(self, 
                              request:WSGIRequest, 
                              oauthapi: Type[T],
                              emailclient: Type[T]) -> str:
        """
        OAuth 인증 URL을 리턴한다.
        """
        # 인자 확인: https://developers.google.com/identity/protocols/oauth2/web-server#python
        # https://accounts.google.com/o/oauth2/auth/oauthchooseaccount

        callback_uri = self.get_callback_uri( request );
        authorization_url = f"{OAUTH2ENDPOINT_URL}?client_id={oauthapi.client_id}" \
                            "&scope=https://www.googleapis.com/auth/gmail.send" \
                            "&response_type=code" \
                            "&access_type=offline" \
                            "&approval_prompt=force" \
                            "&flowName=GeneralOAuthFlow" \
                            f"&redirect_uri={callback_uri}" \
                            f"&state=emailclientId_{emailclient.id}||siteId=test" 
        
        return authorization_url
        
    def complete_callback(self, data: QueryDict):

        """
        # provider에서 전송된 토큰을 저장한다.
        # callback에서
        https://developers.google.com/identity/protocols/oauth2/web-server


        state = flask.session['state']
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            'client_secret.json',
            scopes=['https://www.googleapis.com/auth/drive.metadata.readonly'],
            state=state)
        flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

        authorization_response = flask.request.url
        flow.fetch_token(authorization_response=authorization_response)

        # Store the credentials in the session.
        # ACTION ITEM for developers:
        #     Store user's access and refresh tokens in your data store if
        #     incorporating this code into your real app.
        credentials = flow.credentials
        flask.session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}
        """

        
        print('***  data:', data)