"""
Graph visualization utilities.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import List
from pathlib import Path
import seaborn as sns
from torch_geometric.data import Data

from src import get_logger

logger = get_logger(__name__)


class GraphVisualizer:
    """Visualization utilities for crystal graphs."""

    def __init__(self, output_dir: str = "data/outputs/graphs/visualizations"):
        """
        Initialize visualizer.

        Args:
            output_dir: Directory to save visualizations
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set up matplotlib style
        plt.style.use('default')
        sns.set_palette("husl")

    def visualize_graph_structure(self, graph: Data, composition: float,
                                structure_type: str, save: bool = True) -> None:
        """
        Create 3D visualization of graph structure.

        Args:
            graph: PyTorch Geometric Data object
            composition: Composition value
            structure_type: "original" or "relaxed"
            save: Whether to save the plot
        """
        try:
            fig = plt.figure(figsize=(12, 8))
            ax = fig.add_subplot(111, projection='3d')

            # Extract node positions (fractional coordinates)
            frac_positions = graph.x[:, 1:4].numpy()  # x, y, z fractional (0-1)
            
            # Get atomic numbers for coloring and labeling
            atomic_numbers = graph.x[:, 0].numpy()
            
            # Map atomic numbers to element names
            atom_map = {13: 'Al', 31: 'Ga', 33: 'As'}
            
            # Get unique elements
            unique_atoms = np.unique(atomic_numbers)
            colors = plt.cm.Set1(np.linspace(0, 1, len(unique_atoms)))
            atom_colors = {atom: colors[i] for i, atom in enumerate(unique_atoms)}

            # Plot nodes with proper element labels
            for atom_num in unique_atoms:
                mask = atomic_numbers == atom_num
                element_name = atom_map.get(int(atom_num), f'Atom {int(atom_num)}')
                
                ax.scatter(frac_positions[mask, 0], 
                          frac_positions[mask, 1], 
                          frac_positions[mask, 2],
                          c=[atom_colors[atom_num]], 
                          s=200, 
                          alpha=0.8,
                          label=element_name,
                          edgecolors='black',
                          linewidths=1.5)

            # Plot edges
            edge_index = graph.edge_index.numpy()
            for i in range(0, edge_index.shape[1], 2):  # Skip duplicate edges
                start_idx = edge_index[0, i]
                end_idx = edge_index[1, i]
                start_pos = frac_positions[start_idx]
                end_pos = frac_positions[end_idx]

                ax.plot([start_pos[0], end_pos[0]],
                       [start_pos[1], end_pos[1]],
                       [start_pos[2], end_pos[2]],
                       'gray', alpha=0.3, linewidth=1)

            ax.set_xlabel('X (fractional)')
            ax.set_ylabel('Y (fractional)')
            ax.set_zlabel('Z (fractional)')
            ax.set_title(f'Crystal Graph Structure\nAl$_x$Ga$_{{1-x}}$As x={composition:.3f} ({structure_type})')
            ax.legend(loc='upper right', fontsize=10)
            
            # Set equal aspect ratio
            max_range = 1.0  # Fractional coords are 0-1
            ax.set_xlim([0, max_range])
            ax.set_ylim([0, max_range])
            ax.set_zlim([0, max_range])

            plt.tight_layout()

            if save:
                filename = f"graph_structure_x{composition:.3f}_{structure_type}.png"
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=300, bbox_inches='tight')
                logger.info(f"Saved graph structure visualization to {filepath}")

            plt.close()

        except Exception as e:
            logger.error(f"Failed to create graph structure visualization: {e}")
            import traceback
            logger.error(traceback.format_exc())
            plt.close()

    def plot_feature_distributions(self, graphs: List[Data], save: bool = True) -> None:
        """
        Plot distributions of node and edge features.

        Args:
            graphs: List of graph data objects
            save: Whether to save the plot
        """
        if not graphs:
            logger.warning("No graphs provided for feature distribution plotting")
            return

        try:
            # Collect all features
            node_features = []
            edge_features = []

            for graph in graphs:
                node_features.append(graph.x.numpy())
                edge_features.append(graph.edge_attr.numpy())

            node_features = np.concatenate(node_features, axis=0)
            edge_features = np.concatenate(edge_features, axis=0)

            # Node feature names
            node_feature_names = [
                'Atomic Number', 'X Coord', 'Y Coord', 'Z Coord',
                'Coordination', 'Valence Electrons', 'Atomic Radius',
                'Electronegativity', 'Group', 'Period'
            ]

            # Edge feature names
            edge_feature_names = [
                'Distance', 'Distance Norm', 'Bond Type', 'Angle Factor'
            ]

            # Create subplots
            fig, axes = plt.subplots(2, 5, figsize=(20, 10))
            axes = axes.flatten()

            # Plot node features
            for i in range(min(10, node_features.shape[1])):
                axes[i].hist(node_features[:, i], bins=30, alpha=0.7, edgecolor='black')
                axes[i].set_title(f'Node: {node_feature_names[i]}')
                axes[i].set_xlabel('Value')
                axes[i].set_ylabel('Frequency')

            plt.tight_layout()

            if save:
                filepath = self.output_dir / "feature_distribution.png"
                plt.savefig(filepath, dpi=300, bbox_inches='tight')
                logger.info(f"Saved feature distribution plot to {filepath}")

            plt.close()

            # Plot edge features separately
            fig, axes = plt.subplots(1, 4, figsize=(16, 4))

            for i in range(min(4, edge_features.shape[1])):
                axes[i].hist(edge_features[:, i], bins=30, alpha=0.7, edgecolor='black')
                axes[i].set_title(f'Edge: {edge_feature_names[i]}')
                axes[i].set_xlabel('Value')
                axes[i].set_ylabel('Frequency')

            plt.tight_layout()

            if save:
                filepath = self.output_dir / "edge_feature_distribution.png"
                plt.savefig(filepath, dpi=300, bbox_inches='tight')
                logger.info(f"Saved edge feature distribution plot to {filepath}")

            plt.close()

        except Exception as e:
            logger.error(f"Failed to create feature distribution plots: {e}")
            plt.close()

    def plot_target_correlation(self, graphs: List[Data], property_names: List[str],
                              save: bool = True) -> None:
        """
        Plot correlation matrix of target properties.

        Args:
            graphs: List of graph data objects
            property_names: Names of target properties
            save: Whether to save the plot
        """
        if not graphs:
            logger.warning("No graphs provided for correlation plotting")
            return

        try:
            # Collect all targets
            targets = []
            for graph in graphs:
                targets.append(graph.y.numpy())
            targets = np.array(targets)

            # Compute correlation matrix
            corr_matrix = np.corrcoef(targets.T)

            # Create heatmap
            plt.figure(figsize=(12, 10))
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
            sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='coolwarm',
                       xticklabels=property_names, yticklabels=property_names,
                       center=0, square=True, linewidths=0.5)

            plt.title('Target Property Correlation Matrix')
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)
            plt.tight_layout()

            if save:
                filepath = self.output_dir / "target_correlation.png"
                plt.savefig(filepath, dpi=300, bbox_inches='tight')
                logger.info(f"Saved target correlation plot to {filepath}")

            plt.close()

        except Exception as e:
            logger.error(f"Failed to create target correlation plot: {e}")
            plt.close()

    def create_summary_visualizations(self, graphs: List[Data],
                                    property_names: List[str]) -> None:
        """
        Create all summary visualizations.

        Args:
            graphs: List of graph data objects
            property_names: Names of target properties
        """
        logger.info("Creating summary visualizations...")

        # Feature distributions
        self.plot_feature_distributions(graphs)

        # Target correlations
        self.plot_target_correlation(graphs, property_names)

        # Individual graph structures (first few)
        for i, graph in enumerate(graphs):  # Visualize first 3 graphs
            composition = getattr(graph, 'composition', 0.0)
            structure_type = getattr(graph, 'structure_type', 'unknown')
            self.visualize_graph_structure(graph, composition, structure_type)

        logger.info("Summary visualizations completed")

    def plot_graph_statistics(self, graphs: List[Data], save: bool = True) -> None:
        """
        Plot statistics about the graph dataset.

        Args:
            graphs: List of graph data objects
            save: Whether to save the plot
        """
        if not graphs:
            return

        try:
            # Collect statistics
            num_nodes = [g.num_nodes for g in graphs]
            num_edges = [g.edge_index.shape[1] for g in graphs]
            compositions = [getattr(g, 'composition', 0.0) for g in graphs]

            fig, axes = plt.subplots(2, 2, figsize=(12, 10))

            # Nodes per graph
            axes[0, 0].hist(num_nodes, bins=20, alpha=0.7, edgecolor='black')
            axes[0, 0].set_title('Nodes per Graph')
            axes[0, 0].set_xlabel('Number of Nodes')
            axes[0, 0].set_ylabel('Frequency')

            # Edges per graph
            axes[0, 1].hist(num_edges, bins=20, alpha=0.7, edgecolor='black')
            axes[0, 1].set_title('Edges per Graph')
            axes[0, 1].set_xlabel('Number of Edges')
            axes[0, 1].set_ylabel('Frequency')

            # Composition distribution
            axes[1, 0].hist(compositions, bins=20, alpha=0.7, edgecolor='black')
            axes[1, 0].set_title('Composition Distribution')
            axes[1, 0].set_xlabel('Composition (x)')
            axes[1, 0].set_ylabel('Frequency')

            # Nodes vs Edges scatter
            axes[1, 1].scatter(num_nodes, num_edges, alpha=0.6)
            axes[1, 1].set_title('Nodes vs Edges')
            axes[1, 1].set_xlabel('Number of Nodes')
            axes[1, 1].set_ylabel('Number of Edges')

            plt.tight_layout()

            if save:
                filepath = self.output_dir / "graph_statistics.png"
                plt.savefig(filepath, dpi=300, bbox_inches='tight')
                logger.info(f"Saved graph statistics plot to {filepath}")

            plt.close()

        except Exception as e:
            logger.error(f"Failed to create graph statistics plot: {e}")
            plt.close()