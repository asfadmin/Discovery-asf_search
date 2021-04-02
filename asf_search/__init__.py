from .constants import *
from .health import *
from .search import *
from .baseline import *

try:
    # If we're an installed package, just use the provided version number
    __version__
except NameError:
    # Otherwise, figure it out from github since we're not in a packaged context
    import subprocess
    tag = subprocess.run(['git', 'describe', '--tags'], stdout=subprocess.PIPE).stdout.decode("utf-8").strip()
    __version__ = f'{tag}-devel'
    if "." not in __version__:
        __version__ = "0.0.0-devel"