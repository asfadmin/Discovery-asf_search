from asf_search.ASFSearchOptions import validators
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
    validator = load_validator_by_name(validator_name)
    
    if error == None:
        assert output == validator(param)
    else:
        with raises(ValueError) as e:
            validator(param)
        assert error in str(e.value)

def load_validator_by_name(validator_name: str):
    return getattr(validators, validator_name)
 