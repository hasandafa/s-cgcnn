"""
Graph Conversion Module for S-CGCNN

This module handles the conversion of crystal structures and material properties
into graph representations suitable for Graph Neural Network training.

Key Components:
- CrystalGraphBuilder: Converts pymatgen Structures to PyTorch Geometric graphs
- FeatureExtractor: Extracts node and edge features from crystal structures
- FeatureNormalizer: Normalizes features for stable training
- MaterialPropertyDataset: PyTorch Dataset for material property prediction
- GraphConversionPipeline: Main pipeline for batch conversion
"""

from .graph_builder import CrystalGraphBuilder
from .feature_extractor import FeatureExtractor
from .normalizer import FeatureNormalizer
from .dataset import MaterialPropertyDataset
from .pipeline import GraphConversionPipeline
from .visualizer import GraphVisualizer

__all__ = [
    'CrystalGraphBuilder',
    'FeatureExtractor',
    'FeatureNormalizer',
    'MaterialPropertyDataset',
    'GraphConversionPipeline',
    'GraphVisualizer'
]