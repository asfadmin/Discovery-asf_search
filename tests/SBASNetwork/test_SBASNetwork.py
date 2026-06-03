import copy
from datetime import date
import pickle
from pathlib import Path

from asf_search import SBASNetwork

try:
    from ciso8601 import parse_datetime
except ImportError:
    from dateutil.parser import parse as parse_datetime

import pytest

@pytest.fixture
def reference():
    path = Path(__file__).parent / "data/reference_scene_0.pkl"

    with open(path, "rb") as f:
        # trusted local test fixture
        return pickle.load(f) # nosec B301
    
@pytest.fixture
def pair():
    path = Path(__file__).parent / "data/pair_0.pkl"

    with open(path, "rb") as f:
        # trusted local test fixture
        return pickle.load(f) # nosec B301
    
@pytest.fixture
def stack_results():
    path = Path(__file__).parent / "data/stack_search_0.pkl"

    with open(path, "rb") as f:
        # trusted local test fixture
        return pickle.load(f) # nosec B301
    
@pytest.fixture
def sbas_network(stack_results):
    return SBASNetwork.from_search_results(
        stack_results,
        season=(1, 176),
        perpendicular_baseline=100, 
        inseason_temporal_baseline=24,
        bridge_target_date='3-1',
        bridge_year_threshold=2)

@pytest.fixture(scope="module")
def multiburst_dict():
    return {
        "173_370305": ("IW1", "IW2", "IW3"),
        "173_370306": ("IW1", "IW2", "IW3"),
        "173_370307": ("IW1", "IW2", "IW3"),
    }

@pytest.fixture(scope="module")
def sbas_s1_multiburst_base(multiburst_dict):
    return SBASNetwork.s1_multiburst(
        multiburst_dict,
        start_date='2023-01-01',
        end_date='2025-10-02' ,
        season=(1, 176),
        perpendicular_baseline=100,
        inseason_temporal_baseline=24,
        bridge_target_date='3-1',
        bridge_year_threshold=2,
    )

@pytest.fixture
def sbas_s1_multiburst(sbas_s1_multiburst_base):
    return copy.deepcopy(sbas_s1_multiburst_base)

def test_sbas_network_from_ref_scene(reference):
    """
    Create an SBASNetwork from a geographic reference scene
    """

    # Create an SBASNetwork and confrm expected size of its full_stack and subset_stack
    sbas = SBASNetwork(
        reference,
        start_date="2020-01-01",
        end_date="2025-10-02",
        season=(1, 176),
        perpendicular_baseline=100, 
        inseason_temporal_baseline=24,
        bridge_target_date='3-1',
        bridge_year_threshold=2)

    assert len(sbas.full_stack) == 1730
    assert len(sbas.subset_stack) == 176
    assert len(sbas.connected_substacks) == 3
    assert len(max(sbas.connected_substacks, key=lambda s: len(s))) == 161

def test_sbasnetwork_from_search_results(sbas_network):
    """
    Create an SBASNetwork from ASFProduct.stack search results with the 
    SBASNetwork.from_search_results alternate class method constructor
    """
    assert len(sbas_network.full_stack) == 1730
    assert len(sbas_network.subset_stack) == 176
    assert len(max(sbas_network.connected_substacks, key=lambda s: len(s))) == 161

def test_disallow_missing_state_vectors(stack_results):
    """
    Test the optional allow_missing_state_vectors argument set to False (default). 
    """
    stack_results[2].baseline["stateVectors"]["positions"]["prePositionTime"] = None
    missing_state_vectors_not_allowed_sbas = SBASNetwork.from_search_results(
        stack_results,
        season=(1, 176),
        perpendicular_baseline=100, 
        inseason_temporal_baseline=24,
        bridge_target_date='3-1',
        bridge_year_threshold=2)
    assert len(missing_state_vectors_not_allowed_sbas.full_stack) == 1698
    assert len([p for p in missing_state_vectors_not_allowed_sbas.full_stack if p.perpendicular_baseline is None]) == 0

def test_disallow_missing_state_vectors(stack_results):
    """
    Test the optional allow_missing_state_vectors argument set to True. 
    """
    stack_results[2].baseline["stateVectors"]["positions"]["prePositionTime"] = None
    missing_state_vectors_allowed_sbas = SBASNetwork.from_search_results(
        stack_results,
        season=(1, 176),
        perpendicular_baseline=100, 
        inseason_temporal_baseline=24,
        bridge_target_date='3-1',
        bridge_year_threshold=2,
        allow_missing_state_vectors=True)
    assert len(missing_state_vectors_allowed_sbas.full_stack) == 1730
    assert len([p for p in missing_state_vectors_allowed_sbas.full_stack if p.perpendicular_baseline is None]) == 32

def test_add_pair(sbas_network):
    removed_pair_0 = sbas_network.get_pair_from_dates(sbas_network.remove_list, date(2023,1,17), date(2024,6,16))
    sbas_network.add_pairs(removed_pair_0)
    assert len(sbas_network.subset_stack) == 177
    assert len(sbas_network.connected_substacks) == 2
    assert len(max(sbas_network.connected_substacks, key=lambda s: len(s))) == 165

def test_add_pairs(sbas_network):
    removed_pair_0 = sbas_network.get_pair_from_dates(sbas_network.remove_list, date(2023,1,17), date(2024,6,16))
    removed_pair_1 = sbas_network.get_pair_from_dates(sbas_network.remove_list, date(2023,1,5), date(2024,2,5))
    sbas_network.add_pairs([removed_pair_0, removed_pair_1])
    assert len(sbas_network.subset_stack) == 178
    assert len(sbas_network.connected_substacks) == 2
    assert len(max(sbas_network.connected_substacks, key=lambda s: len(s))) == 166

def test_remove_pairs(sbas_network):
    pair1_to_remove = sbas_network.get_pair_from_dates(sbas_network.subset_stack, date(2025,1,6), date(2025,1,18))
    pair2_to_remove = sbas_network.get_pair_from_dates(sbas_network.subset_stack, date(2025,1,6), date(2025,1,30))
    sbas_network.remove_pairs([pair1_to_remove, pair2_to_remove])
    assert len(sbas_network.subset_stack) == 174
    assert len(max(sbas_network.connected_substacks, key=lambda s: len(s))) == 159
    assert len(sbas_network.remove_list) == 1556

def add_new_pair(sbas_network, pair):
    sbas_network.add_pairs(pair)
    assert len(sbas_network.full_stack) == 1731
    assert len(sbas_network.subset_stack) == 176
    assert len(max(sbas_network.connected_substacks, key=lambda s: len(s))) == 164

def test_check_s1_multiburst_group_validity_valid(multiburst_dict):
    obj = SBASNetwork.__new__(SBASNetwork)
    obj.geo_reference_multiburst_dict = multiburst_dict

    obj.check_s1_multiburst_group_validiity()

def test_multiburst_sbas(sbas_s1_multiburst):
    assert len(sbas_s1_multiburst.s1_multiburst_sbas_networks) == 9
    assert len(sbas_s1_multiburst.s1_multiburst_georeferences) == 9

def test_add_pairs(sbas_s1_multiburst):
    assert len(sbas_s1_multiburst.connected_substacks) == 2

    geo_reference_dict_1 = {s.geo_reference: [
    sbas_s1_multiburst.get_pair_from_dates(s.remove_list, parse_datetime("20230304").date(), parse_datetime("20240614").date()),
    sbas_s1_multiburst.get_pair_from_dates(s.remove_list, parse_datetime("20230127").date(), parse_datetime("20230304").date()),
    ] for s in sbas_s1_multiburst.s1_multiburst_sbas_networks}

    sbas_s1_multiburst.s1_multiburst_add_pairs(geo_reference_dict_1)
    assert len(sbas_s1_multiburst.connected_substacks) == 1

def test_remove_pairs(sbas_s1_multiburst):
    assert len(sbas_s1_multiburst.s1_multiburst_sbas_networks[0].subset_stack) == 84

    pair = sbas_s1_multiburst.s1_multiburst_sbas_networks[0].subset_stack[0]
    sbas_s1_multiburst.s1_multiburst_remove_pairs({'all': [pair]})

    assert len(sbas_s1_multiburst.s1_multiburst_sbas_networks[0].subset_stack) == 83
