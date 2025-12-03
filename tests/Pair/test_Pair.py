from datetime import date, timedelta
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.search import product_search
from asf_search import Pair
import numpy as np


def test_make_s1_pairs():

    args = ASFSearchOptions(
        **{"start": '2022-02-10', "end": '2022-07-01'}
    )

    granule_product = product_search('S1A_IW_SLC__1SDV_20220215T225119_20220215T225146_041930_04FE2E_9252-SLC')[0]
    granule_stack = granule_product.stack(args)
    granule_pair = Pair(granule_product, granule_stack[1])
    assert granule_pair.ref.properties['sceneName'] == "S1A_IW_SLC__1SDV_20220215T225119_20220215T225146_041930_04FE2E_9252"
    assert granule_pair.sec.properties['sceneName'] == "S1A_IW_SLC__1SDV_20220227T225119_20220227T225146_042105_050431_987E"
    assert granule_pair.ref_date == date(2022, 2, 15)
    assert granule_pair.sec_date == date(2022, 2, 27)
    assert granule_pair.perpendicular == -15
    assert granule_pair.temporal == timedelta(days=12)
    assert np.floor(granule_pair.estimate_s1_mean_coherence()) == 18.0

    burst_product = product_search('S1_181296_IW1_20220219T125501_VV_10AF-BURST')[0]
    burst_stack = burst_product.stack(args)
    burst_pair = Pair(burst_product, burst_stack[1])
    assert burst_pair.ref.properties['sceneName'] == "S1_181296_IW1_20220219T125501_VV_10AF-BURST"
    assert burst_pair.sec.properties['sceneName'] == "S1_181296_IW1_20220303T125501_VV_F03A-BURST"
    assert burst_pair.ref_date == date(2022, 2, 19)
    assert burst_pair.sec_date == date(2022, 3, 3)
    assert burst_pair.perpendicular == -75
    assert burst_pair.temporal == timedelta(days=12)
    assert np.floor(burst_pair.estimate_s1_mean_coherence()) == 52.0
