"""
PyTorch Dataset for material property prediction.
"""

import torch
from torch.utils.data import Dataset
import glob
from typing import List, Tuple, Dict, Any
from pathlib import Path

from .normalizer import FeatureNormalizer
from .utils import load_json_file
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MaterialPropertyDataset(Dataset):
    """PyTorch Dataset for material property prediction."""

    def __init__(self, graph_dir: str, normalize: bool = True, preload: bool = True):
        """
        Initialize dataset.

        Args:
            graph_dir: Directory containing graph files
            normalize: Whether to apply normalization
            preload: Whether to preload all graphs into memory
        """
        self.graph_dir = Path(graph_dir)
        self.normalize = normalize
        self.preload = preload

        # Find all graph files
        self.graph_files = self._find_graph_files()
        logger.info(f"Found {len(self.graph_files)} graph files")

        # Load dataset info
        self.dataset_info = self._load_dataset_info()

        # Load normalization statistics
        self.normalizer = None
        if self.normalize:
            self.normalizer = FeatureNormalizer()
            stats_file = self.graph_dir / "statistics" / "node_feature_stats.json"
            if stats_file.exists():
                # Load from separate files or combined stats
                try:
                    self.normalizer.load_statistics(str(self.graph_dir / "statistics" / "normalization_stats.json"))
                except FileNotFoundError:
                    logger.warning("Normalization stats not found, features will not be normalized")
                    self.normalize = False

        # Preload graphs if requested
        self.graphs = []
        if self.preload:
            self._preload_graphs()

    def _find_graph_files(self) -> List[Path]:
        """Find all .pt graph files in the directory."""
        pattern = str(self.graph_dir / "graphs" / "*.pt")
        files = glob.glob(pattern)
        return [Path(f) for f in sorted(files)]

    def _load_dataset_info(self) -> Dict[str, Any]:
        """Load dataset metadata."""
        info_file = self.graph_dir / "dataset_info.json"
        if info_file.exists():
            return load_json_file(str(info_file))
        else:
            logger.warning(f"Dataset info file not found: {info_file}")
            return {}

    def _preload_graphs(self) -> None:
        """Preload all graphs into memory."""
        logger.info("Preloading graphs...")
        for filepath in self.graph_files:
            try:
                graph = torch.load(filepath)
                self.graphs.append(graph)
            except Exception as e:
                logger.error(f"Failed to load graph {filepath}: {e}")
        logger.info(f"Preloaded {len(self.graphs)} graphs")

    def __len__(self) -> int:
        """Return dataset size."""
        if self.preload:
            return len(self.graphs)
        else:
            return len(self.graph_files)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Return (graph, target_properties).

        Args:
            idx: Index of the sample

        Returns:
            Tuple of (graph_data, target_properties)
        """
        if self.preload:
            graph = self.graphs[idx]
        else:
            try:
                graph = torch.load(self.graph_files[idx])
            except Exception as e:
                logger.error(f"Failed to load graph {self.graph_files[idx]}: {e}")
                raise

        # Apply normalization if available
        if self.normalize and self.normalizer and self.normalizer.fitted:
            graph = self.normalizer.transform(graph)

        return graph, graph.y

    def get_graph_info(self, idx: int) -> Dict[str, Any]:
        """
        Get information about a specific graph.

        Args:
            idx: Graph index

        Returns:
            Dictionary with graph metadata
        """
        graph = self[idx][0]  # Get the graph data
        return {
            'composition': graph.composition,
            'structure_type': graph.structure_type,
            'num_nodes': graph.num_nodes,
            'num_edges': graph.edge_index.shape[1],
            'filename': str(self.graph_files[idx]) if not self.preload else f"preloaded_{idx}"
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Return normalization statistics."""
        if self.normalizer and self.normalizer.fitted:
            return self.normalizer.get_statistics()
        else:
            return {}

    def get_property_names(self) -> List[str]:
        """Return list of target property names."""
        return [
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

    def filter_by_composition(self, min_x: float = None, max_x: float = None) -> 'MaterialPropertyDataset':
        """
        Create a filtered dataset by composition range.

        Args:
            min_x: Minimum composition value
            max_x: Maximum composition value

        Returns:
            New filtered dataset
        """
        filtered_files = []
        for filepath in self.graph_files:
            # Extract composition from filename
            filename = filepath.stem  # e.g., "AlGaAs_x0.250_original"
            try:
                x_value = float(filename.split('_x')[1].split('_')[0])
                if ((min_x is None or x_value >= min_x) and
                    (max_x is None or x_value <= max_x)):
                    filtered_files.append(filepath)
            except (IndexError, ValueError):
                continue

        # Create new dataset with filtered files
        new_dataset = MaterialPropertyDataset.__new__(MaterialPropertyDataset)
        new_dataset.graph_dir = self.graph_dir
        new_dataset.normalize = self.normalize
        new_dataset.preload = False  # Don't preload for filtered datasets
        new_dataset.graph_files = filtered_files
        new_dataset.dataset_info = self.dataset_info
        new_dataset.normalizer = self.normalizer
        new_dataset.graphs = []  # Empty since not preloading

        return new_dataset

    def filter_by_structure_type(self, structure_type: str) -> 'MaterialPropertyDataset':
        """
        Create a filtered dataset by structure type.

        Args:
            structure_type: "original" or "relaxed"

        Returns:
            New filtered dataset
        """
        filtered_files = [
            f for f in self.graph_files
            if structure_type in f.stem
        ]

        # Create new dataset with filtered files
        new_dataset = MaterialPropertyDataset.__new__(MaterialPropertyDataset)
        new_dataset.graph_dir = self.graph_dir
        new_dataset.normalize = self.normalize
        new_dataset.preload = False
        new_dataset.graph_files = filtered_files
        new_dataset.dataset_info = self.dataset_info
        new_dataset.normalizer = self.normalizer
        new_dataset.graphs = []

        return new_dataset

    def __repr__(self) -> str:
        return (f"MaterialPropertyDataset("
               f"size={len(self)}, "
               f"normalize={self.normalize}, "
               f"preload={self.preload}, "
               f"dir={self.graph_dir})")