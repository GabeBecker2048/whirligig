from importlib.metadata import PackageNotFoundError, version

from whirligig.spinner import spin

try:
    __version__ = version("whirligig")
except PackageNotFoundError:
    # running from a source tree without an install
    __version__ = "unknown"

__all__ = ["spin", "__version__"]