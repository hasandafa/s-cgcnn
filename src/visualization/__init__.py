"""
s-CGCNN v0.2 - Visualization Module
====================================

Interactive visualization and analysis tools for AlₓGa₁₋ₓAs structures.

Modules:
    - structure_viewer: Crystal-toolkit 3D structure visualization
    - property_plotter: Plotly interactive property plots  
    - figure_generator: Publication-ready figure generation
    - comparison_tools: Analysis and comparison utilities

Author: Abdullah Hasan Dafa
Version: 0.2
"""

from .structure_viewer import StructureViewer
from .property_plotter import PropertyPlotter
from .figure_generator import FigureGenerator
from .comparison_tools import ComparisonTools

__all__ = [
    'StructureViewer',
    'PropertyPlotter', 
    'FigureGenerator',
    'ComparisonTools'
]

__version__ = '0.2.0'