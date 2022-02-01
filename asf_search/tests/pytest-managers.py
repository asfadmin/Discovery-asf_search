from asf_search.exceptions import ASFAuthenticationError

# from fixtures import ASFProduct_fixtures
from ASFProduct.test_ASFProduct import run_test_ASFProduct_Geo_Search, run_test_stack
from ASFSession.test_ASFSession import run_auth_with_creds
from BaselineSearch.test_baseline_search import run_get_stack_params_invalid_insarStackId, run_test_calc_temporal_baselines, run_test_get_preprocessed_stack_params, run_test_get_stack_params_invalid_platform_raises_error, run_test_get_unprocessed_stack_params, run_test_stack_from_id, run_test_stack_from_product

from pytest import raises
from unittest.mock import patch

def test_ASFProduct(**args):
    # run_add_test(**args)
    test_info = args["test_info"]
    geographic_response = test_info["products"]
    run_test_ASFProduct_Geo_Search(geographic_response)

def test_ASFProduct_Stack(**args):
    test_info = args["test_info"]
    reference = test_info["product"]
    stack = test_info["baseline_stack"]
    run_test_stack(reference, stack)
    
    
def test_ASFSession_Error(**args):
    test_info = args["test_info"]
    username = test_info["username"]
    password = test_info["password"]
    with patch('asf_search.ASFSession.get') as mock_get:
        mock_get.return_value = "Error"

        with raises(ASFAuthenticationError):
            run_auth_with_creds(username, password)
            
def test_get_preprocessed_stack_params(**args):
    test_info = args["test_info"]
    reference = test_info["product"]

    run_test_get_preprocessed_stack_params(reference)

def test_get_unprocessed_stack_params(**args):
    test_info = args["test_info"]
    reference = test_info["product"]

    run_test_get_unprocessed_stack_params(reference)

def test_get_stack_params_invalid_insarStackId(**args):
    test_info = args["test_info"]
    reference = test_info["product"]
    
    run_get_stack_params_invalid_insarStackId(reference)
    
def test_get_stack_params_invalid_platform(**args):
    test_info = args["test_info"]
    reference = test_info["product"]    
    run_test_get_stack_params_invalid_platform_raises_error(reference)
    
def test_temporal_baseline(**args):
    test_info = args["test_info"]
    reference = test_info["product"]
    stack = test_info["stack"]
    run_test_calc_temporal_baselines(reference, stack)
    
def test_stack_from_product(**args):
    test_info = args["test_info"]
    reference = test_info["product"]
    stack = test_info["stack"]
    
    run_test_stack_from_product(reference, stack)

def test_stack_from_id():
    run_test_stack_from_id()