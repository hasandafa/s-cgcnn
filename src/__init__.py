"""
s-CGCNN: Simplified Crystal Graph Convolutional Neural Networks
for AlₓGa₁₋ₓAs Semiconductor Alloys

Version 0.1.1 - Enhanced with dual data source support

Author: Abdullah Hasan Dafa
Institution: Universitas Nasional, Indonesia
GitHub: https://github.com/hasandafa/s-cgcnn
"""

__version__ = "0.1.1"
__author__ = "Abdullah Hasan Dafa"
__email__ = "github.com/hasandafa"
__description__ = "Simplified CGCNN for CPU-efficient screening of AlGaAs alloys"

# Package metadata
__all__ = [
    "data_acquisition",
    "utils",
]

# Version history
VERSION_HISTORY = {
    "0.1.0": "Initial release - Literature-based interpolation",
    "0.1.1": "Added dual data source support (Literature + MP-API)",
}

# Feature flags
FEATURES = {
    "dual_data_source": True,
    "literature_mode": True,
    "mp_api_mode": True,
    "comparison_mode": True,
    "bandgap_correction": True,
}

def get_version() -> str:
    """Get current version string"""
    return __version__

def get_version_info() -> dict:
    """Get detailed version information"""
    return {
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "features": FEATURES,
        "history": VERSION_HISTORY,
    }

# Package initialization logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"s-CGCNN v{__version__} initialized")