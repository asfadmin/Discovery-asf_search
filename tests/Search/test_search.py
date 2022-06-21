from numbers import Number
from asf_search.ASFProduct import ASFProduct
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.constants import INTERNAL
from asf_search.search import search
from asf_search.CMR import translate_opts
from asf_search.ASFSearchResults import ASFSearchResults

import requests_mock

def run_test_ASFSearchResults(search_resp):
    search_results = ASFSearchResults([ASFProduct(product, opts=None) for product in search_resp])

    assert(len(search_results) == len(search_resp))
    assert(search_results.geojson()['type'] == 'FeatureCollection')

    for (idx, feature) in enumerate(search_results.data):
        assert(feature.geojson()['geometry'] == search_resp[idx]['geometry'])
        assert(feature.geojson()['properties'] == search_resp[idx]['properties'])

def run_test_search(search_parameters, answer):
    with requests_mock.Mocker() as m:
        copy_params = search_parameters
        copy_params.pop('maxResults', None)
        translated_opts = translate_opts(ASFSearchOptions(**copy_params))
        m.post(f"https://{INTERNAL.CMR_HOST}{INTERNAL.CMR_GRANULE_PATH}", json={'items': answer})
        response = search(**search_parameters)

        if search_parameters.get("maxResults", False):
            assert(len(response) == search_parameters["maxResults"])

        assert(len(response) == len(answer))
        # assert(response.geojson()["features"] == answer)

def run_test_search_http_error(search_parameters, status_code: Number, report: str):
    with requests_mock.Mocker() as m:
        m.register_uri('POST', f"https://{INTERNAL.CMR_HOST}{INTERNAL.CMR_GRANULE_PATH}", status_code=status_code, json={'errors': {'report': report}})
        
        search(**search_parameters)
