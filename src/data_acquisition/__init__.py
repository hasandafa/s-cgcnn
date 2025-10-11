"""
Data Acquisition modules for s-CGCNN

Provides:
- mp_fetcher: Materials Project API interface
- structure_interpolator: AlGaAs structure generation and property interpolation
"""

from .mp_fetcher import MPFetcher, create_fetcher_from_config
from .structure_interpolator import (
    StructureInterpolator,
    create_interpolator_from_config,
    AlloyComposition,
    AlloyProperties,
)

__all__ = [
    # Classes
    "MPFetcher",
    "StructureInterpolator",
    "AlloyComposition",
    "AlloyProperties",
    
    # Factory functions
    "create_fetcher_from_config",
    "create_interpolator_from_config",
]

__version__ = "0.1.1"