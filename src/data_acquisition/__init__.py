"""
Data acquisition module for S-CGCNN project.

This module handles fetching and validating material data from external sources
like Materials Project API.
"""

from .data_acquisition import scrape_binary_compounds
from .validator import validate_material_data, ValidationResult

__all__ = [
    'scrape_binary_compounds',
    'validate_material_data',
    'ValidationResult',
]

__version__ = "0.1.0"