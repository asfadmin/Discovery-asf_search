# backport of importlib.metadata for python < 3.8
from importlib_metadata import PackageNotFoundError, version

## Setup logging now, so it's available if __version__ fails:
import logging
ASF_LOGGER = logging.getLogger(__name__)
# Add null handle so we do nothing by default. It's up to whatever
# imports us, if they want logging.
ASF_LOGGER.addHandler(logging.NullHandler())

try:
    __version__ = version(__name__)
except PackageNotFoundError as e:
    msg = str(
        "package is not installed!\n"
        "Install in editable/develop mode via (from the top of this repo):\n"
        "   python3 -m pip install -e .\n"
        "Or, to just get the version number use:\n"
        "   python setup.py --version"
    )
    print(msg)
    ASF_LOGGER.exception(msg)  # type: ignore # noqa: F821
    raise PackageNotFoundError(
        "Install with 'python3 -m pip install -e .' to use"
    ) from e

ASF_LOGGER = logging.getLogger(__name__)
# Add null handle so we do nothing by default. It's up to whatever
# imports us, if they want logging.
ASF_LOGGER.addHandler(logging.NullHandler())

from .ASFSession import ASFSession  # noqa: F401, E402
from .ASFProduct import ASFProduct  # noqa: F401 E402
from .ASFStackableProduct import ASFStackableProduct  # noqa: F401 E402
from .ASFSearchResults import ASFSearchResults  # noqa: F401 E402
from .ASFSearchOptions import ASFSearchOptions, validators  # noqa: F401 E402
from .Products import *  # noqa: F403 F401 E402
from .exceptions import *  # noqa: F403 F401 E402
from .constants import (  # noqa: F401 E402
    BEAMMODE,  # noqa: F401 E402
    FLIGHT_DIRECTION,  # noqa: F401 E402
    INSTRUMENT,  # noqa: F401 E402
    PLATFORM,  # noqa: F401 E402
    POLARIZATION,  # noqa: F401 E402
    PRODUCT_TYPE,  # noqa: F401 E402
    INTERNAL,  # noqa: F401 E402
    DATASET,  # noqa: F401 E402
)
from .health import *  # noqa: F403 F401 E402
from .search import *  # noqa: F403 F401 E402
from .download import *  # noqa: F403 F401 E402
from .CMR import *  # noqa: F403 F401 E402
from .baseline import *  # noqa: F403 F401 E402
from .WKT import validate_wkt  # noqa: F401 E402
from .export import *  # noqa: F403 F401 E402

REPORT_ERRORS = True
"""Enables automatic search error reporting to ASF, send any questions to uso@asf.alaska.edu"""
