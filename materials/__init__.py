"""
Materials Module - Dynamic Material Property System

This module provides a flexible system for loading and accessing material properties
from YAML configuration files. It supports:
- Binary materials (e.g., GaAs, AlAs)
- Alloy systems (e.g., AlGaAs)
- Multiple data sources (literature, MP-API)
- Tight-binding parameters
"""

from .material_loader import MaterialLoader, Material, AlloySystem
from .material_registry import MaterialRegistry

__all__ = ['MaterialLoader', 'Material', 'AlloySystem', 'MaterialRegistry']
__version__ = '1.0.0'