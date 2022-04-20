import numbers
from typing import List
from asf_search.ASFSession import ASFSession
from requests.cookies import create_cookie
import http.cookiejar
import requests

from unittest.mock import patch

def run_auth_with_creds(username: str, password: str):
    session = ASFSession()
    session.auth_with_creds(username=username, password=password)

def run_auth_with_token(token: str):
    session = ASFSession()

    with patch('asf_search.ASFSession.get') as mock_token_session:
        if not token.startswith('Bearer EDL'):
                mock_token_session.return_value.status_code = 400
                session.auth_with_token(token)

        mock_token_session.return_value.status_code = 200
        session.auth_with_token(token)

def run_auth_with_cookiejar(cookies: List):
    cookiejar = http.cookiejar.CookieJar()
    for cookie in cookies:
        cookiejar.set_cookie(create_cookie(name=cookie.pop('name'), **cookie))
    session = ASFSession()
    session.auth_with_cookiejar(cookies)

def run_test_asf_session_rebuild_auth(original_domain: str, response_domain: str, response_code: numbers.Number):
    session = ASFSession()

    with patch('asf_search.ASFSession.get') as mock_token_session:
        mock_token_session.return_value.status_code = 200
        session.auth_with_token("bad_token")
        
        req = requests.Request(original_domain)
        req.headers.update({'Authorization': 'Bearer fakeToken'})
        response = requests.Response()
        response.status_code = response_code
        response.location = response_domain
        
        response.headers.update({'Location' : response_domain})
        
        with patch('requests.utils.urlparse') as hostname_patch:
            hostname_patch.hostname.side_effect = [original_domain, response_domain]
            # hostname_patch.hostname = original_domain
            
            # original_domain_patch.return_value = original_domain        
            session.rebuild_auth(req, response)
        
            if response_code != 200:
                assert response.headers.get("Authorization") == None
            else:
                assert response.headers.get("Authorization") == session.headers.get("Authorization")