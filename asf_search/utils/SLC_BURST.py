from copy import copy
from asf_search.search.search import search
from asf_search.ASFSearchOptions.ASFSearchOptions import ASFSearchOptions
from shapely.geometry import shape


def get_slc_burst_ids(
    intersectsWith: str = None,
    flightDirection: str = None,
    path: int = None,
    subswath: int = None,
    opts: ASFSearchOptions = None,
):
    kwargs = locals()
    data = dict((k, v) for k, v in kwargs.items() if k not in ["host", "opts"] and v is not None)

    burstmap = "Sentinel-1_Burst_Map"
    opts = ASFSearchOptions() if opts is None else copy(opts)
    opts.merge_args(**data)
    if subswath is not None:
        opts.cmr_keywords = [("attribute[]", f"string,SUBSWATH_NAME,{subswath}")]

    return search(shortName=burstmap, opts=opts)
