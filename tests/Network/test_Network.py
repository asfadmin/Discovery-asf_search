from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.search import product_search
from asf_search.Network import Network, MultiBurst


def test_Network():
    ref_product = product_search('S1A_IW_SLC__1SDV_20220215T225119_20220215T225146_041930_04FE2E_9252-SLC')[0]
    opts = ASFSearchOptions(
        **{
            "start": '2014-01-01', 
            "end": '2025-10-02', 
            "season": [1, 176]
            }
            )

    network = Network(
        geo_reference=ref_product,
        perp_baseline=200, 
        inseason_temporal_baseline=12,
        bridge_target_date='3-1',
        bridge_year_threshold=2,
        opts=opts)

    assert len(network.full_stack) == 3225
    assert len(network.connected_substacks) == 4
    assert len(network.subset_stack) == 163
    assert len(network.remove_list) == 3062
    assert len(network.remove_list) + len(network.subset_stack) == len(network.full_stack)
    assert len(network.get_insar_pair_ids()) == 153


def test_multiburst_Network():
    multiburst_dict = {
        "085_181285": ("IW1", "IW2", ),
        "085_181286": ("IW1", "IW2", ),
        "085_181287": ("IW1", "IW2", "IW3")
    }
    multiburst = MultiBurst(multiburst_dict)
    opts = ASFSearchOptions(
        **{
            "start": '2015-01-01',
            "end": '2025-05-02',
            "season": [1, 176]
            }
    )

    network = Network(
        multiburst=multiburst,
        perp_baseline=400, 
        inseason_temporal_baseline=48,
        bridge_target_date='3-1',
        bridge_year_threshold=2,
        opts=opts)

    assert len(network.full_stack) == 3076
    assert len(network.remove_list) == 1919
    assert len(network.subset_stack) == 1157
    assert len(network.connected_substacks) == 1
    assert len(network.additional_multiburst_networks) == 6
    assert len(set([len(n.subset_stack) for n in network.additional_multiburst_networks])) == 1
