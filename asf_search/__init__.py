# backport of importlib.metadata for python < 3.8
from importlib_metadata import PackageNotFoundError, version

try:
    __version__ = version(__name__)
except PackageNotFoundError as e:
    print('package is not installed!\n'
          'Install in editable/develop mode via (from the top of this repo):\n'
          '   python3 -m pip install -e .\n'
          'Or, to just get the version number use:\n'
          '   python setup.py --version')
    raise PackageNotFoundError("Install with 'python3 -m pip install -e .' to use") from e

from .ASFSession import ASFSession
from .ASFProduct import ASFProduct
from .ASFSearchResults import ASFSearchResults
from .ASFSearchOptions import ASFSearchOptions, validators
from .exceptions import *
from .constants import *
from .health import *
from .search import *
from .download import *
from .CMR import *
from .baseline import *
from .WKT import validate_wkt
