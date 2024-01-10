from typing import List
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

    list_param_names = ['platform', 'season', 'collections', 'dataset', 'processingLevel_collections']  # these parameters will dodge the subquery system
    skip_param_names = ['maxResults']# these params exist in opts, but shouldn't be passed on to subqueries at ALL
    
    params = dict([ (k, v) for k, v in params.items() if k not in skip_param_names ])

    # in case all instances of platform and/or processingLevel can be substituded by a concept id
    keyword_collection_aliases = []
    if 'processingLevel' in params.keys():
        concept_id_aliases = []
        for processingLevel in params['processingLevel']:
            if alias := collections_by_processing_level.get(processingLevel):
                concept_id_aliases.extend(alias)
            else:
                concept_id_aliases = []
                break
            
        if len(concept_id_aliases):
            params.pop('processingLevel')
            params['processingLevel_collections'] = concept_id_aliases

    if 'dataset' in params:
        if 'collections' not in params:
            params['collections'] = []
        
        for dataset in params.pop('dataset'):
            if collections_by_short_name := dataset_collections.get(dataset):
                for concept_ids in collections_by_short_name.values():
                    params['collections'].extend(concept_ids)
            else:
                raise ValueError(f'Could not find dataset named "{dataset}" provided for dataset keyword.')

        if (processingLevel_collections := params.get('processingLevel_collections')) is not None:
            if len(processingLevel_collections):
                params['collections'] = list(intersect1d(processingLevel_collections, params['collections']))
            
            params.pop('processingLevel_collections')

        
    elif 'platform' in params:
        if 'collections' not in params:
            params['collections'] = []
        
        missing = [platform for platform in params['platform'] if collections_per_platform.get(platform.upper()) is None]
        
        # collections limit platform searches, so if there are any we don't have collections for we skip this optimization
        if len(missing) == 0:
            for platform in params['platform']:
                if (collections := collections_per_platform.get(platform.upper())):
                    params['collections'].extend(collections)
            
            if (processingLevel_collections := params.get('processingLevel_collections')) is not None:
                if len(processingLevel_collections):
                    params['collections'] = list(intersect1d(processingLevel_collections, params['collections']))
               
                params.pop('processingLevel_collections')

            params.pop('platform')
    else:
        if params.get('collections') is None:
            params['collections'] = []
            if params.get('processingLevel_collections') is not None:
                params['collections'] = params.get('processingLevel_collections')
        else:
            if (processingLevel_collections := params.get('processingLevel_collections')) is not None:
                params['collections'] = list(intersect1d(processingLevel_collections, params['collections']))
    
    if params.get('processingLevel_collections') is not None:
        params.pop('processingLevel_collections')
    
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
