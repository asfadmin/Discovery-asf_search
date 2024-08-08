from typing import List, Tuple
import itertools
from copy import copy

from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.constants import CMR_PAGE_SIZE
from asf_search.CMR.datasets import (
    collections_by_processing_level,
    collections_per_platform,
    get_concept_id_alias,
    get_dataset_concept_ids,
)
from numpy import intersect1d, union1d


def build_subqueries(opts: ASFSearchOptions) -> List[ASFSearchOptions]:
    """
    Build a list of sub-queries using the cartesian product
    of all the list parameters described by opts

    :param opts: The search options to split into sub-queries
    :return list: A list of ASFSearchOptions objects
    """
    params = dict(opts)

    # Break out two big list offenders into manageable chunks
    for chunked_key in ['granule_list', 'product_list']:
        if params.get(chunked_key) is not None:
            params[chunked_key] = chunk_list(params[chunked_key], CMR_PAGE_SIZE)

    list_param_names = [
        'platform',
        'season',
        'collections',
        'dataset',
        'cmr_keywords',
        'shortName',
        'circle',
        'linestring',
        'point',
    ]  # these parameters will dodge the subquery system
    skip_param_names = [
        'maxResults',
    ]  # these params exist in opts, but shouldn't be passed on to subqueries at ALL

    collections, aliased_keywords = get_keyword_concept_ids(params, opts.collectionAlias)
    params['collections'] = list(union1d(collections, params.get('collections', [])))

    for keyword in [*skip_param_names, *aliased_keywords]:
        params.pop(keyword, None)

    subquery_params, list_params = {}, {}
    for key, value in params.items():
        if key in list_param_names:
            list_params[key] = value
        else:
            subquery_params[key] = value

    sub_queries = cartesian_product(subquery_params)
    return [_build_subquery(query, opts, list_params) for query in sub_queries]


def _build_subquery(
    query: List[Tuple[dict]], opts: ASFSearchOptions, list_params: dict
) -> ASFSearchOptions:
    """
    Composes query dict and list params into new ASFSearchOptions object

    param: query: the cartesian search query options
    param: opts: the search options to pull config options from (provider, host, session)
    param: list_params: the subquery parameters
    """
    q = dict()
    for p in query:
        q.update(p)

    q['provider'] = opts.provider
    q['host'] = opts.host
    q['session'] = copy(opts.session)

    return ASFSearchOptions(**q, **list_params)


def get_keyword_concept_ids(params: dict, use_collection_alias: bool = True) -> dict:
    """
    Gets concept-ids for dataset, platform, processingLevel keywords
    processingLevel is scoped by dataset or platform concept-ids when available

    : param params:
        search parameter dictionary pre-CMR translation
    : param use_collection_alias:
        whether or not to alias platform and processingLevel with concept-ids
    : returns two lists:
        - list of concept-ids for dataset, platform, and processingLevel
        - list of aliased keywords to remove from final parameters
    """
    collections = []
    aliased_keywords = []

    if use_collection_alias:
        if 'processingLevel' in params.keys():
            collections = get_concept_id_alias(
                params.get('processingLevel'), collections_by_processing_level
            )
            if len(collections):
                aliased_keywords.append('processingLevel')

        if 'platform' in params.keys():
            platform_concept_ids = get_concept_id_alias(
                [platform.upper() for platform in params.get('platform')],
                collections_per_platform,
            )
            if len(platform_concept_ids):
                aliased_keywords.append('platform')
                collections = _get_intersection(platform_concept_ids, collections)

    if 'dataset' in params.keys():
        aliased_keywords.append('dataset')
        dataset_concept_ids = get_dataset_concept_ids(params.get('dataset'))
        collections = _get_intersection(dataset_concept_ids, collections)

    return collections, aliased_keywords


def _get_intersection(keyword_concept_ids: List[str], intersecting_ids: List[str]) -> List[str]:
    """
    Returns the intersection between two lists. If the second list is empty the first list
    is return unchaged
    """
    if len(intersecting_ids):
        return list(intersect1d(intersecting_ids, keyword_concept_ids))

    return keyword_concept_ids


def chunk_list(source: List, n: int) -> List:
    """
    Breaks a longer list into a list of lists, each of length n

    :param source: The list to be broken into chunks
    :param n: The maximum length of each chunk

    :return List[List, ...]:
    """
    return [source[i * n : (i + 1) * n] for i in range((len(source) + n - 1) // n)]


def cartesian_product(params):
    formatted_params = format_query_params(params)
    p = list(itertools.product(*formatted_params))
    return p


def format_query_params(params) -> List[List[dict]]:
    listed_params = []

    for param_name, param_val in params.items():
        plist = translate_param(param_name, param_val)
        listed_params.append(plist)

    return listed_params


def translate_param(param_name, param_val) -> List[dict]:
    param_list = []

    if not isinstance(param_val, list):
        param_val = [param_val]

    for unformatted_val in param_val:
        formatted_val = unformatted_val

        if isinstance(unformatted_val, list):
            formatted_val = ','.join([f'{t}' for t in unformatted_val])

        param_list.append({param_name: formatted_val})

    return param_list
