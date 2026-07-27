import copy
from datetime import date
import pickle
from pathlib import Path

from asf_search import SBASNetwork, get_existing_pair_from_dates

import pytest

@pytest.fixture
def reference():
    path = Path(__file__).parent / "data/reference_scene_0.pkl"

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

@pytest.fixture
def multiburst_sbas_network(three_by_three_multiburst_product):
    return SBASNetwork.from_geo_reference(
    geo_reference = three_by_three_multiburst_product,
    start_date = '2023-01-01',
    end_date = '2025-10-02',
    season = (1, 176),
    perpendicular_baseline=150, 
    inseason_temporal_baseline=36,
    bridge_target_date='3-1',
    bridge_year_threshold=1)

def test_sbas_network_from_ref_scene(reference):
    """
    Create an SBASNetwork from a geographic reference scene
    """
    sbas = SBASNetwork.from_geo_reference(
        reference,
        start_date="2020-01-01",
        end_date="2025-10-02",
        season=(1, 176),
        perpendicular_baseline=100, 
        inseason_temporal_baseline=24,
        bridge_target_date='3-1',
        bridge_year_threshold=2)

    assert len(sbas.full_stack) == 1508
    assert len(sbas.subset_stack) == 159
    assert len(sbas.connected_substacks) == 4
    assert len(max(sbas.connected_substacks, key=lambda s: len(s))) == 145

def test_multiburst_sbas_network(multiburst_sbas_network):
    assert len(multiburst_sbas_network.full_stack) == 416
    assert len(multiburst_sbas_network.subset_stack) == 99
    assert len(multiburst_sbas_network.connected_substacks) == 3
    assert len(max(multiburst_sbas_network.connected_substacks, key=lambda s: len(s))) == 96

def test_sbasnetwork_from_search_results(sbas_network):
    """
    Create an SBASNetwork from ASFProduct.stack search results with the 
    SBASNetwork.from_search_results alternate class method constructor
    """
    assert len(sbas_network.full_stack) == 1508
    assert len(sbas_network.subset_stack) == 159
    assert len(max(sbas_network.connected_substacks, key=lambda s: len(s))) == 145

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
    assert len(missing_state_vectors_allowed_sbas.full_stack) == 1508
    assert len([p for p in missing_state_vectors_allowed_sbas.full_stack if p.perpendicular_baseline is None]) == 32

def test_add_pair_date_strings(sbas_network):
    """
    Tests adding a single pair, which is on the remove_list, using date pair strings
    """
    removed_list_size = len(sbas_network.remove_list)
    sbas_network.add_pairs(("2023-01-17", "2024-06-16"))
    assert len(sbas_network.subset_stack) == 160
    assert len(sbas_network.remove_list) == removed_list_size - 1
    assert len(sbas_network.connected_substacks) == 3
    assert len(max(sbas_network.connected_substacks, key=lambda s: len(s))) == 145

def test_add_multiburst_pair_date_strings(multiburst_sbas_network):
    """
    Tests adding a single S1MultiBurstProduct pair, which is on the remove_list, using date pair strings
    """
    multiburst_sbas_network.add_pairs(("2024-03-22", "2024-04-15"))
    assert len(multiburst_sbas_network.subset_stack) == 100
    assert len(multiburst_sbas_network.connected_substacks) == 3
    assert len(max(multiburst_sbas_network.connected_substacks, key=lambda s: len(s))) == 97

def test_add_new_pair_date_strings(sbas_network):
    """
    tests adding a pair previously unknown to the SBASNetwork
    and not on the remove_list, using date pair strings
    """
    removed_list_size = len(sbas_network.remove_list)
    sbas_network.add_pairs(("2023-01-17", "2025-05-14"))
    assert len(sbas_network.subset_stack) == 160
    assert len(sbas_network.remove_list) == removed_list_size
    assert len(sbas_network.connected_substacks) == 3
    assert len(max(sbas_network.connected_substacks, key=lambda s: len(s))) == 145

def test_add_pairs_date_strings(sbas_network):
    """
    Tests adding a multiple pairs using date pair strings
    """
    sbas_network.add_pairs([("2023-01-17", "2024-06-16"), ("2023-01-05", "2024-02-05")])
    assert len(sbas_network.subset_stack) == 161
    assert len(sbas_network.connected_substacks) == 2
    assert len(max(sbas_network.connected_substacks, key=lambda s: len(s))) == 151

def test_add_multiburst_pairs_date_strings(multiburst_sbas_network):
    """
    Tests adding multiple S1MultiBurstProduct pairs using date pair strings
    """
    multiburst_sbas_network.add_pairs([("2024-03-22", "2024-04-15"), ("2024-04-03", "2024-02-15")])
    assert len(multiburst_sbas_network.subset_stack) == 101
    assert len(multiburst_sbas_network.connected_substacks) == 3
    assert len(max(multiburst_sbas_network.connected_substacks, key=lambda s: len(s))) == 98

def test_add_pair_object(sbas_network):
    """
    Tests adding a single pair using a Pair object
    """
    pair_to_add = sbas_network.remove_list[10]
    removed_list_size = len(sbas_network.remove_list)
    sbas_network.add_pairs(pair_to_add)
    assert len(sbas_network.subset_stack) == 160
    assert len(sbas_network.remove_list) == removed_list_size - 1
    assert len(sbas_network.connected_substacks) == 4
    assert len(max(sbas_network.connected_substacks, key=lambda s: len(s))) == 146

def test_add_multiburst_pair_object(multiburst_sbas_network):
    """
    Tests adding a single S1MultiBurstProduct pair using a Pair object
    """
    pair_to_add = multiburst_sbas_network.remove_list[10]
    removed_list_size = len(multiburst_sbas_network.remove_list)
    multiburst_sbas_network.add_pairs(pair_to_add)
    assert len(multiburst_sbas_network.subset_stack) == 100
    assert len(multiburst_sbas_network.remove_list) == removed_list_size - 1
    assert len(multiburst_sbas_network.connected_substacks) == 3
    assert len(max(multiburst_sbas_network.connected_substacks, key=lambda s: len(s))) == 97

def test_add_pair_objects(sbas_network):
    """
    Tests adding a multiple pairs using Pair objects
    """
    pair_to_add_1 = sbas_network.remove_list[10]
    pair_to_add_2 = sbas_network.remove_list[-1]
    removed_list_size = len(sbas_network.remove_list)
    sbas_network.add_pairs([pair_to_add_1, pair_to_add_2])
    assert len(sbas_network.subset_stack) == 161
    assert len(sbas_network.remove_list) == removed_list_size - 2
    assert len(sbas_network.connected_substacks) == 4
    assert len(max(sbas_network.connected_substacks, key=lambda s: len(s))) == 147

def test_add_multiburst_pair_objects(multiburst_sbas_network):
    """
    Tests adding multiple S1MultiBurstProduct pairs using a Pair objects
    """
    pairs_to_add = multiburst_sbas_network.remove_list[10:12]
    removed_list_size = len(multiburst_sbas_network.remove_list)
    multiburst_sbas_network.add_pairs(pairs_to_add)
    assert len(multiburst_sbas_network.subset_stack) == 101
    assert len(multiburst_sbas_network.remove_list) == removed_list_size - 2
    assert len(multiburst_sbas_network.connected_substacks) == 3
    assert len(max(multiburst_sbas_network.connected_substacks, key=lambda s: len(s))) == 98

def test_remove_pair_date_strings(sbas_network):
    """
    Tests removing a single pair using date pair strings
    """
    removed_list_size = len(sbas_network.remove_list)
    sbas_network.remove_pairs(("2025-01-06", "2025-01-18"))
    assert len(sbas_network.subset_stack) == 158
    assert len(sbas_network.remove_list) == removed_list_size + 1
    assert len(sbas_network.connected_substacks) == 4
    assert len(max(sbas_network.connected_substacks, key=lambda s: len(s))) == 144

def test_remove_multiburst_pair_date_strings(multiburst_sbas_network):
    """
    Tests removing a single S1MultiBurstProduct pair using date pair strings
    """
    removed_list_size = len(multiburst_sbas_network.remove_list)
    multiburst_sbas_network.remove_pairs(("2023-02-20", "2024-02-15"))
    assert len(multiburst_sbas_network.subset_stack) == 98
    assert len(multiburst_sbas_network.remove_list) == removed_list_size + 1
    assert len(multiburst_sbas_network.connected_substacks) == 3
    assert len(max(multiburst_sbas_network.connected_substacks, key=lambda s: len(s))) == 95

def test_remove_pairs_date_strings(sbas_network):
    """
    Tests a multiple pairs using date pair strings
    """
    removed_list_size = len(sbas_network.remove_list)
    sbas_network.remove_pairs([("2025-01-06", "2025-01-18"), ("2025-01-06", "2025-01-30")])
    assert len(sbas_network.subset_stack) == 157
    assert len(sbas_network.remove_list) == removed_list_size + 2
    assert len(sbas_network.connected_substacks) == 4
    assert len(max(sbas_network.connected_substacks, key=lambda s: len(s))) == 143

def test_remove_multiburst_pairs_date_strings(multiburst_sbas_network):
    """
    Tests removing multiple S1MultiBurstProduct pairs using date pair strings
    """
    removed_list_size = len(multiburst_sbas_network.remove_list)
    multiburst_sbas_network.remove_pairs([("2023-02-20", "2024-02-15"), ("2023-03-04", "2024-02-15")])
    assert len(multiburst_sbas_network.subset_stack) == 97
    assert len(multiburst_sbas_network.remove_list) == removed_list_size + 2
    assert len(multiburst_sbas_network.connected_substacks) == 3
    assert len(max(multiburst_sbas_network.connected_substacks, key=lambda s: len(s))) == 94

def test_remove_pair_object(sbas_network):
    """
    Tests removing a single pair using a Pair object
    """
    removed_list_size = len(sbas_network.remove_list)
    sbas_network.remove_pairs(sbas_network.subset_stack[0])
    assert len(sbas_network.subset_stack) == 158
    assert len(sbas_network.remove_list) == removed_list_size + 1
    assert len(sbas_network.connected_substacks) == 4
    assert len(max(sbas_network.connected_substacks, key=lambda s: len(s))) == 144

def test_remove_multiburst_pair_object(multiburst_sbas_network):
    """
    Tests removing a single S1MultiBurstProduct pair using a Pair object
    """
    removed_list_size = len(multiburst_sbas_network.remove_list)
    multiburst_sbas_network.remove_pairs(multiburst_sbas_network.subset_stack[0])
    assert len(multiburst_sbas_network.subset_stack) == 98
    assert len(multiburst_sbas_network.remove_list) == removed_list_size + 1
    assert len(multiburst_sbas_network.connected_substacks) == 3
    assert len(max(multiburst_sbas_network.connected_substacks, key=lambda s: len(s))) == 95

def test_remove_pair_objects(sbas_network):
    """
    Tests removing multiple pairs using pair objects
    """
    removed_list_size = len(sbas_network.remove_list)
    sbas_network.remove_pairs(sbas_network.subset_stack[:3])
    assert len(sbas_network.subset_stack) == 156
    assert len(sbas_network.remove_list) == removed_list_size + 3
    assert len(sbas_network.connected_substacks) == 4
    assert len(max(sbas_network.connected_substacks, key=lambda s: len(s))) == 142

def test_remove_multiburst_pair_objects(multiburst_sbas_network):
    """
    Tests removing multiple S1MultiBurstProduct pairs using pair objects
    """
    removed_list_size = len(multiburst_sbas_network.remove_list)
    multiburst_sbas_network.remove_pairs(multiburst_sbas_network.subset_stack[:3])
    assert len(multiburst_sbas_network.subset_stack) == 96
    assert len(multiburst_sbas_network.remove_list) == removed_list_size + 3
    assert len(multiburst_sbas_network.connected_substacks) == 3
    assert len(max(multiburst_sbas_network.connected_substacks, key=lambda s: len(s))) == 93
