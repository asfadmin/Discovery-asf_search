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
