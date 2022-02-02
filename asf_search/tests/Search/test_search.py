from numbers import Number
from asf_search.constants import INTERNAL
from asf_search.search import search

from asf_search.ASFSearchResults import ASFSearchResults

import requests_mock

# class Test_Search:
def run_test_ASFSearchResults(search_resp):
    search_results = ASFSearchResults(search_resp)

    assert(len(search_results) == 5)    

    for (idx, feature) in enumerate(search_results.data):
        assert(feature == search_resp[idx])

def run_test_search(search_parameters):
    with requests_mock.Mocker() as m:
        m.post(f"https://{search_parameters['host']}{INTERNAL.SEARCH_PATH}", json={'features': []})
        assert(len(search(**search_parameters)) == 0)

def run_test_search_http_error(search_parameters, status_code: Number, report: str):
    with requests_mock.Mocker() as m:
        m.register_uri('POST', f"https://{search_parameters['host']}{INTERNAL.SEARCH_PATH}", status_code=status_code, json={'error': {'report': "Server Error"}})
        
        search(**search_parameters)