"""
Core graph construction from crystal structures.
"""

import torch
from torch_geometric.data import Data
import numpy as np
from typing import Optional, Dict, Any, List
from pymatgen.core import Structure

from .feature_extractor import FeatureExtractor
from .normalizer import FeatureNormalizer
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CrystalGraphBuilder:
    """Converts crystal structures to graph representations."""

    def __init__(self, cutoff_radius: float = 5.0, normalize: bool = True):
        """
        Initialize graph builder.

        Args:
            cutoff_radius: Maximum distance for edge connections (Å)
            normalize: Whether to normalize features
        """
        self.cutoff_radius = cutoff_radius
        self.normalize = normalize
        self.feature_extractor = FeatureExtractor(cutoff_radius=cutoff_radius)
        self.normalizer: Optional[FeatureNormalizer] = None

        if self.normalize:
            self.normalizer = FeatureNormalizer()

    def structure_to_graph(self, structure: Structure, properties: Dict[str, Any],
                           composition: float, structure_type: str,
                           per_atom_charge_density: Optional[np.ndarray] = None) -> Data:
        """
        Convert pymatgen Structure to PyTorch Geometric Data.

        Args:
            structure: pymatgen Structure object
            properties: Dictionary of material properties
            composition: Composition value (x in Al_x Ga_{1-x} As)
            structure_type: "original" or "relaxed"
            per_atom_charge_density: Optional array of charge density values per atom

        Returns:
            PyTorch Geometric Data object
        """
        # Extract features
        node_features, edge_index, edge_features = self.feature_extractor.extract_all_features(
            structure, per_atom_charge_density
        )

        # Convert to tensors
        x = torch.tensor(node_features, dtype=torch.float)
        edge_index = torch.tensor(edge_index, dtype=torch.long)
        edge_attr = torch.tensor(edge_features, dtype=torch.float)

        # Extract target properties (20 properties as per spec)
        target_properties = self._extract_target_properties(properties)
        y = torch.tensor(target_properties, dtype=torch.float)

        # Create graph data object
        graph = Data(
            x=x,
            edge_index=edge_index,
            edge_attr=edge_attr,
            y=y,
            composition=composition,
            structure_type=structure_type,
            num_nodes=len(structure)
        )

        # Apply normalization if enabled
        if self.normalize and self.normalizer and self.normalizer.fitted:
            graph = self.normalizer.transform(graph)

        return graph

    def _extract_target_properties(self, properties: Dict[str, Any]) -> np.ndarray:
        """
        Extract the 20 target properties in the correct order.

        Args:
            properties: Raw properties dictionary

        Returns:
            Array of 20 target properties
        """
        # Property order as defined in the spec
        property_names = [
            'lattice_constant',
            'band_gap',
            'band_gap_type',
            'electron_affinity',
            'effective_mass_electron',
            'effective_mass_hole_heavy',
            'effective_mass_hole_light',
            'dielectric_constant_static',
            'dielectric_constant_high_freq',
            'refractive_index',
            'bulk_modulus',
            'shear_modulus',
            'youngs_modulus',
            'poissons_ratio',
            'elastic_constant_c11',
            'elastic_constant_c12',
            'elastic_constant_c44',
            'electron_mobility',
            'hole_mobility',
            'thermal_conductivity'
        ]

        targets = []
        for prop_name in property_names:
            if prop_name in properties:
                value = properties[prop_name]
                # Convert band_gap_type to numeric (0=indirect, 1=direct)
                if prop_name == 'band_gap_type':
                    value = 1 if value == 'direct' else 0
                targets.append(float(value))
            else:
                logger.warning(f"Missing property: {prop_name}, using NaN")
                targets.append(np.nan)

        return np.array(targets)

    def fit_normalizer(self, graphs: List[Data]) -> None:
        """
        Fit the normalizer on a dataset of graphs.

        Args:
            graphs: List of PyTorch Geometric Data objects
        """
        if self.normalize and self.normalizer:
            self.normalizer.fit(graphs)
            logger.info("Graph builder normalizer fitted")
        else:
            logger.info("Normalization disabled or no normalizer available")

    def add_edge_indices(self, graph: Data) -> Data:
        """
        Ensure edge indices are properly formatted.
        This is mainly for compatibility - edges are already computed in feature extraction.

        Args:
            graph: PyTorch Geometric Data object

        Returns:
            Graph with validated edge indices
        """
        # Edge indices should already be set, but we can validate here
        if graph.edge_index is None or graph.edge_index.shape[0] != 2:
            raise ValueError("Invalid edge_index format")

        return graph

    def add_features(self, graph: Data) -> Data:
        """
        Add any additional features to the graph.
        Currently a placeholder for future extensions.

        Args:
            graph: PyTorch Geometric Data object

        Returns:
            Graph with additional features
        """
        # Could add charge density features here if available
        return graph

    def get_graph_info(self, graph: Data) -> Dict[str, Any]:
        """
        Get information about a graph.

        Args:
            graph: PyTorch Geometric Data object

        Returns:
            Dictionary with graph statistics
        """
        return {
            'num_nodes': graph.num_nodes,
            'num_edges': graph.edge_index.shape[1] if graph.edge_index is not None else 0,
            'node_features_dim': graph.x.shape[1] if graph.x is not None else 0,
            'edge_features_dim': graph.edge_attr.shape[1] if graph.edge_attr is not None else 0,
            'target_dim': graph.y.shape[0] if graph.y is not None else 0,
            'composition': graph.composition,
            'structure_type': graph.structure_type
        }

    def validate_graph(self, graph: Data) -> bool:
        """
        Validate graph structure and features.

        Args:
            graph: PyTorch Geometric Data object

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check basic structure
            if graph.x is None or graph.edge_index is None or graph.y is None:
                logger.error("Missing required graph components")
                return False

            # Check dimensions - now supports 10 or 11 features (with/without charge density)
            expected_dims = [10, 11]  # 10 for basic features, 11 with charge density
            if graph.x.shape[1] not in expected_dims:
                logger.error(f"Invalid node features dimension: {graph.x.shape[1]} (expected 10 or 11)")
                return False

            if graph.edge_attr.shape[1] != 4:
                logger.error(f"Invalid edge features dimension: {graph.edge_attr.shape[1]} (expected 4)")
                return False

            if graph.y.shape[0] != 20:
                logger.error(f"Invalid target dimension: {graph.y.shape[0]} (expected 20)")
                return False

            # Check for NaN/inf values
            if torch.isnan(graph.x).any() or torch.isinf(graph.x).any():
                logger.error("NaN or Inf values in node features")
                return False

            if torch.isnan(graph.edge_attr).any() or torch.isinf(graph.edge_attr).any():
                logger.error("NaN or Inf values in edge features")
                return False

            if torch.isnan(graph.y).any() or torch.isinf(graph.y).any():
                logger.error("NaN or Inf values in targets")
                return False

            return True

        except Exception as e:
            logger.error(f"Graph validation failed: {e}")
            return False