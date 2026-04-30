from datetime import date
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.search import product_search
from asf_search import Pair, SBASNetwork
import pytest

def test_make_s1_SBASNetwork():

 
    results = product_search('S1A_IW_SLC__1SDV_20220215T225119_20220215T225146_041930_04FE2E_9252-SLC')
    reference = results[0]

    opts = ASFSearchOptions(
        **{
            "start": '2020-01-01', 
            "end": '2025-10-02', 
            "season": (1, 176)
            }
    )

    # Create an SBASNetwork and confrm expected size of its full_stack and subset_stack
    sbas = SBASNetwork(
        geo_reference = reference,
        perpendicular_baseline=100, 
        inseason_temporal_baseline=24,
        bridge_target_date='3-1',
        bridge_year_threshold=2,
        opts=opts)
    assert len(sbas.full_stack) == 1730
    assert len(sbas.subset_stack) == 176
    assert len(sbas.connected_substacks) == 3
    assert len(max(sbas.connected_substacks, key=lambda s: len(s))) == 161

    # Use get_pair_from_dates() to retreive a Pair remove_list and add it to subset_stack
    removed_pair_to_return_to_network = sbas.get_pair_from_dates(sbas.remove_list,
                                                                 date(2023,1,17), 
                                                                 date(2024,6,16))
    sbas.add_pairs(removed_pair_to_return_to_network)
    assert len(sbas.subset_stack) == 177
    assert len(sbas.connected_substacks) == 2
    assert len(max(sbas.connected_substacks, key=lambda s: len(s))) == 165

    # Remove Pairs from subset_stack
    pair1_to_remove = sbas.get_pair_from_dates(sbas.subset_stack, date(2025,1,6), date(2025,1,18))
    pair2_to_remove = sbas.get_pair_from_dates(sbas.subset_stack, date(2025,1,6), date(2025,1,30))
    sbas.remove_pairs([pair1_to_remove, pair2_to_remove])
    assert len(sbas.subset_stack) == 175
    assert len(max(sbas.connected_substacks, key=lambda s: len(s))) == 163
    assert len(sbas.remove_list) == 1555

    # Add a Pair that does not exist in full_stack
    existing_pair = sbas.get_pair_from_dates(sbas.subset_stack, date(2025,3,7), date(2025,3,19))
    existing_ref_scene = existing_pair.ref
    results = product_search('S1A_IW_SLC__1SDV_20260401T105744_20260401T105802_063885_0808EC_7B1B-SLC')
    new_sec_scene = results[0]
    new_pair = Pair(existing_ref_scene, new_sec_scene)
    sbas.add_pairs(new_pair)
    assert len(sbas.full_stack) == 1731
    assert len(sbas.subset_stack) == 176
    assert len(max(sbas.connected_substacks, key=lambda s: len(s))) == 164
