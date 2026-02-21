import pytest
from asf_search.Products import NISARProduct

def run_test_nisar_static_layer_from_id(params: dict, test_data: dict, expected_output: dict):
    expected_error = None
    if expected_error_type := expected_output.get('should_raise'):
        match expected_error_type:
            case 'ValueError':
                expected_error = ValueError
            case _:
                raise ValueError(f"Unexpected error type '{expected_error_type}' in test case data. Fix or add error type to check")

    pass

    # TODO: mock test data based of test data scene names
    if expected_error is not None:
        with pytest.raises(expected_error):
            NISARProduct.get_static_layer_from_id(**params)
    else:
        expected_scene_name = expected_output['scene_name']
        scene_name = NISARProduct.get_static_layer_from_id(**params).properties['sceneName']

        assert expected_scene_name == scene_name
