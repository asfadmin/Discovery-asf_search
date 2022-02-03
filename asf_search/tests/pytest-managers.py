from asf_search.exceptions import ASFAuthenticationError, ASFSearch4xxError, ASFSearch5xxError

from ASFProduct.test_ASFProduct import run_test_ASFProduct_Geo_Search, run_test_stack
from ASFSession.test_ASFSession import run_auth_with_creds
from BaselineSearch.test_baseline_search import *
from Search.test_search import run_test_ASFSearchResults, run_test_search, run_test_search_http_error

from pytest import raises
from unittest.mock import patch

# asf_search.ASFProduct Tests
def test_ASFProduct(**args) -> None:
    """
    Tests Basic ASFProduct with mock searchAPI response
    """
    test_info = args["test_info"]
    geographic_response = test_info["products"]
    run_test_ASFProduct_Geo_Search(geographic_response)

def test_ASFProduct_Stack(**args) -> None:
    """
    Tests ASFProduct.stack() with reference and corresponding stack
    Checks for temporalBaseline order, 
    asserting the stack is ordered by the scene's temporalBaseline (in ascending order)
    """
    test_info = args["test_info"]
    reference = test_info["product"]
    stack = test_info["baseline_stack"]
    run_test_stack(reference, stack)
    
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

# asf_search.search.baseline_search Tests
def test_get_preprocessed_stack_params(**args) -> None:
    """
    Test asf_search.search.baseline_search.get_stack_params with a reference scene
    that's part of a pre-calculated platform, asserting that get_stack_params returns an object with two parameters
    \n1. processingLevel
    \n2. insarStackId
    """
    test_info = args["test_info"]
    reference = test_info["product"]

    run_test_get_preprocessed_stack_params(reference)

def test_get_unprocessed_stack_params(**args) -> None:
    """
    Test asf_search.search.baseline_search.get_stack_params with a reference scene
    that's not part of a pre-calculated platform, asserting that get_stack_params returns an object with seven parameters
    """
    test_info = args["test_info"]
    reference = test_info["product"]

    run_test_get_unprocessed_stack_params(reference)

def test_get_stack_params_invalid_insarStackId(**args) -> None:
    """
    Test asf_search.search.baseline_search.get_stack_params with a the reference scene's 
    insarStackID set to an invalid value, and asserting an ASFBaselineError is raised
    """
    test_info = args["test_info"]
    reference = test_info["product"]
    
    run_get_stack_params_invalid_insarStackId(reference)
    
def test_get_stack_params_invalid_platform(**args) -> None:
    """
    Test asf_search.search.baseline_search.get_stack_params with a the reference scene's 
    platform set to an invalid value, and asserting an ASFBaselineError is raised
    """
    test_info = args["test_info"]
    reference = test_info["product"]    
    run_test_get_stack_params_invalid_platform_raises_error(reference)
    
def test_temporal_baseline(**args) -> None:
    """
    Test asf_search.search.baseline_search.calc_temporal_baselines, asserting mutated baseline stack
    is still the same length and that each product's properties contain a temporalBaseline key 
    """
    test_info = args["test_info"]
    reference = test_info["product"]
    stack = test_info["stack"]
    run_test_calc_temporal_baselines(reference, stack)
    
def test_stack_from_product(**args) -> None:
    """
    Test asf_search.search.baseline_search.stack_from_product, asserting stack returned is ordered
    by temporalBaseline value in ascending order
    """
    test_info = args["test_info"]
    reference = test_info["product"]
    stack = test_info["stack"]
    
    run_test_stack_from_product(reference, stack)

def test_stack_from_id(**args) -> None:
    """
    Test asf_search.search.baseline_search.stack_from_id, asserting stack returned is ordered
    by temporalBaseline value in ascending order
    """
    test_info = args["test_info"]
    stack_id = test_info["stack_id"]
    stack_reference = test_info["stack_reference"]
    stack = test_info["stack"]

    run_test_stack_from_id(stack_id, stack_reference, stack)

# asf_search.ASFSearchResults Tests
def test_ASFSearchResults(**args) -> None:
    """
    Test asf_search.ASFSearchResults, asserting initialized values, 
    and geojson response returns object with type FeatureCollection
    """
    test_info = args["test_info"]
    search_response = test_info["response"]

    run_test_ASFSearchResults(search_response)

# asf_search.search Tests
def test_ASFSearch_Search(**args) -> None:
    """
    Test asf_search.search, asserting returned value is expected result
    """
    test_info = args["test_info"]
    parameters = test_info["parameters"]
    answer = test_info["answer"]

    run_test_search(parameters, answer)
    
def test_ASFSearch_Search_Error(**args) -> None:
    """
    Test asf_search.search errors,
    asserting server and client errors are raised
    """
    test_info = args["test_info"]
    parameters = test_info["parameters"]
    report = test_info["report"]
    error_code = test_info["status_code"]
    if error_code == 400:
        with raises(ASFSearch4xxError):
            run_test_search_http_error(parameters, error_code, report)
    if error_code == 500:
        with raises(ASFSearch5xxError):
            run_test_search_http_error(parameters, error_code, report)
