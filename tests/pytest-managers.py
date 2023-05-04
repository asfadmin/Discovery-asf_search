from typing import Dict, List
from asf_search import ASFSearchOptions, ASFProduct
from asf_search.exceptions import ASFAuthenticationError

from ASFProduct.test_ASFProduct import run_test_ASFProduct, run_test_product_get_stack_options, run_test_stack
from ASFSearchOptions.test_ASFSearchOptions import run_test_ASFSearchOptions
from ASFSearchResults.test_ASFSearchResults import run_test_output_format, run_test_ASFSearchResults_intersection
from ASFSession.test_ASFSession import run_auth_with_cookiejar, run_auth_with_creds, run_auth_with_token, run_test_asf_session_rebuild_auth
from BaselineSearch.test_baseline_search import *
from Search.test_search import run_test_ASFSearchResults, run_test_search, run_test_search_http_error
from Search.test_search_generator import run_test_search_generator, run_test_search_generator_multi
from CMR.test_MissionList import run_test_get_project_names


from pytest import raises
from unittest.mock import patch

import os
import pathlib
import yaml

from WKT.test_validate_wkt import run_test_search_wkt_prep, run_test_validate_wkt_get_shape_coords, run_test_validate_wkt_clamp_geometry, run_test_validate_wkt_valid_wkt, run_test_validate_wkt_convex_hull, run_test_validate_wkt_counter_clockwise_reorientation, run_test_validate_wkt_invalid_wkt_error, run_test_validate_wkt_merge_overlapping_geometry, run_test_simplify_aoi
from ASFSearchOptions.test_ASFSearchOptions import run_test_ASFSearchOptions_validator, run_test_validator_map_validate
from BaselineSearch.Stack.test_stack import run_test_find_new_reference, run_test_get_baseline_from_stack, run_test_get_default_product_type, run_test_valid_state_vectors

from download.test_download import run_test_download_url, run_test_download_url_auth_error
from Serialization.test_serialization import run_test_serialization
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


# asf_search.ASFProduct Tests
def test_ASFProduct(**args) -> None:
    """
    Tests Basic ASFProduct with mock searchAPI response
    """
    test_info = args["test_info"]
    geographic_response = get_resource(test_info["products"])
    run_test_ASFProduct(geographic_response)

def test_ASFProduct_Stack(**args) -> None:
    """
    Tests ASFProduct.stack() with reference and corresponding stack
    Checks for temporalBaseline order, 
    asserting the stack is ordered by the scene's temporalBaseline (in ascending order)
    """
    test_info = args["test_info"]
    reference = get_resource(test_info["product"])
    preprocessed_stack = get_resource(test_info["preprocessed_stack"])
    processed_stack = get_resource(test_info["processed_stack"])
    run_test_stack(reference, preprocessed_stack, processed_stack)

def test_ASFProduct_get_stack_options(**args) -> None:
    test_info = args["test_info"]
    reference = get_resource(test_info['product'])
    options = get_resource(test_info['options'])

    run_test_product_get_stack_options(reference, options)
 
# asf_search.ASFSession Tests
def test_ASFSession_Error(**args) -> None:
    """
    Test ASFSession.auth_with_creds for sign in errors
    """
    test_info = args["test_info"]
    username = test_info["username"]
    password = test_info["password"]
    with patch('asf_search.ASFSession.get') as mock_get:
        mock_get.return_value = "Error"

        with raises(ASFAuthenticationError):
            run_auth_with_creds(username, password)

def test_ASFSession_Token_Error(**args) -> None:
    """
    Test ASFSession.auth_with_token for sign in errors
    """
    test_info = args["test_info"]
    token = test_info["token"]

    with raises(ASFAuthenticationError):
        run_auth_with_token(token)

def test_ASFSession_Cookie_Error(**args) -> None:
    """
    Test ASFSession.auth_with_cookie for sign in errors
    """
    test_info = args["test_info"]
    cookies = test_info["cookies"]

    with raises(ASFAuthenticationError):
        run_auth_with_cookiejar(cookies)

def test_asf_session_rebuild_auth(**args) -> None:
    """
    Test asf_search.ASFSession.rebuild_auth
    When redirecting from an ASF domain, only accept 
    domains listed in ASFSession.AUTH_DOMAINS
    """
    test_info = args["test_info"]
    original_domain = test_info["original_domain"]
    response_domain = test_info["response_domain"]
    response_code = test_info["response_code"]
    final_token = test_info["final_token"]

    run_test_asf_session_rebuild_auth(original_domain, response_domain, response_code, final_token)

# asf_search.search.baseline_search Tests
def test_get_preprocessed_stack_params(**args) -> None:
    """
    Test asf_search.search.baseline_search.get_stack_opts with a reference scene
    that's part of a pre-calculated platform, asserting that get_stack_opts returns an object with two parameters
    \n1. processingLevel
    \n2. insarStackId
    """
    test_info = args["test_info"]
    reference = get_resource(test_info["product"])

    run_test_get_preprocessed_stack_params(reference)

def test_get_unprocessed_stack_params(**args) -> None:
    """
    Test asf_search.search.baseline_search.get_stack_opts with a reference scene
    that's not part of a pre-calculated platform, asserting that get_stack_opts returns an object with seven parameters
    """
    test_info = args["test_info"]
    reference = get_resource(test_info["product"])

    run_test_get_unprocessed_stack_params(reference)

def test_get_stack_opts_invalid_insarStackId(**args) -> None:
    """
    Test asf_search.search.baseline_search.get_stack_opts with a the reference scene's 
    insarStackID set to an invalid value, and asserting an ASFBaselineError is raised
    """
    test_info = args["test_info"]
    reference = get_resource(test_info["product"])
    
    run_get_stack_opts_invalid_insarStackId(reference)
    
def test_get_stack_opts_invalid_platform(**args) -> None:
    """
    Test asf_search.search.baseline_search.get_stack_opts with a the reference scene's 
    platform set to an invalid value, and asserting an ASFBaselineError is raised
    """
    test_info = args["test_info"]
    reference = get_resource(test_info["product"])    
    run_test_get_stack_opts_invalid_platform_raises_error(reference)
    
def test_temporal_baseline(**args) -> None:
    """
    Test asf_search.search.baseline_search.calc_temporal_baselines, asserting mutated baseline stack
    is still the same length and that each product's properties contain a temporalBaseline key 
    """
    test_info = args["test_info"]
    reference = get_resource(test_info["product"])
    stack = get_resource(test_info["stack"])
    run_test_calc_temporal_baselines(reference, stack)
    
def test_stack_from_product(**args) -> None:
    """
    Test asf_search.search.baseline_search.stack_from_product, asserting stack returned is ordered
    by temporalBaseline value in ascending order
    """
    test_info = args["test_info"]
    reference = get_resource(test_info["product"])
    stack = get_resource(test_info["stack"])
    
    run_test_stack_from_product(reference, stack)

def test_stack_from_id(**args) -> None:
    """
    Test asf_search.search.baseline_search.stack_from_id, asserting stack returned is ordered
    by temporalBaseline value in ascending order
    """
    test_info = args["test_info"]
    stack_id = test_info["stack_id"]
    stack_reference_data = test_info["stack_reference"]
    stack_data = test_info["stack"]

    stack_reference = get_resource(stack_reference_data)
    stack = []

    if(stack_data != []):
        stack = get_resource(stack_data)

    run_test_stack_from_id(stack_id, stack_reference, stack)

# asf_search.ASFSearchResults Tests
def test_ASFSearchResults(**args) -> None:
    """
    Test asf_search.ASFSearchResults, asserting initialized values, 
    and geojson response returns object with type FeatureCollection
    """
    test_info = args["test_info"]
    search_response = get_resource(test_info["response"])

    run_test_ASFSearchResults(search_response)

# asf_search.search Tests
def test_ASFSearch_Search(**args) -> None:
    """
    Test asf_search.search, asserting returned value is expected result
    """
    test_info = args["test_info"]
    parameters = get_resource(test_info["parameters"])
    answer = get_resource(test_info["answer"])

    run_test_search(parameters, answer)

def test_ASFSearch_Search_Generator(**args) -> None:
    test_info = args["test_info"]
    params = get_resource(test_info['parameters'])

    if isinstance(params, list):
        opts = []
        for p in params:
            opts.append(ASFSearchOptions(**p))

        run_test_search_generator_multi(opts)

    else:
        run_test_search_generator(ASFSearchOptions(**params))


def test_ASFSearch_Search_Error(**args) -> None:
    """
    Test asf_search.search errors,
    asserting server and client errors are raised
    """
    test_info = args["test_info"]
    parameters = test_info["parameters"]
    report = test_info["report"]
    error_code = test_info["status_code"]

    run_test_search_http_error(parameters, error_code, report)

def test_wkt_validation_Invalid_WKT_Error(**args) -> None:
    """
    Test asf_search.wkt errors,
    asserting wkt validation errors are raised
    """
    test_info = args["test_info"]
    wkt = get_resource(test_info['wkt'])
    run_test_validate_wkt_invalid_wkt_error(wkt)

def test_wkt_validation_WKT_Valid(**args) -> None:
    """
    Test asf_search.validate_wkt, asserting expected wkts are returned
    """
    test_info = args["test_info"]
    wkt = get_resource(test_info['wkt'])
    validated_wkt = get_resource(test_info['validated-wkt'])
    run_test_validate_wkt_valid_wkt(wkt, validated_wkt)

def test_wkt_validation_WKT_clamp_geometry(**args) -> None:
    """
    Test asf_search.validate_wkt._get_clamped_and_wrapped_geometry, asserting the amount of clamped and wrapped coordinates
    """
    test_info = args["test_info"]
    wkt = get_resource(test_info['wkt'])
    clamped_wkt = get_resource(test_info['clamped-wkt'])
    clamped_count = get_resource(test_info['clamped-count'])
    wrapped_count = get_resource(test_info['wrapped-count'])
    run_test_validate_wkt_clamp_geometry(wkt, clamped_wkt, clamped_count, wrapped_count)

def test_wkt_validation_convex_hull(**args) -> None:
    """
    Test asf_search.validate_wkt._get_convex_hull, asserting convex hulls producted are expected
    """
    test_info = args["test_info"]
    wkt = get_resource(test_info['wkt'])
    convex_wkt = get_resource(test_info['convex-wkt'])
    run_test_validate_wkt_convex_hull(wkt, convex_wkt)

def test_wkt_validation_merge_overlapping_geometry(**args) -> None:
    """
    Test asf_search.validate_wkt._merge_overlapping_geometry, asserting expected shapes are merged
    """
    test_info = args["test_info"]
    wkt = get_resource(test_info['wkt'])
    merged_wkt = get_resource(test_info['merged-wkt'])
    run_test_validate_wkt_merge_overlapping_geometry(wkt, merged_wkt)

def test_wkt_validation_counter_clockwise_reorientation(**args) -> None:
    """
    Test asf_search.validate_wkt._counter_clockwise_reorientation reverses polygon orientation if polygon is wound clockwise,
    and maintains counter-clockwise winding when polygon orientation is correct
    """
    test_info = args["test_info"]
    wkt = get_resource(test_info['wkt'])
    cc_wkt = get_resource(test_info['cc-wkt'])
    run_test_validate_wkt_counter_clockwise_reorientation(wkt, cc_wkt)

def test_validate_wkt_get_shape_coords(**args) -> None:
    """
    Test asf_search.validate_wkt._get_shape_coords asserting all coordinates are returned and expected
    """
    test_info = args["test_info"]
    wkt = get_resource(test_info['wkt'])
    coords = get_resource(test_info['coordinates'])
    run_test_validate_wkt_get_shape_coords(wkt, coords)

def test_search_wkt_prep(**args) -> None:
    """
    Test asf_search.validate_wkt.wkt_prep, asserting returned shape is correct geometric type and expected shape
    """
    test_info = args["test_info"]
    wkt = get_resource(test_info['wkt'])
    
    run_test_search_wkt_prep(wkt)

def test_simplify_aoi(**args) -> None:
    """
    Test asf_search.validate_wkt.wkt_prep, asserting returned shape is correct geometric type and expected shape
    """
    test_info = args["test_info"]
    wkt = get_resource(test_info['wkt'])
    simplified = get_resource(test_info["simplified-wkt"])
    RepairEntries = get_resource(test_info["RepairEntries"])
    run_test_simplify_aoi(wkt, simplified, RepairEntries)

def test_get_platform_campaign_names(**args) -> None:
    test_info = args["test_info"]
    cmr_ummjson = get_resource(test_info["cmr_ummjson"])
    campaigns: List[str] = get_resource(test_info["campaigns"])
    
    run_test_get_project_names(cmr_ummjson, campaigns)

def test_download_url(**args) -> None:
    """
    Test asf_search.download.download_url
    """
    test_info = args["test_info"]
    url = test_info["url"]
    path = test_info["path"]
    filename = test_info["filename"]
        
    if filename == "error":
        run_test_download_url_auth_error(url, path, filename)
    else:
        run_test_download_url(url, path, filename)
        
def test_find_new_reference(**args) -> None:
    """
    Test asf_search.baseline.calc.find_new_reference
    """
    test_info = args["test_info"]
    stack = get_resource(test_info["stack"])
    output_index = get_resource(test_info["output_index"])
    
    run_test_find_new_reference(stack, output_index)

def test_get_default_product_type(**args) -> None:
    test_info = args["test_info"]
    product = get_resource(test_info["product"])
    product_type = get_resource(test_info["product_type"])
    
    product = ASFProduct(args={'meta': product['meta'], 'umm': product['umm']})
    if product.properties.get('sceneName') is None:
        product.properties['sceneName'] = 'BAD_SCENE'
        
    run_test_get_default_product_type(product, product_type)

def test_get_baseline_from_stack(**args) -> None:
    test_info = args["test_info"]
    reference = get_resource(test_info['reference'])
    stack = get_resource(test_info['stack'])
    output_stack = get_resource(test_info['output_stack'])
    error = get_resource(test_info['error'])
    run_test_get_baseline_from_stack(reference, stack, output_stack, error)

def test_valid_state_vectors(**args) -> None:
    test_info = args["test_info"]
    reference = get_resource(test_info['reference'])
    output = get_resource(test_info['output'])
    
    run_test_valid_state_vectors(reference, output)
    
def test_validator_map_validate(**args) -> None:
    test_info = args["test_info"]
    key = get_resource(test_info['key'])
    value = get_resource(test_info['value'])
    output = get_resource(test_info['output'])

    run_test_validator_map_validate(key, value, output)

def test_ASFSearchOptions_validator(**args) -> None:
    test_info = args["test_info"]
    validator_name = get_resource(test_info['validator'])
    param = safe_load_tuple(get_resource(test_info['input']))
    output = safe_load_tuple(get_resource(test_info['output']))
    error = get_resource(test_info['error'])
    run_test_ASFSearchOptions_validator(validator_name, param, output, error)
    

def test_ASFSearchOptions(**kwargs) -> None:
    run_test_ASFSearchOptions(**kwargs)

def test_ASFSearchResults_intersection(**kwargs) -> None:
    wkt = get_resource(kwargs['test_info']['wkt'])
    run_test_ASFSearchResults_intersection(wkt)

def test_serialization(**args) -> None:
    test_info = args['test_info']
    product = get_resource(test_info.get('product'))
    results = get_resource(test_info.get('results'))
    search_opts = get_resource(test_info.get('searchOpts'))
    options = ASFSearchOptions(**search_opts if search_opts else {})

    run_test_serialization(product, results, options)

def test_notebook_examples(**args) -> None:
    test_info = args['test_info']
    notebook_file = test_info['notebook']
    path = os.path.join('examples', notebook_file)

    with open(path) as f:
        notebook = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor(timeout=600)
        try:
            assert ep.preprocess(notebook) != None, f"Got empty notebook for {notebook_file}"
        except Exception as e:
            assert False, f"Failed executing {notebook_file}: {e}"


# Testing resource loading utilities

def safe_load_tuple(param):
    """
    loads a tuple from a list if a param is an object with key 'tuple'
    (Arbritrary constructor initialization is not supported by yaml.safe_load
    as a security measure)
    
    """
    if isinstance(param, Dict):
        if "tuple" in param.keys():
            param = tuple(param['tuple'])
    
    return param

def test_output_format(**args) -> None:
    test_info = args['test_info']
    
    products = get_resource(test_info['results'])
    if not isinstance(products, List):
        products = [products]
    results = ASFSearchResults([ASFProduct(args={'meta': product['meta'], 'umm': product['umm']}) for product in products])

    run_test_output_format(results)

# Finds and loads file from yml_tests/Resouces/ if loaded field ends with .yml/yaml extension
def get_resource(yml_file):
    
    if isinstance(yml_file, str):
        if yml_file.endswith((".yml", ".yaml")):
            base_path = pathlib.Path(__file__).parent.resolve()
            with open(os.path.join(base_path, "yml_tests", "Resources", yml_file), "r") as f:
                try:
                    return yaml.safe_load(f)
                except yaml.YAMLError as exc:
                    print(exc)
    elif isinstance(yml_file, List): #check if it's a list of yml files
        if len(yml_file) > 0:
            if isinstance(yml_file[0], str):
                if yml_file[0].endswith((".yml", ".yaml")):
                    return [get_resource(file) for file in yml_file]

    return yml_file
