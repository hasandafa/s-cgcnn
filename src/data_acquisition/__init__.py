"""
Data acquisition module for S-CGCNN project.

This module handles fetching and validating material data from external sources
like Materials Project API.
"""

from .data_acquisition import scrape_binary_compounds
from .validator import validate_material_data, ValidationResult
from .cif_processor import process_all_materials, process_single_material

__all__ = [
    'scrape_binary_compounds',
    'validate_material_data',
    'ValidationResult',
    'process_all_materials',
    'process_single_material'
]

__version__ = "0.1.0"