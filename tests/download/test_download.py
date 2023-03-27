import unittest

from requests_mock import Adapter
import requests_mock
from asf_search.exceptions import ASFAuthenticationError, ASFDownloadError
import pytest
from unittest.mock import patch

import requests

from asf_search.download.download import download_url

def run_test_download_url_auth_error(url, path, filename):
    with patch('asf_search.ASFSession.get') as mock_get:
        resp = requests.Response()
        resp.status_code = 401
        mock_get.return_value = resp 
        
        if url == "pathError":
            with pytest.raises(ASFDownloadError):
                download_url(url, path, filename)

        with patch('asf_search.download.os.path.isdir') as path_mock:
            path_mock.return_value = True

            if url == "urlError":
                with patch('asf_search.download.os.path.isfile') as isfile_mock:
                    isfile_mock.return_value = False

                    with pytest.raises(ASFAuthenticationError):
                        download_url(url, path, filename)

            with patch('asf_search.download.os.path.isfile') as isfile_mock:
                isfile_mock.return_value = True
        
                with pytest.warns(Warning):
                    download_url(url, path, filename)

def run_test_download_url(url, path, filename):
    if filename == 'BURST':
        with patch('asf_search.ASFSession.get') as mock_get:
            resp = requests.Response()
            resp.status_code = 202
            resp.headers.update({'content-type': 'application/json'})
            mock_get.return_value = resp 

            with patch('asf_search.ASFSession.get') as mock_get_burst:
                resp_2 = requests.Response()
                resp_2.status_code = 200
                resp_2.headers.update({'content-type': 'image/tiff'})
                mock_get_burst.return_value = resp_2
                resp_2.iter_content = lambda chunk_size: []
                    
                with patch('builtins.open', unittest.mock.mock_open()) as m:
                    download_url(url, path, filename)
    else:
        with patch('asf_search.ASFSession.get') as mock_get:
            resp = requests.Response()
            resp.status_code = 200
            mock_get.return_value = resp
            resp.iter_content = lambda chunk_size: []
                
            with patch('builtins.open', unittest.mock.mock_open()) as m:
                download_url(url, path, filename)
