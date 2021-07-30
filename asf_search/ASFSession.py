import requests
import http.cookiejar
from asf_search import __version__
from asf_search.constants import EDL_CLIENT_ID, EDL_HOST, ASF_AUTH_HOST
from asf_search.exceptions import ASFAuthenticationError


class ASFSession(requests.Session):
    def __init__(self):
        super().__init__()
        self.headers.update({'User-Agent': f'{__name__}.{__version__}'})

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

        return self

    def auth_with_cookiejar(self, cookies: http.cookiejar):
        """
        Authenticates the session using a pre-existing cookiejar

        :param cookies: Any http.cookiejar compatible object

        :return ASFSession: returns self for convenience
        """
        self.cookies = cookies

        return self
