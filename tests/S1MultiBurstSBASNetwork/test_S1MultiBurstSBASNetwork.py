import copy

from asf_search import S1MultiBurstSBASNetwork, S1MultiBurstSBASPairMap, S1MultiBurstGroup, get_pair_from_dates

try:
    from ciso8601 import parse_datetime
except ImportError:
    from dateutil.parser import parse as parse_datetime

import pytest

@pytest.fixture(scope="module")
def multiburst_dict():
    return S1MultiBurstGroup(
        bursts={
        "173_370305": ("IW1", "IW2", "IW3"),
        "173_370306": ("IW1", "IW2", "IW3"),
        "173_370307": ("IW1", "IW2", "IW3"),
        }
    )

@pytest.fixture(scope="module")
def sbas_s1_multiburst_base(multiburst_dict):
    return S1MultiBurstSBASNetwork(
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


def test_multiburst_sbas(sbas_s1_multiburst):
    assert len(sbas_s1_multiburst.sbas_networks) == 9
    assert len(sbas_s1_multiburst.georeferences) == 9

def test_multiburst_add_pairs(sbas_s1_multiburst):
    assert len(sbas_s1_multiburst.sbas_networks[0].connected_substacks) == 2

    burst_pair_map= S1MultiBurstSBASPairMap({s.geo_reference: [
    get_pair_from_dates(s.remove_list, parse_datetime("20230304").date(), parse_datetime("20240614").date()),
    get_pair_from_dates(s.remove_list, parse_datetime("20230127").date(), parse_datetime("20230304").date()),
    ] for s in sbas_s1_multiburst.sbas_networks}, sbas_s1_multiburst.sbas_networks)

    sbas_s1_multiburst.add_pairs(burst_pair_map)
    assert len(sbas_s1_multiburst.sbas_networks[0].connected_substacks) == 1

def test_multiburst_remove_pairs(sbas_s1_multiburst):
    assert len(sbas_s1_multiburst.sbas_networks[0].subset_stack) == 84

    burst_pair_map = S1MultiBurstSBASPairMap({s.geo_reference: [
    get_pair_from_dates(s.subset_stack, parse_datetime("20230220").date(), parse_datetime("20230316").date()),
    get_pair_from_dates(s.subset_stack, parse_datetime("20230304").date(), parse_datetime("20230316").date()),
    ] for s in sbas_s1_multiburst.sbas_networks}, sbas_s1_multiburst.sbas_networks)
    sbas_s1_multiburst.remove_pairs(burst_pair_map)

    assert len(sbas_s1_multiburst.sbas_networks[0].subset_stack) == 82