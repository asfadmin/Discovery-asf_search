from datetime import datetime, timedelta, timezone
import pickle
from pathlib import Path

from asf_search import Pair
import numpy as np

import pytest

@pytest.fixture
def reference_full_scene():
    path = Path(__file__).parent / "data/reference_full_scene_0.pkl"

    with open(path, "rb") as f:
        # trusted local test fixture
        return pickle.load(f) # nosec B301
    
@pytest.fixture
def secondary_full_scene():
    path = Path(__file__).parent / "data/secondary_full_scene_0.pkl"

    with open(path, "rb") as f:
        # trusted local test fixture
        return pickle.load(f) # nosec B301
    
@pytest.fixture
def reference_burst():
    path = Path(__file__).parent / "data/reference_burst_0.pkl"

    with open(path, "rb") as f:
        # trusted local test fixture
        return pickle.load(f) # nosec B301
    
@pytest.fixture
def secondary_burst():
    path = Path(__file__).parent / "data/secondary_burst_0.pkl"

    with open(path, "rb") as f:
        # trusted local test fixture
        return pickle.load(f) # nosec B301


def test_make_full_scene_pair(reference_full_scene, secondary_full_scene):
    full_scene_pair = Pair(reference_full_scene, secondary_full_scene)
    assert full_scene_pair.ref.properties['sceneName'] == "S1A_IW_SLC__1SDV_20220215T225119_20220215T225146_041930_04FE2E_9252"
    assert full_scene_pair.sec.properties['sceneName'] == "S1A_IW_SLC__1SDV_20220227T225119_20220227T225146_042105_050431_987E"
    assert full_scene_pair.ref_time == datetime(2022, 2, 15, 22, 51, 19, tzinfo=timezone.utc)
    assert full_scene_pair.sec_time == datetime(2022, 2, 27, 22, 51, 19, tzinfo=timezone.utc)
    assert full_scene_pair.perpendicular_baseline == -15
    assert full_scene_pair.temporal_baseline == timedelta(days=12)
    assert np.floor(full_scene_pair.estimate_s1_mean_coherence()) == 18.0

def test_make_burst_pair(reference_burst, secondary_burst):
    burst_pair = Pair(reference_burst, secondary_burst)
    assert burst_pair.ref.properties['sceneName'] == "S1_181296_IW1_20220219T125501_VV_10AF-BURST"
    assert burst_pair.sec.properties['sceneName'] == "S1_181296_IW1_20220303T125501_VV_F03A-BURST"
    assert burst_pair.ref_time == datetime(2022, 2, 19, 12, 55, 3, tzinfo=timezone.utc)
    assert burst_pair.sec_time == datetime(2022, 3, 3, 12, 55, 2, tzinfo=timezone.utc)
    assert burst_pair.perpendicular_baseline == -75
    assert burst_pair.temporal_baseline == timedelta(days=12)
    assert np.floor(burst_pair.estimate_s1_mean_coherence()) == 52.0    
