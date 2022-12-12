from asf_search.search.search_generator import *
from asf_search import ASFSearchOptions, ASFSearchResults
from asf_search import INTERNAL

def run_test_search_generator(search_opts: ASFSearchOptions):
    pages_iter = search_generator(opts=search_opts)
    
    page_count = int(search_opts.maxResults / INTERNAL.CMR_PAGE_SIZE)

    page_idx = 0
    
    results = ASFSearchResults([])
    for page in pages_iter:
        results.extend(page)
        results.searchComplete = page.searchComplete
        results.searchOptions = page.searchOptions
        page_idx += 1
        
    assert page_count <= page_idx
    assert len(results) <= search_opts.maxResults
    assert results.searchComplete == True
    
    preprocess_opts(search_opts)

    for key, val in search_opts:
        if key != 'maxResults':
            assert getattr(results.searchOptions, key) == val