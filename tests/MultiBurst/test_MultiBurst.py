from asf_search.MultiBurst import (
    MultiBurst,
    MultipleOrbitError,
    InvalidMultiBurstCountError,
    InvalidMultiBurstTopologyError,
    AntimeridianError
    )
from pytest import raises

PASSING_MULTIBURST_DICTS = [
    {
        "173_370305": ("IW1", "IW2", "IW3"),
        "173_370306": ("IW1", "IW2", "IW3"),
        "173_370307": ("IW1", "IW2", "IW3")
    },
    # Diagonal line of bursts
    {
        "173_370305": ("IW1",),
        "173_370306": ("IW2",),
        "173_370307": ("IW3",),
    },
    # "Vertical" zigzag line of bursts
    {
        "173_370305": ["IW1"],
        "173_370306": ["IW2"],
        "173_370307": ["IW1"],
    },
    # "Horizontal" zigzag line of bursts
    {
        "173_370305": ("IW1", "IW3"),
        "173_370306": ("IW2",)
    },
]

FAILING_MULTIBURST_DICTS = [
    # multiple orbital paths
    {
        "173_370305": ("IW1", "IW2", "IW3"),
        "173_370306": ("IW1", "IW2", "IW3"),
        "100_213509": ("IW1", "IW2", "IW3")      
    },
    # disconnected with holes
    {
        "173_370305": ("IW1", "IW2",),
        "173_370306": ("IW1", "IW2", "IW3"),
        "173_370307": ("IW1", ),
        "173_370308": ("IW3",),
        "173_370309": ("IW1", "IW2", "IW3"),
        "173_370310": ("IW1", "IW3"),
        "173_370311": ("IW1", "IW2", "IW3")
    },
    # intersects the Antimeridan
    {
        "001_000664": ("IW1", "IW2", "IW3"),
        "001_000665": ("IW1", "IW2", "IW3"),
        "001_000666": ("IW1", "IW2", "IW3")
    },
    # too big
    {
        "173_370306": ("IW1", "IW2", "IW3"),
        "173_370307": ("IW1", "IW2", "IW3"),
        "173_370308": ("IW1", "IW2", "IW3"),
        "173_370309": ("IW1", "IW2", "IW3"),
        "173_370310": ("IW1", "IW2", "IW3"),
        "173_370311": ("IW1", "IW2", "IW3")
    }
]


def test_multiburst():
    for i, multiburst_dict in enumerate(PASSING_MULTIBURST_DICTS):
        multiburst = MultiBurst(multiburst_dict)
        if i == 0:
            extent_wkt = ("POLYGON((-116.758181 35.403803,-113.866367 35.403803,"
                          "-113.866367 36.216503,-116.758181 36.216503,-116.758181 35.403803))")
            assert multiburst.extent_wkt == extent_wkt

    for i, multiburst_dict in enumerate(FAILING_MULTIBURST_DICTS):
        if i == 0:
            exception = MultipleOrbitError
        elif i == 1:
            exception = InvalidMultiBurstTopologyError
        elif i == 2:
            exception = AntimeridianError
        elif i == 3:
            exception = InvalidMultiBurstCountError
        with raises(exception):
            multiburst = MultiBurst(multiburst_dict)
