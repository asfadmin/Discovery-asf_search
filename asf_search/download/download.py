from typing import Iterable
from multiprocessing import Pool
import os.path
import urllib.parse
import requests
import http.cookiejar

from asf_search import __version__
from asf_search.exceptions import ASFDownloadError

def get_asf_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({'User-Agent': f'{__name__}.{__version__}'})
    return session

def get_session_creds(username: str, password: str) -> requests.Session:
    """
    Gives a session, with username/password added to the headers.

    :param username: The username to EDL
    :param password: The password to EDL
    :return: session object
    """
    session = get_asf_session()
    login_url = "https://urs.earthdata.nasa.gov/oauth/authorize?client_id=BO_n7nTIlMljdvU6kRRB3g&response_type=code&redirect_uri=https://auth.asf.alaska.edu/login"

    session.auth = (username, password)
    session.get(login_url)
    return session

def get_session_token(token: str) -> requests.Session:
    """
    Gives a session, with the token pre-added.

    :param token: EDL Auth Token for authenticated downloads, see https://urs.earthdata.nasa.gov/user_tokens
    :return: session object
    """
    session = get_asf_session()
    session.headers.update({'Authorization': 'Bearer {0}'.format(token)})
    return session


def get_session_cookies(cookies: http.cookiejar) -> requests.Session:
    """
    Gives a session, with cookies added.

    :param cookies: Any http.cookiejar compatible object
    :return: session object
    """
    session = requests.Session()
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
