import pytest
import re

from asf_search import S1MultiBurst, S1MultiBurstGroup, S1MultiBurstProduct, SBASNetwork

def test_three_by_three_group(three_by_three_multiburst_group):       
        assert len(three_by_three_multiburst_group.bursts) == 3

def test_horizontal_line_group():
        multiburst_group = S1MultiBurstGroup(
            bursts=[
                S1MultiBurst("173_370305", ("IW1", "IW2", "IW3")),
                ])
        
        assert len(multiburst_group.bursts) == 1


def test_vertical_line_group():
        multiburst_group = S1MultiBurstGroup(
            bursts=[
                S1MultiBurst("173_370305", ("IW1",)),
                S1MultiBurst("173_370306", ("IW1",)),
                S1MultiBurst("173_370307", ("IW1",))
                ])
        
        assert len(multiburst_group.bursts) == 3

def test_L_shaped_group():
    with pytest.raises(
        ValueError,
        match="Products from swaths 2 and 3 do not overlap"
        ):
        S1MultiBurstGroup(
            bursts=[
                S1MultiBurst("173_370305", ("IW1", "IW2")),
                S1MultiBurst("173_370306", ("IW1", "IW2")),
                S1MultiBurst("173_370307", ("IW1", "IW2", "IW3"))
                ])

def test_u_shaped_group():
    with pytest.raises(
        ValueError,
        match="Products from swaths 1 and 2 do not overlap"
        ):
        S1MultiBurstGroup(
            bursts=[
                S1MultiBurst("173_370305", ("IW1",        "IW3")),
                S1MultiBurst("173_370306", ("IW1",        "IW3")),
                S1MultiBurst("173_370307", ("IW1", "IW2", "IW3"))
                ])

def test_c_shaped_group():
    with pytest.raises(
        ValueError,
        match=re.escape("All bursts must have consecutive burst IDs. Found: [370305, 370307].")
        ):
        S1MultiBurstGroup(
            bursts=[
                S1MultiBurst("173_370305", ("IW1", "IW2", "IW3")),
                S1MultiBurst("173_370306", ("IW1",             )),
                S1MultiBurst("173_370307", ("IW1", "IW2", "IW3"))
                ])

def test_donut_shaped_group():
    with pytest.raises(
        ValueError,
        match=re.escape("All bursts must have consecutive burst IDs. Found: [370305, 370307].")
        ):   
        S1MultiBurstGroup(
            bursts=[
                S1MultiBurst("173_370305", ("IW1", "IW2", "IW3")),
                S1MultiBurst("173_370306", ("IW1",        "IW3")),
                S1MultiBurst("173_370307", ("IW1", "IW2", "IW3"))
                ])

def test_too_large_group():
    with pytest.raises(
        ValueError,
        match="An S1MultiBurstGroup may include no more than 15 burst/subswath combinations"
        ):
        S1MultiBurstGroup(
            bursts=[
                S1MultiBurst("173_370305", ("IW1", "IW2", "IW3")),
                S1MultiBurst("173_370306", ("IW1", "IW2", "IW3")),
                S1MultiBurst("173_370307", ("IW1", "IW2", "IW3")), 
                S1MultiBurst("173_370308", ("IW1", "IW2", "IW3")),
                S1MultiBurst("173_370309", ("IW1", "IW2", "IW3")),
                S1MultiBurst("173_370310", ("IW1", "IW2", "IW3")), 
                ])

def test_multiburst_product_from_multiburst_group(three_by_three_multiburst_product):
     assert three_by_three_multiburst_product.id == '173_370305_IW123_173_370306_IW123_173_370307_IW123_20230103'
     assert len(three_by_three_multiburst_product.geo_reference_bursts) == 9

def test_multiburst_product_from_geo_reference_bursts(three_by_three_multiburst_product):
    geo_ref_bursts = three_by_three_multiburst_product.geo_reference_bursts
    multiburst_product = S1MultiBurstProduct(geo_reference_bursts=geo_ref_bursts)
    assert three_by_three_multiburst_product == multiburst_product

