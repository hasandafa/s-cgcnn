"""
Enhanced Calculation Module for AlGaAs Pipeline

This module contains:
- constants.py: Material properties database with literature references
- structure_interpolator.py: Structure generation with charge density and relaxation
- property_calculator.py: Property calculations with tight-binding electronic structure
- electronic_structure.py: Tight-binding band structure calculations
- charge_density_interpolator.py: Real-space charge density interpolation
- structure_relaxer.py: ML-based structure relaxation
- main.py: Complete pipeline orchestration
"""

from .constants import *
from .structure_interpolator import StructureInterpolator, create_interpolator_from_config
from .property_calculator import PropertyCalculator
from .electronic_structure import GenericTightBinding, AlloyTightBinding, calculate_electronic_structure, calculate_material_electronic_structure
from .charge_density_interpolator import ChargeDensityInterpolator
from .structure_relaxer import StructureRelaxer, relax_structure_simple
from .main import run_full_pipeline, run_calculation_pipeline

__all__ = [
    # From constants
    'get_properties',
    'get_bowing_parameter',
    'determine_band_gap_type',
    'GAAS_PROPERTIES_LITERATURE',
    'ALAS_PROPERTIES_LITERATURE',
    'BOWING_PARAMETERS',
    'CROSSOVER_COMPOSITION',

    # From structure_interpolator
    'StructureInterpolator',
    'create_interpolator_from_config',

    # From property_calculator
    'PropertyCalculator',

    # From electronic_structure
    'GenericTightBinding',
    'AlloyTightBinding',
    'calculate_electronic_structure',
    'calculate_material_electronic_structure',

    # From charge_density_interpolator
    'ChargeDensityInterpolator',

    # From structure_relaxer
    'StructureRelaxer',
    'relax_structure_simple',

    # From main
    'run_full_pipeline',
    'run_calculation_pipeline',
]