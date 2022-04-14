from typing import List
from asf_search.ASFSession import ASFSession
from requests.cookies import create_cookie
import http.cookiejar

def run_auth_with_creds(username: str, password: str):
    session = ASFSession()
    session.auth_with_creds(username=username, password=password)

def run_auth_with_token(token: str):
    session = ASFSession()
    session.auth_with_token(token=token)

def run_auth_with_cookiejar(cookies: List):
    cookiejar = http.cookiejar.CookieJar()
    for cookie in cookies:
        cookiejar.set_cookie(create_cookie(name=cookie.pop('name'), **cookie))
    session = ASFSession()
    session.auth_with_cookiejar(cookies)