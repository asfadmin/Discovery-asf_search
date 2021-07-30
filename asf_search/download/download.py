from typing import Iterable
from multiprocessing import Pool
import os.path
import urllib.parse
import requests
import http.cookiejar

from asf_search import __version__
from asf_search.exceptions import ASFDownloadError, ASFAuthenticationError
from asf_search.constants import EDL_CLIENT_ID, EDL_HOST, ASF_AUTH_HOST


def get_asf_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({'User-Agent': f'{__name__}.{__version__}'})
    return session


def get_session_creds(username: str, password: str) -> requests.Session:
    """
    Builds a session using EDL username/password credentials

    :param username: EDL username, see https://urs.earthdata.nasa.gov/
    :param password: EDL password, see https://urs.earthdata.nasa.gov/
    :return: requests.Session object
    """
    session = get_asf_session()
    login_url = f'https://{EDL_HOST}/oauth/authorize?client_id={EDL_CLIENT_ID}&response_type=code&redirect_uri=https://{ASF_AUTH_HOST}/login'

    session.auth = (username, password)
    session.get(login_url)

    if "urs_user_already_logged" not in session.cookies.get_dict():
        raise ASFAuthenticationError("Username password combo is incorrect")

    return session


def get_session_token(token: str) -> requests.Session:
    """
    Builds a session using an EDL Authorization: Bearer token

    :param token: EDL Auth Token for authenticated downloads, see https://urs.earthdata.nasa.gov/user_tokens
    :return: requests.Session object
    """
    session = get_asf_session()
    session.headers.update({'Authorization': 'Bearer {0}'.format(token)})
    return session


def get_session_cookies(cookies: http.cookiejar) -> requests.Session:
    """
    Builds a session using a pre-existing cookiejar

    :param cookies: Any http.cookiejar compatible object
    :return: requests.Session object
    """
    session = get_asf_session()
    session.cookies = cookies
    return session


def _download_url(arg):
    url, path, session = arg
    download_url(
        url=url,
        path=path,
        session=session)


def download_urls(urls: Iterable[str], path: str, session: requests.Session = None, processes: int = 1):
    pool = Pool(processes=processes)
    args = [(url, path, session) for url in urls]
    pool.map(_download_url, args)
    pool.close()
    pool.join()


def download_url(url: str, path: str, filename: str = None, session: requests.Session = None) -> None:
    """
    Downloads a product from the specified URL to the specified location and (optional) filename.

    :param url: URL from which to download
    :param path: Local path in which to save the product
    :param filename: Optional filename to be used, extracted from the URL by default
    :param session: The session to use, with headers attached. Defaults to get_asf_session().
    :return:
    """
    if filename is None:
        filename = os.path.split(urllib.parse.urlparse(url).path)[1]

    if not os.path.isdir(path):
        raise ASFDownloadError(f'Error downloading {url}: directory not found: {path}')

    if os.path.isfile(os.path.join(path, filename)):
        raise ASFDownloadError(f'File already exists: {os.path.join(path, filename)}')

    if session is None:
        session = get_asf_session()

    print(f'Following {url}')
    response = session.get(url, stream=True, allow_redirects=False)
    print(f'response: {response.status_code}')
    while 300 <= response.status_code <= 399:
        new_url = response.headers['location']
        print(f'Redirect to {new_url}')
        response = session.get(new_url, stream=True, allow_redirects=False)
        print(f'response: {response.status_code}')
    response.raise_for_status()
    with open(os.path.join(path, filename), 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
