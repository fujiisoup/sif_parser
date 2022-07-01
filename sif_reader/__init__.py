raise DeprecationWarning("""
The `sif_reader` package will be depricated in version 0.4.0.
Please use the `sif_parser` package instead. The APIs are identical.
""")
from ._version import __version__, __version_info__
from .sif_open import *
from . import plugin
from . import utils
