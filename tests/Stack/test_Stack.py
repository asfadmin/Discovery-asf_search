from datetime import datetime, timedelta, timezone
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.search import product_search
from asf_search import Pair, Stack
from asf_search.warnings import PairNotInFullStackWarning
import numpy as np
import pytest

def test_make_s1_stack():

    args = ASFSearchOptions(
        **{"start": '2022-01-01', "end": '2022-04-02'}
    )

    # Create a Stack and confrm expected size of its full_stack and subset_stack
    results = product_search('S1A_IW_SLC__1SDV_20220215T225119_20220215T225146_041930_04FE2E_9252-SLC')
    reference = results[0]
    stack = Stack(reference, opts=args)
    assert len(stack.full_stack) == 21
    assert stack.subset_stack == stack.full_stack

    # Remove Pairs from the Stack, confirm expected Pair list lengths
    stack.remove_pairs(stack.full_stack[1:11])
    assert len(stack.subset_stack) == 11
    assert len(stack.remove_list) == 10
    assert len(stack.connected_substacks) == 2

    # Add one Pair back and confirm expexted Pair list lengths
    stack.add_pairs([stack.remove_list[0]])
    assert len(stack.subset_stack) == 12
    assert len(stack.remove_list) == 9
    assert len(stack.connected_substacks) == 1

    # Create a Pair not present in the stack and confirm that it cannot be removed
    results_1 = product_search('S1A_IW_SLC__1SDV_20250903T225120_20250903T225147_060830_0792D3_868A-SLC')
    results_2 = product_search('S1A_IW_SLC__1SDV_20250822T225120_20250822T225147_060655_078BEA_2065-SLC')
    my_pair = Pair(results_1[0], results_2[0])
    with pytest.warns(PairNotInFullStackWarning):
        stack.remove_pairs([my_pair])

    # Add the new Pair to the stack and confirm expected Pair list lengths
    stack.add_pairs([my_pair])
    assert len(stack.full_stack) == 22
    assert len(stack.subset_stack) == 13
    assert len(stack.connected_substacks) == 2

    # Test Stack.get_scene_ids()
    largest_fully_connected_subset_stack_ids = stack.get_scene_ids()
    remove_list_scene_ids = stack.get_scene_ids(stack.remove_list)
    full_stack_scene_ids = stack.get_scene_ids(stack.full_stack)
    subset_stack_scene_ids = stack.get_scene_ids(stack.subset_stack)
    assert len(largest_fully_connected_subset_stack_ids) == 12
    assert len(remove_list_scene_ids) == 9
    assert len(full_stack_scene_ids) == 22
    assert len(subset_stack_scene_ids) == 13

