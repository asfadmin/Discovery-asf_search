import requests
import http.cookiejar
from asf_search import __version__
from asf_search.constants import EDL_CLIENT_ID, EDL_HOST, ASF_AUTH_HOST
from asf_search.exceptions import ASFAuthenticationError

import copy

class ASFSession(requests.Session):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.headers.update({'User-Agent': f'{__name__}.{__version__}'})

        ### Figure out what auth method to use ###
        ## Possible params:
        #   Nothing -> Generic session
        #   (user, pass) or (username=user, password=pass) -> auth with creds session
        #   (cookiejar) or (cookies=cookiejar) -> auth with cookiejar session
        #   (myToken) or (token=myToken) -> auth with token session

        def add_if_new(key, val, main_dict):
            if key not in main_dict:
                main_dict[key] = val
            else:
                raise ValueError(f"Passed multiple '{key}' objects.")

        ## 1) Turn all args into kwargs:
        if len(args) == 0:
            pass
        elif len(args) == 1:
            # Check if cookejar:
            if isinstance(args[0], http.cookiejar.CookieJar):
                add_if_new("cookies", args[0], kwargs)
            # Check if token:
            elif isinstance(args[0], str):
                add_if_new("token", args[0], kwargs)
            # Else got no clue:
            else:
                raise ValueError(f"Unknown arg: '{args[0]}'.")
        elif len(args) == 2:
            # Check if user/pass:
            if isinstance(args[0], str) and isinstance(args[1], str):
                # This means you can't do half, i.e. parse_session("user", password="password"). Is this okay?
                add_if_new("username", args[0], kwargs)
                add_if_new("password", args[1], kwargs)
            else:
                raise ValueError(f"Unknown args: '{args}'.")
        else: # len(args) > 2:
            raise ValueError(f"Too many args passed: '{args}'.")
        
        ## 2) Parse kwargs to see which session to call:
        if len(kwargs) == 0:
            return
        elif len(kwargs) == 1:
            if "token" in kwargs and isinstance(kwargs["token"], str):
                self.auth_with_token(kwargs["token"])
                return
            if "cookies" in kwargs and isinstance(kwargs["cookies"], http.cookiejar.CookieJar):
                self.auth_with_cookiejar(kwargs["cookies"])
                return
        elif len(kwargs) == 2:
            if set(["username", "password"]).issubset(kwargs) and isinstance(kwargs["username"], str) and isinstance(kwargs["password"], str):
                self.auth_with_creds(kwargs["username"], kwargs["password"])
                return
        raise ValueError(f"No known auth method found. {kwargs}")


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
