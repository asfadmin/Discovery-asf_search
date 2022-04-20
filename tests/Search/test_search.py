from numbers import Number
from asf_search.ASFProduct import ASFProduct
from asf_search.constants import INTERNAL
from asf_search.search import search

from asf_search.ASFSearchResults import ASFSearchResults

import requests_mock

def run_test_ASFSearchResults(search_resp):
    search_results = ASFSearchResults(map(ASFProduct, search_resp))

    assert(len(search_results) == len(search_resp))
    assert(search_results.geojson()['type'] == 'FeatureCollection')

    for (idx, feature) in enumerate(search_results.data):
        assert(feature.geojson() == search_resp[idx])

def run_test_search(search_parameters, answer):
    with requests_mock.Mocker() as m:
        m.post(f"https://{search_parameters['host']}{INTERNAL.SEARCH_PATH}", json={'features': answer})
        response = search(**search_parameters)

        if search_parameters["maxResults"] != 'None':
            assert(len(response) == search_parameters["maxResults"])

        assert(len(response) == len(answer))
        assert(response.geojson()["features"] == answer)

def run_test_search_http_error(search_parameters, status_code: Number, report: str):
    with requests_mock.Mocker() as m:
        m.register_uri('POST', f"https://{search_parameters['host']}{INTERNAL.SEARCH_PATH}", status_code=status_code, json={'error': {'report': report}})
        
        search(**search_parameters)
