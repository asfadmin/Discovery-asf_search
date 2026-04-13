from asf_search.constants import PRODUCT_TYPE
from asf_search.search import search
from asf_search import ASFSearchOptions
from copy import copy


def get_nisar_orbit_ephemeras(opts: ASFSearchOptions | None = None):
    """Returns a dictionary of the latest NISAR orbit ephemera products (`POE`, `MOE`, `NOE`, and `FOE`).
    Additional options may be specified to pass to search.

    For more information refer to the NISAR Data User Guide:
    https://nisar-docs.asf.alaska.edu/orbit-ephemeris/#tbl-nisar-orbit-ephemeris-characteristics
    """
    opts = ASFSearchOptions() if opts is None else copy(opts)

    opts.shortName = 'NISAR_OE'
    opts.maxResults = 1

    orbits = {}
    for processingLevel in [PRODUCT_TYPE.POE, PRODUCT_TYPE.MOE, PRODUCT_TYPE.NOE, PRODUCT_TYPE.FOE]:
        orbits[processingLevel] = search(opts=opts, processingLevel=processingLevel)[0]

    return orbits
