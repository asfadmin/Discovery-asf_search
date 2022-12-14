from asf_search.search.search_generator import *
from asf_search import ASFSearchOptions, ASFSearchResults
from asf_search import INTERNAL
from typing import List

import math

def run_test_search_generator_multi(search_opts: List[ASFSearchOptions]):
    queries = [search_generator(opts=opts) for opts in search_opts]
    
    expected_results_size = sum([opts.maxResults for opts in search_opts])
    expected_page_count = sum([math.ceil(opts.maxResults / INTERNAL.CMR_PAGE_SIZE) for opts in search_opts])
    combined_results = []
    
    page_count = 0
    searches = {}
    
    for opt in search_opts:
        if isinstance(opt.platform, list):
            for platform in opt.platform:
                searches[platform] = False
        else:
            searches[opt.platform] = False

    while(len(queries)):
        queries_iter = iter(queries)
        for idx, query in enumerate(queries_iter):  # Alternate pages between results
            page = next(query, None)
            if page != None:
                combined_results.extend(page)
                page_count += 1
                if page.searchComplete:
                    if isinstance(page.searchOptions.platform, list):
                        for platform in page.searchOptions.platform:
                            searches[platform] = True
                    else:
                        searches[page.searchOptions.platform] = True
            else:
                queries[idx] = None

        queries = [query for query in queries if query != None]

    assert page_count == expected_page_count
    assert len(combined_results) == expected_results_size
    assert len([completed for completed in searches if completed]) >= len(search_opts)

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