"""
Utility functions for graph conversion module.
"""

import os
import json
import numpy as np
from typing import Dict, List, Tuple, Any
from pathlib import Path

from src import get_logger

logger = get_logger(__name__)


def ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load JSON file with error handling."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        raise


def save_json_file(data: Dict[str, Any], filepath: str, indent: int = 2) -> None:
    """Save data to JSON file."""
    ensure_dir(os.path.dirname(filepath))
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=indent, default=str)


def format_composition(x: float) -> str:
    """Format composition value for filenames."""
    return f"{x:.3f}"


def parse_composition(filename: str) -> float:
    """Extract composition from filename."""
    # Extract x value from patterns like "AlGaAs_x0.250" or "x0.250"
    import re
    match = re.search(r'x(\d+\.\d+)', filename)
    if match:
        return float(match.group(1))
    raise ValueError(f"Could not parse composition from filename: {filename}")


def get_bond_type(atom1: str, atom2: str) -> int:
    """Encode bond type as integer."""
    bond_types = {
        ('Al', 'As'): 0,
        ('Ga', 'As'): 1,
        ('Al', 'Al'): 2,
        ('Ga', 'Ga'): 3,
        ('As', 'As'): 4,
    }

    # Sort atoms to handle both directions
    atoms = tuple(sorted([atom1, atom2]))
    return bond_types.get(atoms, -1)  # -1 for unknown bonds


def compute_angle_factor(pos1: np.ndarray, pos2: np.ndarray, pos3: np.ndarray) -> float:
    """Compute angle factor for tetrahedral coordination."""
    v1 = pos2 - pos1
    v2 = pos3 - pos1

    # Compute norms
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    # Handle zero-length vectors (parallel or overlapping atoms)
    if norm1 < 1e-10 or norm2 < 1e-10:
        return 0.0  # Return 0 for degenerate cases
    
    # Compute cosine of angle with safe division
    cos_angle = np.dot(v1, v2) / (norm1 * norm2)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)  # Handle numerical precision issues

    # Ideal tetrahedral angle is 109.47 degrees
    ideal_cos = np.cos(np.radians(109.47))
    return abs(cos_angle - ideal_cos)


def validate_graph_data(graph_data: Dict[str, Any]) -> bool:
    """Validate graph data structure."""
    required_keys = ['x', 'edge_index', 'edge_attr', 'y', 'composition', 'structure_type']

    for key in required_keys:
        if key not in graph_data:
            logger.error(f"Missing required key: {key}")
            return False

    # Check tensor shapes
    if graph_data['x'].shape[1] != 10:  # 10 node features
        logger.error(f"Invalid node features shape: {graph_data['x'].shape}")
        return False

    if graph_data['edge_attr'].shape[1] != 4:  # 4 edge features
        logger.error(f"Invalid edge features shape: {graph_data['edge_attr'].shape}")
        return False

    if len(graph_data['y']) != 20:  # 20 target properties
        logger.error(f"Invalid targets shape: {len(graph_data['y'])}")
        return False

    return True


def get_atomic_properties() -> Dict[str, Dict[str, float]]:
    """Get atomic properties for common semiconductor elements."""
    return {
        'Al': {
            'atomic_number': 13,
            'valence_electrons': 3,
            'atomic_radius': 1.18,  # Å
            'electronegativity': 1.61,
            'group': 13,
            'period': 3
        },
        'Ga': {
            'atomic_number': 31,
            'valence_electrons': 3,
            'atomic_radius': 1.36,
            'electronegativity': 1.81,
            'group': 13,
            'period': 4
        },
        'As': {
            'atomic_number': 33,
            'valence_electrons': 5,
            'atomic_radius': 1.19,
            'electronegativity': 2.18,
            'group': 15,
            'period': 4
        }
    }


def safe_divide(a: np.ndarray, b: np.ndarray, default: float = 0.0) -> np.ndarray:
    """Safe division that handles division by zero."""
    with np.errstate(divide='ignore', invalid='ignore'):
        result = np.true_divide(a, b)
        result[~np.isfinite(result)] = default
    return result


def normalize_features(features: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    """Apply z-score normalization."""
    return safe_divide(features - mean, std)


def denormalize_features(normalized_features: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    """Denormalize z-score normalized features."""
    return normalized_features * std + mean


def compute_statistics(data_list: List[np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
    """Compute mean and std from list of arrays."""
    if not data_list:
        raise ValueError("Empty data list")

    concatenated = np.concatenate(data_list, axis=0)
    mean = np.mean(concatenated, axis=0)
    std = np.std(concatenated, axis=0)

    # Avoid division by zero
    std = np.where(std == 0, 1.0, std)

    return mean, std