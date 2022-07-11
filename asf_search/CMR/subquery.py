from typing import List
import itertools
from copy import copy

from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.constants import CMR_PAGE_SIZE


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

    list_param_names = ['platform', 'season']  # these parameters will dodge the subquery system
    skip_param_names = ['maxResults']# these params exist in opts, but shouldn't be passed on to subqueries at ALL
    
    params = dict([ (k, v) for k, v in params.items() if k not in skip_param_names ])

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
