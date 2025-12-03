from datetime import date
import numpy as np
import pandas as pd
from pytest import raises

from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.search import product_search
from asf_search.Stack import Stack, DateTypeError, PairNotInFullStackWarning


def test_create_stack():
    ref_product = product_search('S1A_IW_SLC__1SDV_20220215T225119_20220215T225146_041930_04FE2E_9252-SLC')[0]
    args = ASFSearchOptions(**{"start": '2022-01-01', "end": '2022-05-02'})
    stack = Stack(ref_product, opts=args)

    assert len(stack.full_stack) == len(stack.subset_stack) == 45
    assert len(stack.connected_substacks) == 1

    return stack


def test_remove_pairs(stack):
    date_pair_list = [
        (date(2022, 1, 10), date(2022, 4, 4)),
        (pd.to_datetime("2022-1-10"), pd.to_datetime("2022-4-16")),
        ("2022-01-10", "2022-04-28"),
        (np.datetime64("2022-01-22"), np.datetime64("2022-02-03")),
        (date(2022, 1, 22), "2022-02-15"),
    ]

    stack.remove_pairs(date_pair_list)

    assert len(stack.full_stack) == 45
    assert len(stack.connected_substacks) == 1
    assert len(stack.subset_stack) == 40
    assert len(stack.remove_list) == 5
    assert date_pair_list[0] in stack.full_stack
    assert date_pair_list[0] in stack.remove_list
    assert date_pair_list[0] not in stack.subset_stack

    # assert all dates added to remove_list were normalized to the same type (datetime.date)
    assert len(set([type(scene_date) for pair in stack.remove_list for scene_date in pair])) == 1
    assert type(stack.remove_list[0][0]) is date

    with raises(PairNotInFullStackWarning):
        stack.remove_pairs([("1900-01-01", "1977-10-19")])
    with raises(DateTypeError):
        # single-digit months and days in ISO format should be preceded by a zero
        stack.remove_pairs([("2022-4-4", "2022-4-16")])
