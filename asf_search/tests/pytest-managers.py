from asf_search.exceptions import ASFAuthenticationError

# from fixtures import ASFProduct_fixtures
from test_ASFProduct import run_test_ASFProduct_Geo_Search, run_test_stack
from test_ASFSession import run_auth_with_creds

from pytest import raises

from unittest.mock import patch
# from custom_add import run_add_test
# from custom_factor import run_fact_test

# The methods here matchs the 'method' key in 'pytest-config.yml' example. (Required)
# @pytest.fixture
# def metafuncParam(metafunc):
    # return metafunc

# @pytest.mark.parametrize("metafunction", metafunc)
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