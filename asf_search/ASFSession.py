import platform
import requests
from requests.utils import get_netrc_auth
import http.cookiejar
from asf_search import __name__ as asf_name, __version__ as asf_version
from asf_search.constants import EDL_CLIENT_ID, EDL_HOST, ASF_AUTH_HOST, AUTH_DOMAINS
from asf_search.exceptions import ASFAuthenticationError

class ASFSession(requests.Session):

    def __init__(self):
        super().__init__()
        user_agent = '; '.join([
            f"{asf_name}/{asf_version}",
            f'Python/{platform.python_version()}',
            f'{requests.__name__}/{requests.__version__}'])

        self.headers.update({'User-Agent': user_agent})  # For all hosts
        self.headers.update({'Client-Id': f"{asf_name}_v{asf_version}"})  # For CMR

    def __eq__(self, other):
        return self.auth == other.auth \
           and self.headers == other.headers \
           and self.cookies == other.cookies

    def auth_with_creds(self, username: str, password: str):
        """
        Authenticates the session using EDL username/password credentials

        :param username: EDL username, see https://urs.earthdata.nasa.gov/
        :param password: EDL password, see https://urs.earthdata.nasa.gov/

        :return ASFSession: returns self for convenience
        """
        login_url = f'https://{EDL_HOST}/oauth/authorize?client_id={EDL_CLIENT_ID}&response_type=code&redirect_uri=https://{ASF_AUTH_HOST}/login'

        self.auth = (username, password)
        self.get(login_url)

        if "urs_user_already_logged" not in self.cookies.get_dict():
            raise ASFAuthenticationError("Username or password is incorrect")

        return self

    def auth_with_token(self, token: str):
        """
        Authenticates the session using an EDL Authorization: Bearer token

        :param token: EDL Auth Token for authenticated downloads, see https://urs.earthdata.nasa.gov/user_tokens

        :return ASFSession: returns self for convenience
        """
        self.headers.update({'Authorization': 'Bearer {0}'.format(token)})

        url = "https://cmr.earthdata.nasa.gov/search/collections"
        response = self.get(url)        

        if not 200 <= response.status_code <= 299:
            raise ASFAuthenticationError("Invalid/Expired token passed")

        return self

    def auth_with_cookiejar(self, cookies: http.cookiejar):
        """
        Authenticates the session using a pre-existing cookiejar

        :param cookies: Any http.cookiejar compatible object

        :return ASFSession: returns self for convenience
        """
        
        if "urs_user_already_logged" not in cookies:
            raise ASFAuthenticationError("Cookiejar does not contain login cookies")

        for cookie in cookies:
            if cookie.is_expired():
                raise ASFAuthenticationError("Cookiejar contains expired cookies")

        self.cookies = cookies

        return self

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
                and (original_domain not in AUTH_DOMAINS
                or redirect_domain not in AUTH_DOMAINS)):
                del headers['Authorization']

        new_auth = get_netrc_auth(url) if self.trust_env else None
        if new_auth is not None:
            prepared_request.prepare_auth(new_auth)

    def _get_domain(self, url: str):
            return requests.utils.urlparse(url).hostname
