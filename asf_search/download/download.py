import os.path
import urllib.parse
import requests
from importlib.metadata import PackageNotFoundError, version

from asf_search.exceptions import ASFDownloadError


def download_url(url: str, dir: str, filename: str = None, token: str = None) -> None:
    """
    Downloads a product from the specified URL to the specified location and (optional) filename.

    :param url: URL from which to download
    :param dir: Directory in which to save the product
    :param filename: Optional filename to be used, extracted from the URL by default
    :param token: EDL Auth Token for authenticating downloads, see https://urs.earthdata.nasa.gov/user_tokens
    :return:
    """
    if filename is None:
        filename = os.path.split(urllib.parse.urlparse(url).path)[1]

    if not os.path.isdir(dir):
        raise ASFDownloadError(f'Error downloading {url}: directory not found: {dir}')

    if os.path.isfile(os.path.join(dir, filename)):
        raise ASFDownloadError(f'File already exists: {os.path.join(dir, filename)}')

    try:
        pkg_version = version(__name__)
    except PackageNotFoundError:
        pkg_version = '0.0.0'
    headers = {'User-Agent': f'{__name__}.{pkg_version}'}
    if token is not None:
        headers['Authorization'] = f'Bearer {token}'

    response = requests.get(url, stream=True, allow_redirects=False)
    while 300 <= response.status_code <= 399:
        new_url = response.headers['location']
        if 'aws.amazon.com' in urllib.parse.urlparse(new_url).netloc:
            response = requests.get(new_url, stream=True, allow_redirects=False)  # S3 detests auth headers
        else:
            response = requests.get(new_url, stream=True, headers=headers, allow_redirects=False)
    response.raise_for_status()
    with open(os.path.join(dir, filename), 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)