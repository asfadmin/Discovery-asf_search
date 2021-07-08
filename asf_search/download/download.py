from typing import Iterable
from multiprocessing import Pool
import os.path
import urllib.parse
import requests

from asf_search import __version__
from asf_search.exceptions import ASFDownloadError


def _download_url(arg):
    url, path, token = arg
    download_url(
        url=url,
        path=path,
        token=token)


def download_urls(urls: Iterable[str], path: str, token: str, processes: int = 1):
    pool = Pool(processes=processes)
    args = [(url, path, token) for url in urls]
    pool.map(_download_url, args)
    pool.close()
    pool.join()


def download_url(url: str, path: str, filename: str = None, token: str = None) -> None:
    """
    Downloads a product from the specified URL to the specified location and (optional) filename.

    :param url: URL from which to download
    :param path: Local path in which to save the product
    :param filename: Optional filename to be used, extracted from the URL by default
    :param token: EDL Auth Token for authenticating downloads, see https://urs.earthdata.nasa.gov/user_tokens
    :return:
    """
    if filename is None:
        filename = os.path.split(urllib.parse.urlparse(url).path)[1]

    if not os.path.isdir(path):
        raise ASFDownloadError(f'Error downloading {url}: directory not found: {path}')

    if os.path.isfile(os.path.join(path, filename)):
        raise ASFDownloadError(f'File already exists: {os.path.join(path, filename)}')

    headers = {'User-Agent': f'{__name__}.{__version__}'}
    if token is not None:
        headers['Authorization'] = f'Bearer {token}'

    print(f'Following {url}')
    response = requests.get(url, stream=True, allow_redirects=False)
    print(f'response: {response.status_code}')
    while 300 <= response.status_code <= 399:
        new_url = response.headers['location']
        print(f'Redirect to {new_url}')
        if 'aws.amazon.com' in urllib.parse.urlparse(new_url).netloc:
            response = requests.get(new_url, stream=True, allow_redirects=False)  # S3 detests auth headers
        else:
            response = requests.get(new_url, stream=True, headers=headers, allow_redirects=False)
        print(f'response: {response.status_code}')
    response.raise_for_status()
    with open(os.path.join(path, filename), 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
