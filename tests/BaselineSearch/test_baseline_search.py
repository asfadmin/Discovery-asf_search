from copy import deepcopy
from unittest.mock import patch
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.Products import ARIAS1GUNWProduct
from asf_search.exceptions import ASFBaselineError, ASFSearchError
from asf_search.ASFSearchResults import ASFSearchResults
from asf_search import ASFSession, DATASET, BEAMMODE, POLARIZATION, PRODUCT_TYPE
from asf_search.search.baseline_search import stack_from_id, stack_from_product
from asf_search.baseline.stack import calculate_temporal_baselines
import pytest

from asf_search.search.search_generator import as_ASFProduct
from asf_enumeration import aria_s1_gunw

def run_test_get_preprocessed_stack_params(product):
    reference = as_ASFProduct(product, ASFSession())
    params = reference.get_stack_opts()

    original_properties = product['properties']

    assert params.processingLevel == [reference.get_default_baseline_product_type()]
    assert params.insarStackId == original_properties['insarStackId']
    assert len(dict(params)) == 2


def run_test_get_unprocessed_stack_params(product):
    reference = as_ASFProduct(product, ASFSession())
    params = reference.get_stack_opts()

    original_properties = product['properties']
    assert original_properties['polarization'] in params.polarization

    if reference.properties['processingLevel'] == 'BURST':
        assert [reference.properties['polarization']] == params.polarization
        assert [reference.properties['burst']['fullBurstID']] == params.fullBurstID
    elif reference.properties['sceneName'].startswith('S1-GUNW'):
        assert params.platform == ['SA', 'SB', 'SC']
        assert DATASET.SENTINEL1 in params.dataset
        assert params.processingLevel == [PRODUCT_TYPE.SLC]
        assert params.beamMode == [BEAMMODE.IW]
        assert params.polarization == [POLARIZATION.VV, POLARIZATION.VV_VH]
        assert params.flightDirection.upper() == reference.properties['flightDirection'].upper()
        assert params.relativeOrbit == [reference.properties['pathNumber']]
    else:
        assert (
            ['VV', 'VV+VH'] == params.polarization
            if reference.properties['polarization'] in ['VV', 'VV+VH']
            else ['HH', 'HH+HV'] == params.polarization
        )
        assert len(dict(params)) == 7


def run_get_stack_opts_invalid_insarStackId(product):
    invalid_reference = as_ASFProduct(product, ASFSession())

    invalid_reference.properties['insarStackId'] = '0'

    with pytest.raises(ASFBaselineError):
        invalid_reference.get_stack_opts()


def run_test_calc_temporal_baselines(reference, stack):
    reference = as_ASFProduct(reference, ASFSession())
    stack = ASFSearchResults([as_ASFProduct(product, ASFSession()) for product in stack])
    stackLength = len(stack)

    calculate_temporal_baselines(reference, stack)

    assert len(stack) == stackLength
    for secondary in stack:
        assert 'temporalBaseline' in secondary.properties


def run_test_stack_from_product(reference, stack):
    reference = as_ASFProduct(reference, ASFSession())

    with patch('asf_search.baseline_search.search') as search_mock:
        search_mock.return_value = ASFSearchResults(
            [as_ASFProduct(product, ASFSession()) for product in stack]
        )

        stack = stack_from_product(reference)

        for idx, secondary in enumerate(stack):
            if idx > 0:
                assert (
                    secondary.properties['temporalBaseline']
                    >= stack[idx - 1].properties['temporalBaseline']
                )


def run_test_stack_from_id(stack_id: str, reference, stack, opts: ASFSearchOptions):
    temp = deepcopy(stack)

    with patch('asf_search.baseline_search.product_search') as mock_product_search:
        mock_product_search.return_value = ASFSearchResults(
            [as_ASFProduct(product, ASFSession()) for product in stack]
        )

        if not stack_id:
            with pytest.raises(ASFSearchError):
                stack_from_id(stack_id)
        else:
            with patch('asf_search.baseline_search.search') as search_mock:
                search_mock.return_value = ASFSearchResults(
                    [as_ASFProduct(product, ASFSession()) for product in temp]
                )

                returned_stack = stack_from_id(stack_id, opts=opts)
                stack_files = set(x['properties']['fileID'] for x in stack)
                filtered_stack = [x for x in returned_stack if x.properties['fileID'] in stack_files]
                for idx, secondary in enumerate(filtered_stack):
                    if idx > 0:
                        assert (
                            secondary.properties['temporalBaseline']
                            >= stack[idx - 1]['properties']['temporalBaseline']
                        )