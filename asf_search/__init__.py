from importlib.metadata import PackageNotFoundError, version

from .ASFProduct import ASFProduct
from .ASFSearchResults import ASFSearchResults
from .exceptions import *
from .constants import *
from .health import *
from .search import *
from .download import *

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    print('package is not installed!\n'
          'Install in editable/develop mode via (from the top of this repo):\n'
          '   python -m pip install -e .\n'
          'Or, to just get the version number use:\n'
          '   python setup.py --version')