"""
Main pipeline for graph conversion.
"""

import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from pymatgen.io.cif import CifParser

from .graph_builder import CrystalGraphBuilder
from .visualizer import GraphVisualizer
from .utils import load_json_file, save_json_file, ensure_dir
from src import get_logger

logger = get_logger(__name__)


class GraphConversionPipeline:
    """Main pipeline for converting crystal structures to graphs."""

    def __init__(self, structure_dir: str, properties_file: str, output_dir: str,
                 cutoff_radius: float = 5.0, use_both_structures: bool = True):
        """
        Initialize pipeline.

        Args:
            structure_dir: Directory containing CIF files
            properties_file: Path to properties JSON file
            output_dir: Output directory for graphs
            cutoff_radius: Radius for edge connections
            use_both_structures: Whether to process both original and relaxed structures
        """
        self.structure_dir = Path(structure_dir)
        self.properties_file = Path(properties_file)
        self.output_dir = Path(output_dir)
        self.cutoff_radius = cutoff_radius
        self.use_both_structures = use_both_structures

        # Create subdirectories
        self.graphs_dir = self.output_dir / "graphs"
        self.stats_dir = self.output_dir / "statistics"
        self.viz_dir = self.output_dir / "visualizations"

        ensure_dir(self.graphs_dir)
        ensure_dir(self.stats_dir)
        ensure_dir(self.viz_dir)

        # Initialize components
        self.graph_builder = CrystalGraphBuilder(cutoff_radius=cutoff_radius)
        self.visualizer = GraphVisualizer(str(self.viz_dir))

        # Data storage
        self.properties_data = {}
        self.generated_graphs = []
        self.charge_density_available = False

    def convert_all(self) -> None:
        """Convert all available structures to graphs."""
        logger.info("Starting graph conversion pipeline...")

        # Load properties
        self._load_properties()

        # Find all structure files
        structure_files = self._find_structure_files()
        logger.info(f"Found {len(structure_files)} structure files")

        # Convert each structure
        for filepath in structure_files:
            try:
                self._convert_single_structure(filepath)
            except Exception as e:
                logger.error(f"Failed to convert {filepath}: {e}")
                continue

        logger.info(f"Converted {len(self.generated_graphs)} structures to graphs")

    def _load_properties(self) -> None:
        """Load material properties from JSON file."""
        try:
            self.properties_data = load_json_file(str(self.properties_file))
            logger.info(f"Loaded properties for {len(self.properties_data)} compositions")

            # Check if charge density data is available
            self._check_charge_density_availability()

        except Exception as e:
            logger.error(f"Failed to load properties file: {e}")
            raise

    def _check_charge_density_availability(self) -> None:
        """Check if charge density data is available in the structures."""
        # First check if charge density was enabled in config
        try:
            from src.utils import get_config
            config = get_config()
            charge_density_enabled = config.get('features.enable_charge_density', False)
            if not charge_density_enabled:
                logger.info("Charge density feature is disabled in config")
                return
        except Exception as e:
            logger.warning(f"Could not load config to check charge density setting: {e}")
            charge_density_enabled = False

        # Look for charge density files or metadata in structure directories
        import os
        for root, dirs, files in os.walk(self.structure_dir):
            for file in files:
                if 'charge' in file.lower() or 'chgcar' in file.lower():
                    self.charge_density_available = True
                    logger.info("Charge density data detected in input structures")
                    return

        # Also check metadata files for charge density information
        for root, dirs, files in os.walk(self.structure_dir):
            for file in files:
                if file.endswith('.json'):
                    try:
                        metadata = load_json_file(os.path.join(root, file))
                        if 'charge_density' in metadata or 'has_charge_density' in metadata:
                            self.charge_density_available = True
                            logger.info("Charge density metadata detected in input structures")
                            return
                    except:
                        continue

        # Check if CHGCAR files exist in the data directory for the materials
        try:
            # Try to determine the materials from the properties file
            if self.properties_data and 'metadata' in self.properties_data:
                alloy_system = self.properties_data['metadata'].get('alloy_system', 'AlGaAs')
                if alloy_system == 'AlGaAs':
                    # Check for CHGCAR files for GaAs and AlAs
                    data_dir = Path("data")
                    gaas_chgcar = data_dir / "mp-2534" / "mp-2534_CHGCAR.vasp"
                    alas_chgcar = data_dir / "mp-2172" / "mp-2172_CHGCAR.vasp"
                    if gaas_chgcar.exists() and alas_chgcar.exists():
                        self.charge_density_available = True
                        logger.info("Charge density data detected in data directory")
                        return
        except Exception as e:
            logger.warning(f"Could not check data directory for CHGCAR files: {e}")

        # If charge density was enabled in config but we didn't find evidence of it being used
        if charge_density_enabled:
            logger.info("Charge density feature is enabled in config but no data detected")
        else:
            logger.info("No charge density data detected in input structures")

    def _find_structure_files(self) -> List[Path]:
        """Find all CIF structure files."""
        import os
        cif_files = []

        # Look for CIF files in subdirectories
        for root, dirs, files in os.walk(self.structure_dir):
            for file in files:
                if file.endswith('.cif'):
                    cif_files.append(Path(root) / file)

        return sorted(cif_files)

    def _convert_single_structure(self, filepath: Path) -> None:
        """Convert a single structure file to graph."""
        # Parse filename to extract composition and structure type
        filename = filepath.stem  # e.g., "AlGaAs_x0.250" or "AlGaAs_x0.250_relaxed"

        # Extract composition
        if '_x' in filename:
            composition_str = filename.split('_x')[1].split('_')[0]
            composition = float(composition_str)
        else:
            logger.warning(f"Could not parse composition from {filename}")
            return

        # Determine structure type
        if 'relaxed' in filename:
            structure_type = 'relaxed'
        else:
            structure_type = 'original'

        # Skip if we don't want both structures
        if not self.use_both_structures and structure_type == 'relaxed':
            return

        logger.info(f"Converting {filename} (x={composition}, type={structure_type})")

        # Load structure
        try:
            parser = CifParser(str(filepath))
            # The CIF files already contain the correct supercell structures (16 atoms for 2x2x2)
            structure = parser.get_structures(primitive=False)[0]
            
        except Exception as e:
            logger.error(f"Failed to parse CIF file {filepath}: {e}")
            return

        # Get properties for this composition
        # Try different key formats since the JSON might use different precision
        compositions_data = self.properties_data.get('compositions', {})

        # Try different key formats
        possible_keys = [
            f"x_{composition:.3f}",  # Format: x_0.000
            f"x{composition:.3f}",    # Format: x0.000
            f"x_{composition:.1f}",  # Format: x_0.0
            f"x{composition:.1f}",    # Format: x0.0
        ]

        properties = None
        for comp_key in possible_keys:
            if comp_key in compositions_data:
                properties = compositions_data[comp_key]['properties']
                logger.debug(f"Found properties for {filename} using key '{comp_key}'")
                break

        if properties is None:
            logger.warning(f"No properties found for composition {composition} (available: {list(compositions_data.keys())})")
            return

        # Convert to graph
        try:
            # Check if charge density data is available for this composition
            per_atom_charge_density = None
            if self.charge_density_available:
                # Try to load charge density data from metadata
                metadata_file = filepath.parent / f"{filepath.stem}.json"
                if metadata_file.exists():
                    try:
                        metadata = load_json_file(str(metadata_file))
                        if 'per_atom_charge_density' in metadata:
                            per_atom_charge_density = np.array(metadata['per_atom_charge_density'])
                            logger.debug(f"Loaded charge density data for {filename}")
                    except Exception as e:
                        logger.warning(f"Could not load charge density from metadata: {e}")

            graph = self.graph_builder.structure_to_graph(
                structure, properties, composition, structure_type, per_atom_charge_density
            )

            # Validate graph
            if not self.graph_builder.validate_graph(graph):
                logger.error(f"Graph validation failed for {filename}")
                return

            # Save graph
            output_filename = f"AlGaAs_x{composition:.3f}_{structure_type}.pt"
            output_path = self.graphs_dir / output_filename

            import torch
            torch.save(graph, str(output_path), _use_new_zipfile_serialization=False)

            self.generated_graphs.append(graph)
            logger.info(f"Saved graph to {output_path}")

        except Exception as e:
            logger.error(f"Failed to convert structure {filename}: {e}")

    def compute_statistics(self) -> None:
        """Compute and save normalization statistics."""
        if not self.generated_graphs:
            logger.warning("No graphs available for statistics computation")
            return

        logger.info("Computing normalization statistics...")

        # Fit normalizer
        self.graph_builder.fit_normalizer(self.generated_graphs)

        # Save statistics
        stats_path = self.stats_dir / "normalization_stats.json"
        if self.graph_builder.normalizer:
            self.graph_builder.normalizer.save_statistics(str(stats_path))

        # Compute additional statistics
        self._compute_dataset_statistics()

    def _compute_dataset_statistics(self) -> None:
        """Compute comprehensive dataset statistics."""
        if not self.generated_graphs:
            return

        stats = {
            'node_features': {},
            'edge_features': {},
            'targets': {},
            'graph_properties': {}
        }

        # Collect all features
        all_node_features = []
        all_edge_features = []
        all_targets = []
        graph_props = []

        for graph in self.generated_graphs:
            all_node_features.append(graph.x.numpy())
            all_edge_features.append(graph.edge_attr.numpy())
            all_targets.append(graph.y.numpy())

            graph_props.append({
                'num_nodes': graph.num_nodes,
                'num_edges': graph.edge_index.shape[1],
                'composition': graph.composition,
                'structure_type': graph.structure_type
            })

        node_concat = np.concatenate(all_node_features, axis=0)
        edge_concat = np.concatenate(all_edge_features, axis=0)
        target_concat = np.array(all_targets)

        stats['node_features'] = {
            'mean': node_concat.mean(axis=0).tolist(),
            'std': node_concat.std(axis=0).tolist(),
            'min': node_concat.min(axis=0).tolist(),
            'max': node_concat.max(axis=0).tolist()
        }

        stats['edge_features'] = {
            'mean': edge_concat.mean(axis=0).tolist(),
            'std': edge_concat.std(axis=0).tolist(),
            'min': edge_concat.min(axis=0).tolist(),
            'max': edge_concat.max(axis=0).tolist()
        }

        stats['targets'] = {
            'mean': target_concat.mean(axis=0).tolist(),
            'std': target_concat.std(axis=0).tolist(),
            'min': target_concat.min(axis=0).tolist(),
            'max': target_concat.max(axis=0).tolist()
        }

        stats['graph_properties'] = {
            'total_graphs': len(self.generated_graphs),
            'avg_nodes_per_graph': np.mean([p['num_nodes'] for p in graph_props]),
            'avg_edges_per_graph': np.mean([p['num_edges'] for p in graph_props]),
            'compositions': sorted(list(set(p['composition'] for p in graph_props))),
            'structure_types': sorted(list(set(p['structure_type'] for p in graph_props)))
        }

        # Save statistics
        stats_file = self.stats_dir / "dataset_statistics.json"
        save_json_file(stats, str(stats_file))
        logger.info(f"Saved dataset statistics to {stats_file}")

    def create_visualizations(self) -> None:
        """Create visualization plots."""
        if not self.generated_graphs:
            logger.warning("No graphs available for visualization")
            return

        logger.info("Creating visualizations...")

        # Get property names
        property_names = [
            'lattice_constant', 'band_gap', 'band_gap_type', 'electron_affinity',
            'effective_mass_electron', 'effective_mass_hole_heavy', 'effective_mass_hole_light',
            'dielectric_constant_static', 'dielectric_constant_high_freq', 'refractive_index',
            'bulk_modulus', 'shear_modulus', 'youngs_modulus', 'poissons_ratio',
            'elastic_constant_c11', 'elastic_constant_c12', 'elastic_constant_c44',
            'electron_mobility', 'hole_mobility', 'thermal_conductivity'
        ]

        # Create visualizations
        self.visualizer.create_summary_visualizations(self.generated_graphs, property_names)
        self.visualizer.plot_graph_statistics(self.generated_graphs)

    def save_dataset_info(self) -> None:
        """Save comprehensive dataset metadata."""
        info = {
            'dataset_name': 'AlGaAs_PropertyPrediction',
            'version': '1.0.0',
            'created_at': datetime.now().isoformat(),
            'num_graphs': len(self.generated_graphs),
            'num_compositions': len(set(g.composition for g in self.generated_graphs)),
            'compositions': sorted(list(set(g.composition for g in self.generated_graphs))),
            'structure_types': sorted(list(set(g.structure_type for g in self.generated_graphs))),
            'graph_statistics': {
                'avg_nodes_per_graph': np.mean([g.num_nodes for g in self.generated_graphs]),
                'avg_edges_per_graph': np.mean([g.edge_index.shape[1] for g in self.generated_graphs]),
                'node_feature_dim': self.generated_graphs[0].x.shape[1] if self.generated_graphs else 0,
                'edge_feature_dim': self.generated_graphs[0].edge_attr.shape[1] if self.generated_graphs else 0,
                'target_dim': self.generated_graphs[0].y.shape[0] if self.generated_graphs else 0
            },
            'normalization': {
                'method': 'z_score',
                'applied': self.graph_builder.normalize
            },
            'source_files': {
                'structures': str(self.structure_dir),
                'properties': str(self.properties_file),
                'charge_density': 'enabled' if self.charge_density_available else 'disabled'
            },
            'configuration': {
                'cutoff_radius': self.cutoff_radius,
                'use_both_structures': self.use_both_structures
            }
        }

        # Add normalization stats if available
        if self.graph_builder.normalizer and self.graph_builder.normalizer.fitted:
            norm_stats = self.graph_builder.normalizer.get_statistics()
            info['normalization'].update(norm_stats)

        info_file = self.output_dir / "dataset_info.json"
        save_json_file(info, str(info_file))
        logger.info(f"Saved dataset info to {info_file}")

    def get_summary(self) -> Dict[str, Any]:
        """Get pipeline execution summary."""
        return {
            'total_graphs_converted': len(self.generated_graphs),
            'output_directory': str(self.output_dir),
            'graphs_directory': str(self.graphs_dir),
            'statistics_directory': str(self.stats_dir),
            'visualizations_directory': str(self.viz_dir),
            'normalization_applied': self.graph_builder.normalize,
            'cutoff_radius': self.cutoff_radius
        }