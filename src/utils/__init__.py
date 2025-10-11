"""
Utility modules for s-CGCNN

Provides:
- constants: Material properties (literature & MP-API)
- logger_config: Logging setup
- file_io: File I/O helpers (v0.1.1+)
- validators: Input validation (v0.1.1+)
"""

from . import constants
from .logger_config import setup_logger, get_logger

__all__ = [
    "constants",
    "setup_logger",
    "get_logger",
]

__version__ = "0.1.1"

# Try to import optional v0.1.1 modules
try:
    from . import file_io
    __all__.append("file_io")
except ImportError:
    pass

try:
    from . import validators
    __all__.append("validators")
except ImportError:
    pass