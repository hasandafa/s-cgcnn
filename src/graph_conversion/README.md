# Graph Conversion Module

The `src/graph_conversion/` module handles the conversion of crystal structures and material properties into graph representations suitable for Graph Neural Network (GNN) training. This module transforms structural data into PyTorch Geometric graphs with rich node and edge features.

## Overview

This module enables:
- **Crystal to Graph Conversion**: Transform pymatgen Structures into PyTorch Geometric Data objects
- **Feature Extraction**: Extract comprehensive node and edge features from crystal structures
- **Feature Normalization**: Standardize features for stable GNN training
- **Dataset Creation**: Build PyTorch Datasets for material property prediction
- **Visualization**: Generate plots and statistics for dataset analysis
- **Pipeline Orchestration**: End-to-end conversion from CIF files to normalized graphs

## Key Features

- **Rich Feature Sets**: 10-11 dimensional node features, 4-dimensional edge features
- **Charge Density Integration**: Optional per-atom charge density as node features
- **Normalization**: Z-score normalization for stable training
- **Batch Processing**: Efficient conversion of multiple structures
- **Validation**: Comprehensive graph structure validation
- **Visualization**: Dataset statistics and feature distribution plots

## Module Structure

### Core Files

| File | Purpose |
|------|---------|
| `pipeline.py` | Main pipeline for batch conversion from CIF to graphs |
| `graph_builder.py` | Core conversion from pymatgen Structures to PyTorch Geometric graphs |
| `feature_extractor.py` | Node and edge feature extraction from crystal structures |
| `normalizer.py` | Feature normalization and statistics computation |
| `dataset.py` | PyTorch Dataset class for material property prediction |
| `visualizer.py` | Visualization utilities for graphs and datasets |
| `utils.py` | Utility functions for feature computation and data handling |

### Key Classes

- **`GraphConversionPipeline`**: Orchestrates the complete conversion process
- **`CrystalGraphBuilder`**: Converts individual structures to graphs
- **`FeatureExtractor`**: Extracts node and edge features
- **`FeatureNormalizer`**: Normalizes features using training statistics
- **`MaterialPropertyDataset`**: PyTorch Dataset for GNN training
- **`GraphVisualizer`**: Creates plots and visualizations

## Quick Start

### Basic Conversion

```python
from src.graph_conversion import GraphConversionPipeline

# Initialize pipeline
pipeline = GraphConversionPipeline(
    structure_dir="data/outputs/calculations/structures",
    properties_file="data/outputs/calculations/properties.json",
    output_dir="data/outputs/graphs",
    cutoff_radius=5.0
)

# Convert all structures to graphs
pipeline.convert_all()

# Compute normalization statistics
pipeline.compute_statistics()

# Create visualizations
pipeline.create_visualizations()

# Save dataset metadata
pipeline.save_dataset_info()
```

### Individual Graph Creation

```python
from src.graph_conversion import CrystalGraphBuilder
from pymatgen.core import Structure

# Initialize builder
builder = CrystalGraphBuilder(cutoff_radius=5.0, normalize=True)

# Convert single structure
graph = builder.structure_to_graph(
    structure=structure,
    properties=properties_dict,
    composition=0.5,
    structure_type="original",
    per_atom_charge_density=charge_density_array
)

print(f"Graph: {graph.num_nodes} nodes, {graph.edge_index.shape[1]} edges")
```

## Feature Extraction

### Node Features (10-11 dimensions)

| Feature | Description | Range/Units |
|---------|-------------|-------------|
| 0 | Atomic number | 1-118 |
| 1 | Fractional x-coordinate | 0-1 |
| 2 | Fractional y-coordinate | 0-1 |
| 3 | Fractional z-coordinate | 0-1 |
| 4 | Coordination number | 0-12+ |
| 5 | Valence electrons | 1-8 |
| 6 | Atomic radius | Å |
| 7 | Electronegativity | 0.7-4.0 |
| 8 | Group number | 1-18 |
| 9 | Period number | 1-7 |
| 10 | Charge density* | e/Å³ |

*Optional, only when charge density data is available

### Edge Features (4 dimensions)

| Feature | Description | Range/Units |
|---------|-------------|-------------|
| 0 | Interatomic distance | 0-5.0 Å |
| 1 | Normalized distance | Distance/(r₁+r₂) |
| 2 | Bond type | 0-3 (ionic/covalent/metallic/van der Waals) |
| 3 | Angle factor | 0-1 (tetrahedral coordination measure) |

## Target Properties (20 dimensions)

The module predicts 20 material properties:

| Category | Properties |
|----------|------------|
| **Electronic** | band_gap, band_gap_type, electron_affinity, effective_mass_electron, effective_mass_hole_heavy, effective_mass_hole_light |
| **Optical** | dielectric_constant_static, dielectric_constant_high_freq, refractive_index |
| **Mechanical** | bulk_modulus, shear_modulus, youngs_modulus, poissons_ratio, elastic_constant_c11, elastic_constant_c12, elastic_constant_c44 |
| **Transport** | electron_mobility, hole_mobility |
| **Thermal** | thermal_conductivity |
| **Structural** | lattice_constant |

## Pipeline Workflow

### 1. Data Loading
- Load CIF structure files from `structure_dir`
- Load material properties from `properties.json`
- Detect charge density availability

### 2. Structure Processing
- Parse CIF files using pymatgen
- Extract supercell structures (16 atoms for 2×2×2)
- Match structures with property data by composition

### 3. Graph Conversion
- Extract node features (atomic properties + coordinates)
- Compute edge connectivity within cutoff radius
- Extract edge features (distances, bond types)
- Create PyTorch Geometric Data objects

### 4. Normalization
- Fit normalizer on training set statistics
- Apply z-score normalization to features
- Save normalization parameters

### 5. Validation & Output
- Validate graph structure and features
- Save graphs as `.pt` files
- Generate dataset statistics and visualizations

## Configuration

### Pipeline Parameters

```python
pipeline = GraphConversionPipeline(
    structure_dir="data/outputs/calculations/structures",  # CIF files location
    properties_file="data/outputs/calculations/properties.json",  # Properties data
    output_dir="data/outputs/graphs",  # Output directory
    cutoff_radius=5.0,  # Edge connection cutoff (Å)
    use_both_structures=True  # Process both original and relaxed structures
)
```

### Feature Extraction Settings

```python
builder = CrystalGraphBuilder(
    cutoff_radius=5.0,  # Maximum bond distance
    normalize=True  # Apply feature normalization
)
```

## Output Structure

```
data/outputs/graphs/
├── graphs/
│   ├── AlGaAs_x0.000_original.pt
│   ├── AlGaAs_x0.250_original.pt
│   ├── AlGaAs_x0.000_relaxed.pt
│   └── ...
├── statistics/
│   ├── normalization_stats.json
│   └── dataset_statistics.json
├── visualizations/
│   ├── feature_distributions.png
│   ├── target_correlations.png
│   └── graph_statistics.png
└── dataset_info.json
```

## Dataset Creation

### PyTorch Dataset

```python
from src.graph_conversion import MaterialPropertyDataset

# Create dataset
dataset = MaterialPropertyDataset(
    graph_dir="data/outputs/graphs/graphs",
    normalize=True,  # Apply normalization
    preload=True  # Load all graphs into memory
)

# Dataset operations
print(f"Dataset size: {len(dataset)}")
graph, target = dataset[0]
print(f"Graph: {graph.num_nodes} nodes, target shape: {target.shape}")

# Filter by composition
filtered_dataset = dataset.filter_by_composition(min_x=0.0, max_x=0.5)
```

### DataLoader Integration

```python
from torch.utils.data import DataLoader

# Create data loader
loader = DataLoader(dataset, batch_size=32, shuffle=True)

for batch in loader:
    # batch.x: [total_nodes, node_features]
    # batch.edge_index: [2, total_edges]
    # batch.edge_attr: [total_edges, edge_features]
    # batch.y: [batch_size, 20]
    # batch.batch: [total_nodes] (batch assignment)
    pass
```

## Normalization

### Z-Score Normalization

```python
from src.graph_conversion import FeatureNormalizer

normalizer = FeatureNormalizer()

# Fit on training data
normalizer.fit(training_graphs)

# Transform features
normalized_graph = normalizer.transform(graph)

# Inverse transform predictions
original_predictions = normalizer.inverse_transform_targets(normalized_preds)
```

### Statistics Storage

```python
# Save normalization statistics
normalizer.save_statistics("data/outputs/graphs/statistics/normalization_stats.json")

# Load for inference
normalizer.load_statistics("data/outputs/graphs/statistics/normalization_stats.json")
```

## Visualization

### Dataset Statistics

```python
from src.graph_conversion import GraphVisualizer

visualizer = GraphVisualizer("data/outputs/graphs/visualizations")

# Plot feature distributions
visualizer.plot_feature_distributions(graphs)

# Plot target correlations
visualizer.plot_target_correlation(graphs, property_names)

# Create summary visualizations
visualizer.create_summary_visualizations(graphs, property_names)
```

## Validation

### Graph Validation

```python
# Validate individual graph
is_valid = builder.validate_graph(graph)

# Validation checks:
# - Required components present (x, edge_index, y)
# - Correct feature dimensions (10-11 node, 4 edge, 20 target)
# - No NaN or Inf values
# - Valid edge connectivity
```

### Dataset Validation

```python
from src.graph_conversion.utils import validate_graph_data

# Validate graph data structure
is_valid = validate_graph_data(graph_dict)
```

## Performance Optimization

### Memory Management
- **Preloading**: Load all graphs into memory for fast access
- **Batching**: Process structures in batches to manage memory
- **Lazy Loading**: Load graphs on-demand for large datasets

### Computation Optimization
- **Cutoff Radius**: Balance connectivity vs computation (4-6 Å typical)
- **Supercell Size**: Larger cells provide better statistics but increase computation
- **Feature Selection**: Include charge density only when beneficial

## Troubleshooting

### Common Issues

1. **Missing Properties**: Ensure properties.json contains all 20 target properties
2. **CIF Parsing Errors**: Check CIF file format and completeness
3. **Memory Issues**: Reduce batch size or use lazy loading
4. **Normalization Errors**: Ensure normalizer is fitted before transforming
5. **Feature Dimension Mismatch**: Verify charge density availability matches expectations

### Debugging

```python
# Check graph structure
print(f"Nodes: {graph.num_nodes}")
print(f"Edges: {graph.edge_index.shape[1]}")
print(f"Node features: {graph.x.shape}")
print(f"Edge features: {graph.edge_attr.shape}")
print(f"Targets: {graph.y.shape}")

# Validate features
print(f"NaN in nodes: {torch.isnan(graph.x).any()}")
print(f"NaN in edges: {torch.isnan(graph.edge_attr).any()}")
print(f"NaN in targets: {torch.isnan(graph.y).any()}")
```

## Dependencies

### Required
- `torch`: PyTorch for tensor operations
- `torch_geometric`: Graph neural network library
- `pymatgen`: Crystal structure manipulation
- `numpy`: Numerical computations
- `matplotlib`: Visualization (optional)

### Optional
- `scipy`: Advanced computations
- `seaborn`: Enhanced plotting

## Examples

### Complete Workflow

```python
from src.graph_conversion import GraphConversionPipeline

# Initialize and run pipeline
pipeline = GraphConversionPipeline(
    structure_dir="data/outputs/calculations/structures",
    properties_file="data/outputs/calculations/properties.json",
    output_dir="data/outputs/graphs"
)

pipeline.convert_all()
pipeline.compute_statistics()
pipeline.create_visualizations()
pipeline.save_dataset_info()

# Create dataset
from src.graph_conversion import MaterialPropertyDataset
dataset = MaterialPropertyDataset("data/outputs/graphs/graphs")

print(f"Created dataset with {len(dataset)} graphs")
```

### Custom Feature Extraction

```python
from src.graph_conversion import FeatureExtractor

extractor = FeatureExtractor(cutoff_radius=5.0)

# Extract features
node_features = extractor.extract_node_features(structure, charge_density)
edge_index, edge_features = extractor.extract_edge_features(structure)

# All features at once
nodes, edges, edge_attrs = extractor.extract_all_features(structure, charge_density)
```

## Contributing

When adding new features:
1. Update `FeatureExtractor` for new node/edge features
2. Modify `CrystalGraphBuilder` for new graph construction logic
3. Add validation in `validate_graph()` method
4. Update normalization statistics computation
5. Add visualization support in `GraphVisualizer`

## References

- PyTorch Geometric: https://pytorch-geometric.readthedocs.io/
- pymatgen: https://pymatgen.org/
- Crystal Graph Convolutions: https://arxiv.org/abs/1710.10324
- Materials Project: https://materialsproject.org/