import platform
from typing import Dict, List, Union
import requests
from requests.utils import get_netrc_auth
import http.cookiejar
from asf_search import __name__ as asf_name, __version__ as asf_version
from asf_search.exceptions import ASFAuthenticationError

class ASFSession(requests.Session):
    def __init__(self, 
                edl_host: str = None,
                edl_client_id: str = None,
                asf_auth_host: str = None,
                cmr_host: str = None,
                cmr_collections: str = None,
                auth_domains: List[str] = None,
                auth_cookie_names: List[str] = None
                ):
        """
        ASFSession is a subclass of `requests.Session`, and is meant to ease downloading ASF hosted data by simplifying logging in to Earthdata Login.
        To create an EDL account, see here: https://urs.earthdata.nasa.gov/users/new
        
        ASFSession provides three built-in methods for authorizing downloads:
        - EDL Username and Password: `auth_with_creds()`
        - EDL Token: `auth_with_token()`
        - Authenticated cookiejars: `auth_with_cookiejar()`

        `edl_host`: the Earthdata login endpoint used by auth_with_creds(). Defaults to `asf_search.constants.INTERNAL.EDL_HOST`
        `edl_client_id`: The Earthdata Login client ID for this package. Defaults to `asf_search.constants.INTERNAL.EDL_CLIENT_ID`
        `asf_auth_host`: the ASF auth endpoint . Defaults to `asf_search.constants.INTERNAL.ASF_AUTH_HOST`
        `cmr_host`: the base CMR endpoint to test EDL login tokens against. Defaults to `asf_search.constants.INTERNAL.CMR_HOST`
        `cmr_collections`: the CMR endpoint path login tokens will be tested against. Defaults to `asf_search.constants.INTERNAL.CMR_COLLECTIONS`
        `auth_domains`: the list of authorized endpoints that are allowed to pass auth credentials. Defaults to `asf_search.constants.INTERNAL.AUTH_DOMAINS`. Authorization headers WILL NOT be stripped from the session object when redirected through these domains.
        `auth_cookie_names`: the list of cookie names to use when verifying with `auth_with_creds()` & `auth_with_cookiejar()`
        More information on Earthdata Login can be found here:
        https://urs.earthdata.nasa.gov/documentation/faq
        """
        super().__init__()
        user_agent = '; '.join([
            f'Python/{platform.python_version()}',
            f'{requests.__name__}/{requests.__version__}',
            f'{asf_name}/{asf_version}'])

        self.headers.update({'User-Agent': user_agent})  # For all hosts
        self.headers.update({'Client-Id': f"{asf_name}_v{asf_version}"})  # For CMR

        from asf_search.constants import INTERNAL

        self.edl_host = INTERNAL.EDL_HOST if edl_host is None else edl_host
        self.edl_client_id = INTERNAL.EDL_CLIENT_ID if edl_client_id is None else edl_client_id
        self.asf_auth_host = INTERNAL.ASF_AUTH_HOST if asf_auth_host is None else asf_auth_host
        self.cmr_host = INTERNAL.CMR_HOST if cmr_host is None else cmr_host
        self.cmr_collections = INTERNAL.CMR_COLLECTIONS if cmr_collections is None else cmr_collections
        self.auth_domains = INTERNAL.AUTH_DOMAINS if auth_domains is None else auth_domains
        self.auth_cookie_names = INTERNAL.AUTH_COOKIES if auth_cookie_names is None else auth_cookie_names

    def __eq__(self, other):
        return self.auth == other.auth \
           and self.headers == other.headers \
           and self.cookies == other.cookies

    def auth_with_creds(self, username: str, password: str):
        """
        Authenticates the session using EDL username/password credentials

        :param username: EDL username, see https://urs.earthdata.nasa.gov/
        :param password: EDL password, see https://urs.earthdata.nasa.gov/
        :param host (optional): EDL host to log in to 

        :return ASFSession: returns self for convenience
        """
        login_url = f'https://{self.edl_host}/oauth/authorize?client_id={self.edl_client_id}&response_type=code&redirect_uri=https://{self.asf_auth_host}/login'

        self.auth = (username, password)
        self.get(login_url)

        if not self._check_auth_cookies(self.cookies.get_dict()):
            raise ASFAuthenticationError("Username or password is incorrect")

        return self

    def auth_with_token(self, token: str):
        """
        Authenticates the session using an EDL Authorization: Bearer token

        :param token: EDL Auth Token for authenticated downloads, see https://urs.earthdata.nasa.gov/user_tokens

        :return ASFSession: returns self for convenience
        """
        self.headers.update({'Authorization': 'Bearer {0}'.format(token)})

        url = f"https://{self.cmr_host}{self.cmr_collections}"
        response = self.get(url)

        if not 200 <= response.status_code <= 299:
            raise ASFAuthenticationError("Invalid/Expired token passed")

        return self

    def auth_with_cookiejar(self, cookies: http.cookiejar.CookieJar):
        """
        Authenticates the session using a pre-existing cookiejar

        :param cookies: Any http.cookiejar compatible object

        :return ASFSession: returns self for convenience
        """
        
        if not self._check_auth_cookies(cookies):
            raise ASFAuthenticationError("Cookiejar does not contain login cookies")

        for cookie in cookies:
            if cookie.is_expired():
                raise ASFAuthenticationError("Cookiejar contains expired cookies")

        self.cookies = cookies

        return self

    def _check_auth_cookies(self, cookies: Union[http.cookiejar.CookieJar, Dict]) -> bool:
        return any(cookie in self.auth_cookie_names for cookie in cookies)

    def rebuild_auth(self, prepared_request: requests.Request, response: requests.Response):
        """
        Overrides requests.Session.rebuild_auth() default behavior of stripping the Authorization header
        upon redirect. This allows token authentication to work with redirects to trusted domains
        """

        headers = prepared_request.headers
        url = prepared_request.url

        if 'Authorization' in headers:
            original_domain = '.'.join(self._get_domain(response.request.url).split('.')[-3:])
            redirect_domain = '.'.join(self._get_domain(url).split('.')[-3:])

            if (original_domain != redirect_domain 
                and (original_domain not in self.auth_domains
                or redirect_domain not in self.auth_domains)):
                del headers['Authorization']

        new_auth = get_netrc_auth(url) if self.trust_env else None
        if new_auth is not None:
            prepared_request.prepare_auth(new_auth)

    def _get_domain(self, url: str):
            return requests.utils.urlparse(url).hostname

    # multi-processing does an implicit copy of ASFSession objects,  
    # this ensures ASFSession class variables are included
    def __getstate__(self):
        state = super().__getstate__()
        state = {
            **state,
            'edl_host': self.edl_host,
            'edl_client_id': self.edl_client_id,
            'asf_auth_host': self.asf_auth_host,
            'cmr_host': self.cmr_host,
            'cmr_collections': self.cmr_collections,
            'auth_domains': self.auth_domains,
            'auth_cookie_names': self.auth_cookie_names
        }
        return state
