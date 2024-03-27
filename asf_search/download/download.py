from typing import Dict, Iterable, List
from multiprocessing import Pool
import os.path
from urllib import parse
from requests import Response
from requests.exceptions import HTTPError
import warnings

from asf_search.exceptions import ASFAuthenticationError, ASFDownloadError
from asf_search import ASF_LOGGER, ASFSession
from tenacity import retry, stop_after_delay, retry_if_result, wait_fixed

try:
    from remotezip import RemoteZip
    import boto3
except ImportError:
    RemoteZip = None
    boto3 = None

def _download_url(arg):
    url, path, session = arg
    download_url(
        url=url,
        path=path,
        session=session)


def download_urls(urls: Iterable[str], path: str, session: ASFSession = None, processes: int = 1):
    """
    Downloads all products from the specified URLs to the specified location.

    :param urls: List of URLs from which to download
    :param path: Local path in which to save the product
    :param session: The session to use, in most cases should be authenticated beforehand
    :param processes: Number of download processes to use. Defaults to 1 (i.e. sequential download)
    :return:
    """
    if session is None:
        session = ASFSession()

    if processes <= 1:
        for url in urls:
            download_url(url=url, path=path, session=session)
    else:
        pool = Pool(processes=processes)
        args = [(url, path, session) for url in urls]
        pool.map(_download_url, args)
        pool.close()
        pool.join()


def download_url(url: str, path: str, filename: str = None, session: ASFSession = None) -> None:
    """
    Downloads a product from the specified URL to the specified location and (optional) filename.

    :param url: URL from which to download
    :param path: Local path in which to save the product
    :param filename: Optional filename to be used, extracted from the URL by default
    :param session: The session to use, in most cases should be authenticated beforehand
    :return:
    """
    
    if filename is None:
        filename = os.path.split(parse.urlparse(url).path)[1]
    
    if not os.path.isdir(path):
        raise ASFDownloadError(f'Error downloading {url}: directory not found: {path}')

    if os.path.isfile(os.path.join(path, filename)):
        warnings.warn(f'File already exists, skipping download: {os.path.join(path, filename)}')
        return

    if session is None:
        session = ASFSession()

    response = _try_get_response(session=session, url=url)
    
    with open(os.path.join(path, filename), 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def remotezip(url: str, session: ASFSession) -> 'RemoteZip':
    """
    :param url: the url to the zip product
    :param session: the authenticated ASFSession to read and download from the zip file
    """
    if RemoteZip is None:
        raise ImportError("Could not find remotezip package in current python environment. \"remotezip\" is an optional dependency of asf-search required for the `remotezip()` method. Enable by including the appropriate pip or conda install. Ex: `python3 -m pip install asf-search[extras]`")
    
    session.hooks['response'].append(strip_auth_if_aws)
    return RemoteZip(url, session=session)

def strip_auth_if_aws(r, *args, **kwargs):
    if 300 <= r.status_code <= 399 and 'amazonaws.com' in parse.urlparse(r.headers['location']).netloc:
        location = r.headers['location']
        r.headers.clear()
        r.headers['location'] = location

# if it's an unprocessed burst product it'll return a 202 and we'll have to query again 
# https://sentinel1-burst-docs.asf.alaska.edu/
def _is_burst_processing(response: Response):
    return response.status_code == 202

@retry(reraise=True,
       retry=retry_if_result(_is_burst_processing),
       wait=wait_fixed(1),
       stop=stop_after_delay(90),
    )
def _try_get_response(session: ASFSession, url: str):
    response = session.get(url, stream=True, hooks={'response': strip_auth_if_aws})

    try:
        response.raise_for_status()
    except HTTPError as e:
        if 400 <= response.status_code <= 499:
            raise ASFAuthenticationError(f'HTTP {e.response.status_code}: {e.response.text}')

        raise e

    return response

def download_s3_urls(urls: Iterable[str], path: str, botoS3Client, extraArgs: Dict = {}, processes: int = 1):
    if processes <= 1:
        for url in urls:
            download_s3_url(url=url, path=path, botoS3Client=botoS3Client, extraArgs=extraArgs)
    else:
        pool = Pool(processes=processes)
        args = [(url, path, botoS3Client, extraArgs) for url in urls]
        pool.map(_download_s3_url, args)
        pool.close()
        pool.join()

def _download_s3_url(arg):
    url, path, botoS3Client, extraArgs = arg
    download_s3_url(
        url=url,
        path=path,
        botoS3Client=botoS3Client,
        extraArgs=extraArgs)
    
def download_s3_url(url: str, path: str, botoS3Client = None, extraArgs: Dict = {}, fileName=None) -> None:
    if boto3 is None:
        raise ImportError("Could not find boto3 package in current python environment. \"boto3\" is an optional dependency of asf-search required for the `download_from_s3()` method. Enable by including the appropriate pip or conda install. Ex: `python3 -m pip install asf-search[extras]`")
    
    if botoS3Client is None:
        botoS3Client = boto3.client('s3')
    
    if not os.path.isdir(path):
        raise ASFDownloadError(f'Error downloading {url}: directory not found: {path}')

    parsed = parse.urlparse(url)
    
    if fileName is None:
        filename = os.path.join(path, os.path.basename(parsed.path))
    else:
        fileName = os.path.join(path, fileName)
    
    if os.path.isfile(filename):
        warnings.warn(f'File already exists, skipping download: {os.path.join(path, filename)}')
        return
    
    bucket = parsed.netloc
    object_name = parsed.path.lstrip('/')

    ASF_LOGGER.info(f"Downloading object \"{object_name}\" from s3 bucket: \"{bucket}\"")

    try:
        botoS3Client.download_file(bucket, object_name, filename, extraArgs)
        ASF_LOGGER.info(f"Object \"{object_name}\" downloaded from s3 bucket: \"{bucket}\"")
    except Exception as exc:
        error_message = f"Error downloading \"{object_name}\" from s3 bucket: \"{bucket}\". Reason: {exc}"
        ASF_LOGGER.warning(error_message)
        raise ASFDownloadError(error_message)
