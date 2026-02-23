import re

import pytest
from asf_search.Products import NISARProduct
from unittest.mock import patch

# For mocking data based on granule names, same as regex in NISARProduct
# but with crid version too
UTILITY_STATIC_PATTERN_STR = r'NISAR_L2_STATIC_.*_(?P<posting>\d{4}_\d{4})_(?P<validity_start_time>\d{8}T\d{6})_(?P<crid>\D\d{5})_\D_(?P<counter>\d{3})'
UTILITY_STATIC_PATTERN = re.compile(UTILITY_STATIC_PATTERN_STR)


def run_test_nisar_static_layer_from_id(params: dict, test_data: dict, expected_output: dict):
    expected_error = None
    if expected_error_type := expected_output.get('should_raise'):
        match expected_error_type:
            case 'ValueError':
                expected_error = ValueError
            case _:
                raise ValueError(
                    f"Unexpected error type '{expected_error_type}' in test case data. Fix or add error type to check"
                )

    pass


    if expected_error is not None:
        with pytest.raises(expected_error):
            NISARProduct.get_static_layer_from_id(params['product_id'])
    else:
        expected_scene_name = expected_output['scene_name']

        mock_test_data = [
            _mock_static_layer_NISARProduct(static_scene_name) for static_scene_name in test_data
        ]

        with patch('asf_search.search') as NISARProductPatch:
            NISARProductPatch.return_value = mock_test_data
            # NISARProductPatch.get_static_layer_from_id.isinstance.return_value = True
            scene_name = NISARProduct.get_static_layer_from_id(**params).properties['sceneName']
            print(scene_name)
        assert expected_scene_name == scene_name


def _mock_static_layer_NISARProduct(scene_name):
    """Create mock NISARProduct with the bare minimum data"""
    posting = UTILITY_STATIC_PATTERN.match(scene_name)
    if posting is not None:
        static_props = posting.groupdict()
        postings = static_props['posting'].split('_')
        return MockNISARProduct(
            scene_name=scene_name,
            posting=(postings[0], postings[1]),
            validity_start_time=static_props['validity_start_time'],
            crid=static_props['crid'],
            crid_counter=static_props['counter'],
        )

    raise ValueError(
        f'Invalid mock static layer file name provided "{scene_name}", unable to parse mock data from it (Verify spelling and format)'
    )


class MockNISARProduct:
    properties: dict

    def __init__(
        self,
        scene_name: str,
        posting: tuple[str, str],
        validity_start_time: str,
        crid: str,
        crid_counter: str,
    ) -> None:
        self.properties = {
            'sceneName': scene_name,
            'posting': posting,
            'validityStartDate': validity_start_time,
            'crid': crid,
            'crid_counter': crid_counter,
        }
