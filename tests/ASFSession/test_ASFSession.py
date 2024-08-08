import numbers
from typing import List
import asf_search
from asf_search.ASFSession import ASFSession
from requests.cookies import create_cookie
import http.cookiejar
import requests
from multiprocessing import Pool

from unittest.mock import patch


def run_auth_with_creds(username: str, password: str):
    session = ASFSession()
    session.auth_with_creds(username=username, password=password)


def run_auth_with_token(token: str):
    session = ASFSession()

    with patch('asf_search.ASFSession.post') as mock_token_session:
        if not token.startswith('Bearer EDL'):
            mock_token_session.return_value.status_code = 400
            session.auth_with_token(token)

        mock_token_session.return_value.status_code = 200
        session.auth_with_token(token)


def run_auth_with_cookiejar(cookies: List):
    cookiejar = http.cookiejar.CookieJar()
    for cookie in cookies:
        cookiejar.set_cookie(create_cookie(name=cookie.pop('name'), **cookie))

    # requests.cookies.RequestsCookieJar, which has slightly different behaviour
    session = ASFSession()
    session.auth_with_cookiejar(cookiejar)

    request_cookiejar_session = ASFSession()
    request_cookiejar_session.auth_with_cookiejar(session.cookies)


def run_test_asf_session_rebuild_auth(
    original_domain: str,
    response_domain: str,
    response_code: numbers.Number,
    final_token,
):
    if final_token == 'None':
        final_token = None

    session = ASFSession()

    with patch('asf_search.ASFSession.post') as mock_token_session:
        mock_token_session.return_value.status_code = 200
        session.auth_with_token('bad_token')

        req = requests.Request(original_domain)
        req.headers.update({'Authorization': 'Bearer fakeToken'})

        response = requests.Response()
        response.status_code = response_code
        response.location = response_domain
        response.request = requests.Request()
        response.request.url = response_domain
        response.headers.update({'Authorization': 'Bearer fakeToken'})

        with patch('asf_search.ASFSession._get_domain') as hostname_patch:
            hostname_patch.side_effect = [original_domain, response_domain]

            session.rebuild_auth(req, response)

            assert req.headers.get('Authorization') == final_token


def test_ASFSession_INTERNAL_mangling():
    session = asf_search.ASFSession()
    session.cmr_host = asf_search.constants.INTERNAL.EDL_HOST
    session.edl_host = asf_search.constants.INTERNAL.EDL_CLIENT_ID
    session.auth_cookie_names = asf_search.constants.INTERNAL.ASF_AUTH_HOST
    session.auth_domains = asf_search.constants.INTERNAL.CMR_HOST
    session.asf_auth_host = asf_search.constants.INTERNAL.CMR_COLLECTIONS
    session.cmr_collections = asf_search.constants.INTERNAL.AUTH_DOMAINS
    session.edl_client_id = asf_search.constants.INTERNAL.AUTH_COOKIES

    # get the current defaults since we're going to mangle them
    DEFAULT_EDL_HOST = asf_search.constants.INTERNAL.EDL_HOST
    DEFAULT_EDL_CLIENT_ID = asf_search.constants.INTERNAL.EDL_CLIENT_ID
    DEFAULT_ASF_AUTH_HOST = asf_search.constants.INTERNAL.ASF_AUTH_HOST
    DEFAULT_CMR_HOST = asf_search.constants.INTERNAL.CMR_HOST
    DEFAULT_CMR_COLLECTIONS = asf_search.constants.INTERNAL.CMR_COLLECTIONS
    DEFAULT_AUTH_DOMAINS = asf_search.constants.INTERNAL.AUTH_DOMAINS
    DEFAULT_AUTH_COOKIES = asf_search.constants.INTERNAL.AUTH_COOKIES

    uat_domain = 'cmr.uat.earthdata.nasa.gov'
    edl_client_id = 'custom_client_id'
    auth_host = 'custom_auth_host'
    cmr_collection = '/search/granules'
    auth_domains = ['custom_auth_domain']
    uat_login_cookie = ['uat_urs_user_already_logged']
    uat_login_domain = 'uat.urs.earthdata.nasa.gov'

    asf_search.constants.INTERNAL.CMR_HOST = uat_domain
    asf_search.constants.INTERNAL.EDL_HOST = uat_login_domain
    asf_search.constants.INTERNAL.AUTH_COOKIES = uat_login_cookie
    asf_search.constants.INTERNAL.EDL_CLIENT_ID = edl_client_id
    asf_search.constants.INTERNAL.AUTH_DOMAINS = auth_domains
    asf_search.constants.INTERNAL.ASF_AUTH_HOST = auth_host
    asf_search.constants.INTERNAL.CMR_COLLECTIONS = cmr_collection

    mangeled_session = asf_search.ASFSession()

    # set them back
    asf_search.constants.INTERNAL.EDL_HOST = DEFAULT_EDL_HOST
    asf_search.constants.INTERNAL.EDL_CLIENT_ID = DEFAULT_EDL_CLIENT_ID
    asf_search.constants.INTERNAL.ASF_AUTH_HOST = DEFAULT_ASF_AUTH_HOST
    asf_search.constants.INTERNAL.CMR_HOST = DEFAULT_CMR_HOST
    asf_search.constants.INTERNAL.CMR_COLLECTIONS = DEFAULT_CMR_COLLECTIONS
    asf_search.constants.INTERNAL.AUTH_DOMAINS = DEFAULT_AUTH_DOMAINS
    asf_search.constants.INTERNAL.AUTH_COOKIES = DEFAULT_AUTH_COOKIES

    assert mangeled_session.cmr_host == uat_domain
    assert mangeled_session.edl_host == uat_login_domain
    assert mangeled_session.auth_cookie_names == uat_login_cookie
    assert mangeled_session.auth_domains == auth_domains
    assert mangeled_session.asf_auth_host == auth_host
    assert mangeled_session.cmr_collections == cmr_collection
    assert mangeled_session.edl_client_id == edl_client_id

    custom_session = asf_search.ASFSession(
        cmr_host=uat_domain,
        edl_host=uat_login_domain,
        auth_cookie_names=uat_login_cookie,
        auth_domains=auth_domains,
        asf_auth_host=auth_host,
        cmr_collections=cmr_collection,
        edl_client_id=edl_client_id,
    )

    assert custom_session.cmr_host == uat_domain
    assert custom_session.edl_host == uat_login_domain
    assert custom_session.auth_cookie_names == uat_login_cookie
    assert custom_session.auth_domains == auth_domains
    assert custom_session.asf_auth_host == auth_host
    assert custom_session.cmr_collections == cmr_collection
    assert custom_session.edl_client_id == edl_client_id


def test_ASFSession_pooling():
    uat_domain = 'cmr.uat.earthdata.nasa.gov'
    edl_client_id = 'custom_client_id'
    auth_host = 'custom_auth_host'
    cmr_collection = '/search/granules'
    auth_domains = ['custom_auth_domain']
    uat_login_cookie = ['uat_urs_user_already_logged']
    uat_login_domain = 'uat.urs.earthdata.nasa.gov'

    custom_session = asf_search.ASFSession(
        cmr_host=uat_domain,
        edl_host=uat_login_domain,
        auth_cookie_names=uat_login_cookie,
        auth_domains=auth_domains,
        asf_auth_host=auth_host,
        cmr_collections=cmr_collection,
        edl_client_id=edl_client_id,
    )
    Pool()
    pool = Pool(processes=2)
    pool.map(_assert_pooled_instance_variables, [custom_session, custom_session])
    pool.close()
    pool.join()


def _assert_pooled_instance_variables(session):
    uat_domain = 'cmr.uat.earthdata.nasa.gov'
    edl_client_id = 'custom_client_id'
    auth_host = 'custom_auth_host'
    cmr_collection = '/search/granules'
    auth_domains = ['custom_auth_domain']
    uat_login_cookie = ['uat_urs_user_already_logged']
    uat_login_domain = 'uat.urs.earthdata.nasa.gov'
    assert session.cmr_host == uat_domain
    assert session.edl_host == uat_login_domain
    assert session.auth_cookie_names == uat_login_cookie
    assert session.auth_domains == auth_domains
    assert session.asf_auth_host == auth_host
    assert session.cmr_collections == cmr_collection
    assert session.edl_client_id == edl_client_id
