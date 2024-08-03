from numbers import Number
from asf_search import ASFProduct, ASFSearchOptions
from asf_search import ASFSession
# from asf_search.CMR.translate import get

from tenacity import retry, retry_if_exception_type, stop_after_attempt
from asf_search import ASF_LOGGER
from asf_search.CMR.subquery import build_subqueries
from asf_search.CMR.translate import try_parse_date
from asf_search.constants import INTERNAL
from asf_search.exceptions import ASFSearchError
from asf_search.search import search
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.CMR import dataset_collections
from pytest import raises
from typing import List
import requests
import requests_mock

from asf_search.search.search_generator import as_ASFProduct, preprocess_opts

SEARCHAPI_URL = 'https://api.daac.asf.alaska.edu'
SEARCHAPI_ENDPOINT = '/services/search/param?'


def run_test_ASFSearchResults(search_resp):
    search_results = ASFSearchResults(
        [as_ASFProduct(product, ASFSession()) for product in search_resp]
    )

    assert len(search_results) == len(search_resp)
    assert search_results.geojson()['type'] == 'FeatureCollection'

    for idx, feature in enumerate(search_results):
        # temporal and perpendicular baseline values are calculated post-search,
        # so there's no instance where they'll be returned in a CMR search
        search_resp[idx]['properties'].pop('temporalBaseline', None)
        search_resp[idx]['properties'].pop('perpendicularBaseline', None)

        assert feature.geojson()['geometry'] == search_resp[idx]['geometry']
        for key, item in feature.geojson()['properties'].items():
            if key == 'esaFrame':
                assert search_resp[idx]['properties']['frameNumber'] == item
            elif 'esaFrame' in feature.geojson()['properties'].keys() and key == 'frameNumber':
                continue
            elif key in ['stopTime', 'startTime', 'processingDate']:
                assert try_parse_date(item) == try_parse_date(search_resp[idx]['properties'][key])
            elif search_resp[idx]['properties'].get(key) is not None and item is not None:
                assert item == search_resp[idx]['properties'][key]


def run_test_search(search_parameters, answer):
    with requests_mock.Mocker() as m:
        m.post(
            f'https://{INTERNAL.CMR_HOST}{INTERNAL.CMR_GRANULE_PATH}',
            json={'items': answer, 'hits': len(answer)},
        )
        response = search(**search_parameters)

        if search_parameters.get('maxResults', False):
            assert len(response) == search_parameters['maxResults']

        assert len(response) == len(answer)
        # assert(response.geojson()["features"] == answer)


def run_test_search_http_error(search_parameters, status_code: Number, report: str):
    if not len(search_parameters.keys()):
        with requests_mock.Mocker() as m:
            m.register_uri(
                'POST',
                f'https://{INTERNAL.CMR_HOST}{INTERNAL.CMR_GRANULE_PATH}',
                status_code=status_code,
                json={'errors': {'report': report}},
            )
            m.register_uri('POST', 'https://search-error-report.asf.alaska.edu/', real_http=True)
            searchOptions = ASFSearchOptions(**search_parameters)
            with raises(ASFSearchError):
                search(opts=searchOptions)
            return

    # If we're not doing an empty search we want to fire off one real query to CMR, then interrupt it with an error
    # We can tell a search isn't the first one by checking if 'CMR-Search-After' has been set
    def custom_matcher(request: requests.Request):
        if 'CMR-Search-After' in request.headers.keys():
            resp = requests.Response()
            resp.status_code = 200
            return resp
        return None

    with requests_mock.Mocker() as m:
        m.register_uri(
            'POST',
            f'https://{INTERNAL.CMR_HOST}{INTERNAL.CMR_GRANULE_PATH}',
            real_http=True,
        )
        m.register_uri(
            'POST',
            f'https://{INTERNAL.CMR_HOST}{INTERNAL.CMR_GRANULE_PATH}',
            additional_matcher=custom_matcher,
            status_code=status_code,
            json={'errors': {'report': report}},
        )
        m.register_uri('POST', 'https://search-error-report.asf.alaska.edu/', real_http=True)

        search_parameters['maxResults'] = INTERNAL.CMR_PAGE_SIZE + 1
        searchOptions = ASFSearchOptions(**search_parameters)

        with raises(ASFSearchError):
            search(opts=searchOptions)


def run_test_dataset_search(datasets: List):
    if any(dataset for dataset in datasets if dataset_collections.get(dataset) is None):
        with raises(ValueError):
            search(dataset=datasets, maxResults=1)
    else:
        for dataset in datasets:
            valid_shortnames = list(dataset_collections.get(dataset))

            response = search(dataset=dataset, maxResults=250)

            # Get collection shortName of all granules
            shortNames = list(
                set(
                    [
                        shortName
                        for product in response
                        if (
                            shortName := ASFProduct.umm_get(
                                product.umm, 'CollectionReference', 'ShortName'
                            )
                        )
                        is not None
                    ]
                )
            )

            # and check that results are limited to the expected datasets by their shortname
            for shortName in shortNames:
                assert shortName in valid_shortnames


def run_test_build_subqueries(params: ASFSearchOptions, expected: List):
    # mainly for getting platform aliases
    preprocess_opts(params)
    actual = build_subqueries(params)
    for a, b in zip(actual, expected):
        for key, actual_val in a:
            expected_val = getattr(b, key)
            if isinstance(actual_val, list):
                if key == 'cmr_keywords':
                    for idx, key_value_pair in enumerate(actual_val):
                        assert key_value_pair == expected_val[idx]
                else:
                    if len(actual_val) > 0:  # ASFSearchOptions leaves empty lists as None
                        expected_set = set(expected_val)
                        actual_set = set(actual_val)

                        difference = expected_set.symmetric_difference(actual_set)
                        assert (
                            len(difference) == 0
                        ), f'Found {len(difference)} missing entries for subquery generated keyword: "{key}"\n{list(difference)}'
            else:
                assert actual_val == expected_val


def run_test_keyword_aliasing_results(params: ASFSearchOptions):
    module_response = search(opts=params)

    try:
        api_response = query_endpoint(dict(params))
    except requests.ReadTimeout:
        ASF_LOGGER.warn(f'SearchAPI timed out, skipping test for params {str(params)}')
        return

    api_results = api_response['results']

    api_dict = {product['granuleName']: True for product in api_results}

    for product in module_response:
        sceneName = product.properties['sceneName']
        assert api_dict.get(
            sceneName, False
        ), f'Found unexpected scene in asf-search module results, {sceneName}\{dict(params)}'


@retry(
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(requests.HTTPError),
    reraise=True,
)
def query_endpoint(params):
    response = requests.post(
        url=SEARCHAPI_URL + SEARCHAPI_ENDPOINT, data={**params, 'output': 'jsonlite'}
    )
    response.raise_for_status()

    return response.json()
