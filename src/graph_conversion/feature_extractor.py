"""
Feature extraction for crystal structures.
"""

import numpy as np
from typing import Tuple, Optional
from pymatgen.core import Structure

from .utils import get_atomic_properties, get_bond_type, compute_angle_factor
from src import get_logger

logger = get_logger(__name__)


class FeatureExtractor:
    """Extracts node and edge features from crystal structures."""

    def __init__(self, cutoff_radius: float = 5.0):
        """
        Initialize feature extractor.

        Args:
            cutoff_radius: Maximum distance for edge connections (Å)
        """
        self.cutoff_radius = cutoff_radius
        self.atomic_props = get_atomic_properties()

    def extract_node_features(self, structure: Structure, per_atom_charge_density: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Extract node features for each atom.

        Features (10-dim or 11-dim):
        0. atomic_number
        1. x_coord (fractional)
        2. y_coord (fractional)
        3. z_coord (fractional)
        4. coordination_number
        5. valence_electrons
        6. atomic_radius
        7. electronegativity
        8. group_number
        9. period_number
        10. charge_density (optional)

        Args:
            structure: pymatgen Structure object
            per_atom_charge_density: Optional array of charge density values per atom

        Returns:
            Node features array of shape [num_atoms, 11] (or [num_atoms, 10] if no charge density)
        """
        num_atoms = len(structure)
        include_charge_density = per_atom_charge_density is not None
        num_features = 11 if include_charge_density else 10
        features = np.zeros((num_atoms, num_features))

        # Get coordination numbers
        coord_nums = self._get_coordination_numbers(structure)

        for i, site in enumerate(structure):
            element = site.species_string

            if element not in self.atomic_props:
                logger.warning(f"Unknown element {element}, using default properties")
                props = {
                    'atomic_number': 0,
                    'valence_electrons': 0,
                    'atomic_radius': 1.0,
                    'electronegativity': 0,
                    'group': 0,
                    'period': 0
                }
            else:
                props = self.atomic_props[element]

            # Base features
            base_features = [
                props['atomic_number'],
                site.frac_coords[0],  # x fractional coordinate (0-1)
                site.frac_coords[1],  # y fractional coordinate (0-1)
                site.frac_coords[2],  # z fractional coordinate (0-1)
                coord_nums[i],        # coordination number
                props['valence_electrons'],
                props['atomic_radius'],
                props['electronegativity'],
                props['group'],
                props['period']
            ]

            if include_charge_density:
                # Add charge density as 11th feature
                charge_density_value = float(per_atom_charge_density[i]) if i < len(per_atom_charge_density) else 0.0
                features[i] = base_features + [charge_density_value]
            else:
                features[i] = base_features

        return features

    def extract_edge_features(self, structure: Structure) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract edge features and connectivity.

        Edge features (4-dim):
        0. distance
        1. distance_normalized
        2. bond_type
        3. angle_factor

        Args:
            structure: pymatgen Structure object

        Returns:
            Tuple of (edge_index, edge_features)
            edge_index: [2, num_edges] array of connected atom indices
            edge_features: [num_edges, 4] array of edge features
        """
        edge_index = []
        edge_features = []

        # Get all pairs within cutoff
        for i in range(len(structure)):
            for j in range(i + 1, len(structure)):
                site1, site2 = structure[i], structure[j]
                distance = structure.get_distance(i, j)

                if distance <= self.cutoff_radius:
                    # Add both directions for undirected graph
                    edge_index.extend([[i, j], [j, i]])

                    # Compute edge features
                    element1 = site1.species_string
                    element2 = site2.species_string

                    # Distance normalized by sum of covalent radii
                    radius1 = self.atomic_props.get(element1, {}).get('atomic_radius', 1.0)
                    radius2 = self.atomic_props.get(element2, {}).get('atomic_radius', 1.0)
                    distance_norm = distance / (radius1 + radius2)

                    # Bond type encoding
                    bond_type = get_bond_type(element1, element2)

                    # Angle factor (related to tetrahedral angle)
                    angle_factor = compute_angle_factor(
                        site1.coords, site2.coords,
                        # For tetrahedral structures, we could compute angle with central atom
                        # but this is a simplified version
                        np.array([0, 0, 0])  # Placeholder - would need proper implementation
                    )

                    features = [
                        distance,
                        distance_norm,
                        bond_type,
                        angle_factor
                    ]

                    edge_features.extend([features, features])  # Same for both directions

        edge_index = np.array(edge_index).T if edge_index else np.zeros((2, 0), dtype=int)
        edge_features = np.array(edge_features) if edge_features else np.zeros((0, 4))

        return edge_index, edge_features

    def _get_coordination_numbers(self, structure: Structure) -> np.ndarray:
        """Compute coordination numbers for each atom."""
        coord_nums = np.zeros(len(structure))

        for i, site in enumerate(structure):
            count = 0
            for j, other_site in enumerate(structure):
                if i != j:
                    distance = structure.get_distance(i, j)
                    if distance <= self.cutoff_radius:
                        count += 1
            coord_nums[i] = count

        return coord_nums

    def extract_all_features(self, structure: Structure, per_atom_charge_density: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extract all node and edge features.

        Args:
            structure: pymatgen Structure object
            per_atom_charge_density: Optional array of charge density values per atom

        Returns:
            Tuple of (node_features, edge_index, edge_features)
        """
        node_features = self.extract_node_features(structure, per_atom_charge_density)
        edge_index, edge_features = self.extract_edge_features(structure)

        return node_features, edge_index, edge_features