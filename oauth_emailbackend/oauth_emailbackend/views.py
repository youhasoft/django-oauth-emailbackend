from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View

class OAuthCallbackView(HttpResponseRedirect):
    def get(self, request):
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
