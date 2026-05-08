import pickle
from pathlib import Path

from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search import Stack
from asf_search.warnings import PairNotInFullStackWarning

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
def stack(stack_results):
    return Stack.from_search_results(stack_results)
    
def test_stack_from_ref_scene(mocker, reference, stack_results):
    """
    Create a Stack from a geographic reference scene and confrm expected size of its full_stack and subset_stack
    """
    args = ASFSearchOptions(
        **{"start": "2022-01-01", "end": "2022-04-02"}
    )

    mock_stack = mocker.patch.object(
        reference,
        "stack",
        return_value=stack_results,
    )

    stack = Stack(reference, opts=args)

    mock_stack.assert_called_once_with(opts=args)

    assert len(stack.full_stack) == 21
    assert stack.subset_stack == stack.full_stack

def test_stack_from_search_results(stack):
    """
    Create a Stack from ASFProduct.stack search results with the Stack.from_search_results alternate class method constructor
    """
    assert len(stack.full_stack) == 21
    assert stack.subset_stack == stack.full_stack

def test_remove_pair(stack):
    stack.remove_pairs(stack.full_stack[0])
    assert len(stack.subset_stack) == 20
    assert len(stack.remove_list) == 1
    assert len(stack.connected_substacks) == 1 

def test_remove_pairs(stack):
    stack.remove_pairs(stack.full_stack[1:11])
    assert len(stack.subset_stack) == 11
    assert len(stack.remove_list) == 10
    assert len(stack.connected_substacks) == 2

def test_attempt_remove_invalid_pair(stack, pair):
    with pytest.warns(PairNotInFullStackWarning):
        stack.remove_pairs(pair)

def test_add_pair(stack):
    stack.remove_pairs(stack.full_stack[0])
    stack.add_pairs(stack.remove_list[0])
    assert len(stack.subset_stack) == 21
    assert len(stack.remove_list) == 0
    assert len(stack.connected_substacks) == 1 

def test_add_pairs(stack):
    stack.remove_pairs(stack.full_stack[1:11])
    stack.add_pairs(stack.remove_list)
    assert len(stack.subset_stack) == 21
    assert len(stack.remove_list) == 0
    assert len(stack.connected_substacks) == 1

def test_add_new_pair(stack, pair):
    stack.add_pairs(pair)
    assert len(stack.subset_stack) == 22
    assert len(stack.remove_list) == 0
    assert len(stack.connected_substacks) == 2 

def test_get_scene_ids(stack):
    stack.remove_pairs(stack.full_stack[1:11])
    largest_fully_connected_subset_stack_ids = stack.get_scene_ids()
    remove_list_scene_ids = stack.get_scene_ids(stack.remove_list)
    full_stack_scene_ids = stack.get_scene_ids(stack.full_stack)
    subset_stack_scene_ids = stack.get_scene_ids(stack.subset_stack)
    assert len(largest_fully_connected_subset_stack_ids) == 10
    assert len(remove_list_scene_ids) == 10
    assert len(full_stack_scene_ids) == 21
    assert len(subset_stack_scene_ids) == 11

def test_stack_disallow_missing_state_vectors(stack_results):
    """
    Test the optional allow_missing_state_vectors argument set to False (default). 
    """
    stack_results[2].baseline["stateVectors"]["positions"]["prePositionTime"] = None
    missing_state_vectors_not_allowed_stack = Stack.from_search_results(stack_results)
    assert len(missing_state_vectors_not_allowed_stack.full_stack) == 15
    assert len([p for p in missing_state_vectors_not_allowed_stack.full_stack if p.perpendicular_baseline is None]) == 0

def test_stack_allow_missing_state_vectors(stack_results):
    """
    Test the optional allow_missing_state_vectors argument set to False (default). 
    """
    stack_results[2].baseline["stateVectors"]["positions"]["prePositionTime"] = None
    missing_state_vectors_allowed_stack = Stack.from_search_results(stack_results, allow_missing_state_vectors=True)
    assert len(missing_state_vectors_allowed_stack.full_stack) == 21
    assert len([p for p in missing_state_vectors_allowed_stack.full_stack if p.perpendicular_baseline is None]) == 6
