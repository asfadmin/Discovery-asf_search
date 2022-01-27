from urllib.error import HTTPError
from urllib.request import HTTPErrorProcessor
from asf_search.constants import INTERNAL
from asf_search.exceptions import ASFSearch4xxError, ASFSearch5xxError, ASFServerError
from ..search import search
from .fixtures.search_fixtures import *

from asf_search.ASFSearchResults import ASFSearchResults

from unittest.mock import Mock, patch
import requests
import requests_mock

class Test_Search:
    def test_ASFSearchResults(self, alos_search_results):
        search_results = ASFSearchResults(alos_search_results)
    
        assert(len(search_results) == 5)    
    
        for (idx, feature) in enumerate(search_results.data):
            assert(feature == alos_search_results[idx])
    
    def test_search_empty(self, empty_search_parameters, requests_mock):
        requests_mock.post(f"https://{empty_search_parameters['host']}{INTERNAL.SEARCH_PATH}", json={'features': []})
        assert(len(search(**empty_search_parameters)) == 0)
    
    
    def test_search_4xx_client_error(self, empty_search_parameters, requests_mock):
        requests_mock.register_uri('POST', f"https://{empty_search_parameters['host']}{INTERNAL.SEARCH_PATH}", status_code=400, json={'error': {'report': "Client Error"}})

        with pytest.raises(ASFSearch4xxError):
            search(**empty_search_parameters)
    
    def test_search_http_5xx_server_error(self, empty_search_parameters, requests_mock):
        requests_mock.register_uri('POST', f"https://{empty_search_parameters['host']}{INTERNAL.SEARCH_PATH}", status_code=500, json={'error': {'report': "Server Error"}})

        with pytest.raises(ASFSearch5xxError):
            search(**empty_search_parameters)

    # def test_search_http_ASF_server_error(self, empty_search_parameters, requests_mock):
    #     requests_mock.register_uri('POST', f"https://{empty_search_parameters['host']}{INTERNAL.SEARCH_PATH}", status_code=200, json={'error': {'report': "ASF Server Error"}})

    #     with pytest.raises(ASFServerError):
    #         search(**empty_search_parameters)