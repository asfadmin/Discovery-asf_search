from datetime import date
import pickle
from pathlib import Path

from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search import SBASNetwork

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
    
def test_sbas_network_from_ref_scene(mocker, reference, stack_results):
    """
    Create an SBASNetwork from a geographic reference scene
    """
    mock_stack = mocker.patch.object(
        reference,
        "stack",
        return_value=stack_results,
    )

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
