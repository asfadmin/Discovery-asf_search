from typing import List, Optional
import itertools
from copy import copy

from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.constants import CMR_PAGE_SIZE

from asf_search.CMR.datasets import collections_by_processing_level, collections_per_platform, dataset_collections
from numpy import intersect1d

def build_subqueries(opts: ASFSearchOptions) -> List[ASFSearchOptions]:
    """
    Build a list of sub-queries using the cartesian product of all the list parameters described by opts

    :param opts: The search options to split into sub-queries

    :return list: A list of ASFSearchOptions objects
    """
    params = dict(opts)

    # Break out two big list offenders into manageable chunks
    if params.get('granule_list') is not None:
        params['granule_list'] = chunk_list(params['granule_list'], CMR_PAGE_SIZE)
    if params.get('product_list') is not None:
        params['product_list'] = chunk_list(params['product_list'], CMR_PAGE_SIZE)

    list_param_names = ['platform', 'season', 'collections', 'dataset']  # these parameters will dodge the subquery system
    skip_param_names = ['maxResults']# these params exist in opts, but shouldn't be passed on to subqueries at ALL
    
    params = dict([ (k, v) for k, v in params.items() if k not in skip_param_names ])

    # Gets concept-ids for Dataset, and checks if concept-ids exist for platform, processingLevel
    # processingLevel is scoped by dataset concept-ids, or platform concept-ids when available
    collections, aliased_keywords = get_keyword_concept_ids(params)

    if 'collections' in params.keys():
        params['collections'] = list(set(*collections, *params.get('collections')))
    else:
        params['collections'] = collections
        
    for keyword in aliased_keywords:
        params.pop(keyword)
    
    subquery_params, list_params = {}, {}
    for k, v in params.items():
        if k in list_param_names:
            list_params[k] = v
        else:
            subquery_params[k] = v

    sub_queries = cartesian_product(subquery_params)

    final_sub_query_opts = []
    for query in sub_queries:
        q = dict()
        for p in query:
            q.update(p)
        q['provider'] = opts.provider
        q['host'] = opts.host
        q['session'] = copy(opts.session)
        for key in list_params.keys():
            q[key] = list_params[key]

        final_sub_query_opts.append(ASFSearchOptions(**q))

    return final_sub_query_opts

def get_keyword_concept_ids(params: dict) -> dict:
    """
    Gets concept-ids for dataset, platform, processingLevel keywords
    processingLevel is scoped by dataset or platform concept-ids when available

    : param params: search parameter dictionary pre-CMR translation
    : returns two lists: 
        - list of concept-ids for dataset, platform, and processingLevel
        - list of keywords to remove from parameters
    """
    collections = []
    keywords = []

    processing_level_collections = []
    if 'processingLevel' in params.keys():
        pl_concept_id_aliases = get_processing_level_concept_ids(params.get('processingLevel'))
        if len(pl_concept_id_aliases):
            keywords.append('processingLevel')
            processing_level_collections = pl_concept_id_aliases

    if 'dataset' in params.keys():
        keywords.append('dataset')
        
        collections.extend(get_dataset_concept_ids(params.get('dataset')))

        if len(processing_level_collections):
            collections = list(intersect1d(processing_level_collections, collections))

    elif 'platform' in params.keys():
        platform_concept_ids = get_platform_concept_ids(params.get('platform'))
        if len(platform_concept_ids):
            collections.extend(platform_concept_ids)

            if processing_level_collections is not None:
                if len(processing_level_collections):
                    collections = list(intersect1d(processing_level_collections, collections))
            keywords.append('platform')

    else:
        if len(collections) and processing_level_collections is not None:
            collections = list(intersect1d(processing_level_collections, collections))
        else:
            collections = processing_level_collections
    
    return collections, keywords
    
def get_processing_level_concept_ids(processingLevels: List[str]) -> List[str]:
    concept_id_aliases = []
    for processingLevel in processingLevels:
        if alias := collections_by_processing_level.get(processingLevel):
            concept_id_aliases.extend(alias)
        else:
            break
    
    return []

def get_platform_concept_ids(platforms: List[str]) -> List[str]:
    output = []

    # collections limit platform searches, so if there are any we don't have collections for we skip this optimization
    for platform in platforms:
        if (collections := collections_per_platform.get(platform.upper())):
            output.extend(collections)
        else:
            output = []
            break
    
    return output

def get_dataset_concept_ids(datasets: List[str]) -> List[str]:
    output = []
    for dataset in datasets:
        if collections_by_short_name := dataset_collections.get(dataset):
            for concept_ids in collections_by_short_name.values():
                output.extend(concept_ids)
        else:
            raise ValueError(f'Could not find dataset named "{dataset}" provided for dataset keyword.')
    
    return output

def chunk_list(source: List, n: int) -> List:
    """
    Breaks a longer list into a list of lists, each of length n

    :param source: The list to be broken into chunks
    :param n: The maximum length of each chunk

    :return List[List, ...]:
    """
    return [source[i * n:(i + 1) * n] for i in range((len(source) + n - 1) // n)]


def cartesian_product(params):
    formatted_params = format_query_params(params)
    p = list(itertools.product(*formatted_params))
    return p


def format_query_params(params):
    listed_params = []

    for param_name, param_val in params.items():
        plist = translate_param(param_name, param_val)
        listed_params.append(plist)

    return listed_params


def translate_param(param_name, param_val):
    param_list = []

    if not isinstance(param_val, list):
        param_val = [param_val]

    for unformatted_val in param_val:
        formatted_val = unformatted_val

        if isinstance(unformatted_val, list):
            formatted_val = ','.join([f'{t}' for t in unformatted_val])

        param_list.append({
            param_name: formatted_val
        })

    return param_list
