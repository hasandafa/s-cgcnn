"""
S-CGCNN: Crystal Graph Convolutional Neural Network for Materials Property Prediction

A comprehensive framework for AlGaAs alloy property prediction using
crystal graph convolutional neural networks.

Modules:
- calculation: Core calculation modules for structure interpolation and property calculation
- data_acquisition: Data fetching and validation from Materials Project
- utils: Utility functions for configuration, caching, and validation
"""

# Import key functions for easy access
from .calculation import run_full_pipeline, run_calculation_pipeline
from .data_acquisition import scrape_binary_compounds
from .utils import get_config, get_logger

__all__ = [
    # Main pipeline functions
    'run_full_pipeline',
    'run_calculation_pipeline',

    # Data acquisition
    'scrape_binary_compounds',

    # Utilities
    'get_config',
    'get_logger',
]

__version__ = "0.1.1"
__author__ = "Abdullah Hasan Dafa && Razasyattar M. N."