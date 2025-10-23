"""
Feature normalization for stable training.
"""

import numpy as np
import torch
from typing import List, Dict, Any, Optional

from .utils import save_json_file, load_json_file, compute_statistics
from src import get_logger

logger = get_logger(__name__)


class FeatureNormalizer:
    """Normalize features to zero mean and unit variance."""

    def __init__(self):
        self.node_mean: Optional[np.ndarray] = None
        self.node_std: Optional[np.ndarray] = None
        self.edge_mean: Optional[np.ndarray] = None
        self.edge_std: Optional[np.ndarray] = None
        self.target_mean: Optional[np.ndarray] = None
        self.target_std: Optional[np.ndarray] = None

        self.fitted = False

    def fit(self, graphs: List[Any]) -> None:
        """
        Compute mean and std from dataset.

        Args:
            graphs: List of PyTorch Geometric Data objects or dicts
        """
        if not graphs:
            raise ValueError("Empty graph list")

        logger.info(f"Fitting normalizer on {len(graphs)} graphs")

        # Collect all features
        node_features = []
        edge_features = []
        targets = []

        for graph in graphs:
            if hasattr(graph, 'x'):  # PyTorch Geometric Data object
                node_features.append(graph.x.numpy())
                edge_features.append(graph.edge_attr.numpy())
                targets.append(graph.y.numpy())
            elif isinstance(graph, dict):  # Dict format
                node_features.append(graph['x'])
                edge_features.append(graph['edge_attr'])
                targets.append(graph['y'])
            else:
                raise ValueError(f"Unsupported graph format: {type(graph)}")

        # Compute statistics
        self.node_mean, self.node_std = compute_statistics(node_features)
        self.edge_mean, self.edge_std = compute_statistics(edge_features)
        self.target_mean, self.target_std = compute_statistics(targets)

        self.fitted = True
        logger.info("Normalizer fitted successfully")

    def transform(self, graph: Any) -> Any:
        """
        Apply normalization to a single graph.

        Args:
            graph: PyTorch Geometric Data object or dict

        Returns:
            Normalized graph
        """
        if not self.fitted:
            raise ValueError("Normalizer must be fitted before transform")

        if hasattr(graph, 'x'):  # PyTorch Geometric Data object
            graph.x = torch.tensor(self._normalize_features(
                graph.x.numpy(), self.node_mean, self.node_std
            ), dtype=torch.float)
            graph.edge_attr = torch.tensor(self._normalize_features(
                graph.edge_attr.numpy(), self.edge_mean, self.edge_std
            ), dtype=torch.float)
            graph.y = torch.tensor(self._normalize_features(
                graph.y.numpy(), self.target_mean, self.target_std
            ), dtype=torch.float)
            return graph

        elif isinstance(graph, dict):  # Dict format
            graph['x'] = self._normalize_features(
                graph['x'], self.node_mean, self.node_std
            )
            graph['edge_attr'] = self._normalize_features(
                graph['edge_attr'], self.edge_mean, self.edge_std
            )
            graph['y'] = self._normalize_features(
                graph['y'], self.target_mean, self.target_std
            )
            return graph

        else:
            raise ValueError(f"Unsupported graph format: {type(graph)}")

    def inverse_transform_targets(self, normalized_targets: np.ndarray) -> np.ndarray:
        """
        Denormalize target predictions.

        Args:
            normalized_targets: Normalized target values

        Returns:
            Denormalized target values
        """
        if not self.fitted:
            raise ValueError("Normalizer must be fitted before inverse transform")

        return self._denormalize_features(
            normalized_targets, self.target_mean, self.target_std
        )

    def _normalize_features(self, features: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
        """Apply z-score normalization."""
        return (features - mean) / std

    def _denormalize_features(self, normalized_features: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
        """Denormalize z-score normalized features."""
        return normalized_features * std + mean

    def save_statistics(self, path: str) -> None:
        """
        Save normalization parameters to file.

        Args:
            path: Path to save statistics JSON
        """
        if not self.fitted:
            raise ValueError("Normalizer must be fitted before saving")

        stats = {
            'node_features': {
                'mean': self.node_mean.tolist(),
                'std': self.node_std.tolist()
            },
            'edge_features': {
                'mean': self.edge_mean.tolist(),
                'std': self.edge_std.tolist()
            },
            'targets': {
                'mean': self.target_mean.tolist(),
                'std': self.target_std.tolist()
            }
        }

        save_json_file(stats, path)
        logger.info(f"Normalization statistics saved to {path}")

    def load_statistics(self, path: str) -> None:
        """
        Load normalization parameters from file.

        Args:
            path: Path to statistics JSON file
        """
        stats = load_json_file(path)

        self.node_mean = np.array(stats['node_features']['mean'])
        self.node_std = np.array(stats['node_features']['std'])
        self.edge_mean = np.array(stats['edge_features']['mean'])
        self.edge_std = np.array(stats['edge_features']['std'])
        self.target_mean = np.array(stats['targets']['mean'])
        self.target_std = np.array(stats['targets']['std'])

        self.fitted = True
        logger.info(f"Normalization statistics loaded from {path}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get current normalization statistics."""
        if not self.fitted:
            raise ValueError("Normalizer not fitted")

        return {
            'node_features': {
                'mean': self.node_mean,
                'std': self.node_std
            },
            'edge_features': {
                'mean': self.edge_mean,
                'std': self.edge_std
            },
            'targets': {
                'mean': self.target_mean,
                'std': self.target_std
            }
        }

    def __repr__(self) -> str:
        if self.fitted:
            return (f"FeatureNormalizer(fitted=True, "
                   f"node_dim={len(self.node_mean)}, "
                   f"edge_dim={len(self.edge_mean)}, "
                   f"target_dim={len(self.target_mean)})")
        else:
            return "FeatureNormalizer(fitted=False)"