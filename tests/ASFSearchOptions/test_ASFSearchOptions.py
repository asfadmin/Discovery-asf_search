from asf_search.ASFSearchOptions import validators, ASFSearchOptions
from asf_search.ASFSearchOptions.validator_map import validate, validator_map
from pytest import raises

def run_test_validator_map_validate(key, value, output):
    if key not in list(validator_map.keys()):
        
        with raises(KeyError) as keyerror:
            validate(key, value)

        if key in [validator_key.lower() for validator_key in list(validator_map.keys())]:
            assert "Did you mean" in str(keyerror.value) 

        return

    assert validate(key, value) == output

def run_test_ASFSearchOptions_validator(validator_name, param, output, error):
    validator = getattr(validators, validator_name)
    
    if error == None:
        assert output == validator(param)
    else:
        with raises(ValueError) as e:
            validator(param)
        assert error in str(e.value)

def run_test_ASFSearchOptions(**kwargs):
    test_info = kwargs["test_info"]
    exception = test_info["exception"] # Can be "None" for don't.
    if "expect_output" in test_info:
        expect_output = test_info.pop("expect_output")
    else:
        expect_output = {}

    # Take out anything that isn't supposed to reach the options object:
    del test_info["title"]
    del test_info["exception"]

    try:
        options_obj = ASFSearchOptions(**test_info)
    except (KeyError, ValueError) as e:
        assert type(e).__name__ == exception, f"ERROR: Didn't expect exception {type(e).__name__} to occur."
        return
    else:
        assert exception == None, f"ERROR: Expected exception {exception}, but SearchOptions never threw."

    for key, val in expect_output.items():
        assert getattr(options_obj, key) == val, f"ERROR: options object param '{key}' should have value '{val}'. Got '{getattr(options_obj, key)}'."
