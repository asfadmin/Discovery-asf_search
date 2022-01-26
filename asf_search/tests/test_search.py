from .fixtures.search_fixtures import *

from asf_search.ASFSearchResults import ASFSearchResults


def test_ASFSearchResults(alos_search_results):
    search_results = ASFSearchResults(alos_search_results)

    assert(len(search_results) == 5)    

    for (idx, feature) in enumerate(search_results.data):
        assert(feature == alos_search_results[idx])