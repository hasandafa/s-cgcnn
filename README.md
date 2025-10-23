## THIS IS STILL INCOMPLETE DUE TO BUGS! ANYWAY, ENJOY THE EARLY PHASE PIPELINE!

# S-CGCNN: Material-Agnostic Semiconductor Research Pipeline

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/hasandafa/s-cgcnn)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A comprehensive computational framework for studying semiconductor alloys and their properties using machine learning and first-principles calculations. The system is now **fully material-agnostic**, supporting any binary alloy system through extensible YAML configuration.

## 🎯 Overview

S-CGCNN is a research pipeline that combines:
- **Material-Agnostic Alloy Generation**: Support for any binary semiconductor alloy
- **Multi-Scale Property Calculation**: From electronic structure to mechanical properties
- **Graph Neural Networks**: Crystal structure representation for ML predictions
- **Advanced Interpolation**: Charge density, structure relaxation, and tight-binding methods
- **Extensible Architecture**: Easy addition of new materials and properties

### Key Capabilities

- **20+ Material Properties**: Band gaps, effective masses, dielectric constants, elastic properties, etc.
- **Electronic Structure**: Tight-binding calculations with direct/indirect gap transitions
- **Charge Density Interpolation**: Real-space alloy charge density from binary endpoints
- **ML Structure Relaxation**: CHGNet and EMT potential-based optimization
- **Graph Representation**: PyTorch Geometric graphs for GNN training
- **Data Validation**: Comprehensive quality checks for Materials Project data

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/hasandafa/s-cgcnn.git
cd s-cgcnn

# Install dependencies
pip install -r requirements.txt

# Set up Materials Project API key
echo "mp_api = YOUR_API_KEY_HERE" > key.env
```

### Basic Usage

```python
from src.calculation.main import run_full_pipeline

# Run complete pipeline for AlGaAs
results = run_full_pipeline(
    alloy_system="AlGaAs",
    material1="GaAs",
    material2="AlAs",
    enable_all_features=True
)

print(f"Generated {results['summary']['num_structures']} alloy structures")
print(f"Calculated properties for {results['summary']['num_compositions']} compositions")
```

### Material-Agnostic Usage

```python
# Works with any alloy system defined in materials/properties/
results = run_full_pipeline(
    alloy_system="InGaAs",  # Just change the alloy name
    material1="GaAs",
    material2="InAs"
)
```

## 📊 Pipeline Architecture

<<<<<<< HEAD
```
Materials Project API → Data Acquisition → Structure Generation → Property Calculation → Graph Conversion → GNN Training
        ↓                    ↓                    ↓                    ↓                    ↓              ↓
   Validation         CIF Processing     Charge Density      Electronic Structure    Feature Extraction  Prediction
   Caching            YAML Updates       Interpolation       Tight-Binding          Normalization       Analysis
=======
1. **Clone the repository**
```bash
git clone -b version-0.1-improved https://github.com/hasandafa/s-cgcnn.git
cd s-cgcnn
>>>>>>> 5958d4264453e67be10726dc0518d9639ae9d00f
```

### Core Modules

<<<<<<< HEAD
| Module | Purpose | Key Features |
|--------|---------|--------------|
| **Data Acquisition** | Fetch and validate materials data | MP-API integration, caching, validation |
| **Calculation** | Property computation and structure generation | Material-agnostic, 20+ properties, tight-binding |
| **Graph Conversion** | Crystal to graph transformation | PyTorch Geometric, rich features, normalization |
| **Utils** | Configuration and utilities | YAML config, logging, API validation |

## 🔬 Key Features

### Material-Agnostic Design

- **Any Binary Alloy**: Support for AlGaAs, InGaAs, GaN-AlN, etc.
- **YAML Configuration**: Add new materials via simple config files
- **Automatic Detection**: Element substitution and property interpolation

### Advanced Calculations

- **20 Material Properties**: Electronic, optical, mechanical, thermal, transport
- **Tight-Binding Electronic Structure**: Band gaps, effective masses, direct/indirect transitions
- **Charge Density Interpolation**: Real-space alloy charge density from binary endpoints
- **ML Structure Relaxation**: CHGNet and EMT potential optimization

### Graph Neural Networks

- **Rich Node Features**: 10-11 dimensional (atomic properties + optional charge density)
- **Edge Features**: 4-dimensional (distance, bond type, angle factors)
- **PyTorch Geometric**: Ready for GNN training and inference
- **Feature Normalization**: Z-score normalization for stable training

## 📁 Project Structure

```
s-cgcnn/
├── src/
│   ├── calculation/          # Property calculation & structure generation
│   ├── data_acquisition/     # Materials Project API & data validation
│   ├── graph_conversion/     # Crystal to graph transformation
│   └── utils/               # Configuration, logging, caching
├── materials/               # Material property definitions
│   └── properties/          # YAML files for each material/alloy
├── data/                    # Downloaded material data
├── outputs/                 # Calculation results & graphs
├── tests/                   # Unit and integration tests
├── config.yaml             # Main configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🧪 Usage Examples

### Property Calculation
=======
3. **Set up key.env and add your Materials Project API key**
```bash
# Add your API key to key.env
echo "MP_API_KEY=your_api_key_here" > key.env
```

## 🔬 Usage Examples
>>>>>>> 5958d4264453e67be10726dc0518d9639ae9d00f

```python
from src.calculation import PropertyCalculator

# Calculate properties for any alloy composition
calculator = PropertyCalculator("AlGaAs", data_source="literature")
properties = calculator.calculate_multiple_properties(
    ["band_gap", "lattice_constant", "bulk_modulus"],
    x=0.5  # Al₀.₅Ga₀.₅As
)

print(f"Band gap: {properties['band_gap']:.3f} eV")
```

### Electronic Structure

```python
from src.calculation import calculate_electronic_structure

<<<<<<< HEAD
# Advanced electronic structure calculation
results = calculate_electronic_structure(
    "AlGaAs", x=0.3,
    calculate_bs=True,
    calculate_dos=True,
    calculate_masses=True
)

print(f"Band gap: {results['band_gap']:.3f} eV")
print(f"Direct gap: {results['is_direct']}")
=======
```bash
# Test full pipeline (quick mode)
python tests/test_full_pipeline.py --quick

# Test full pipeline with all features
python tests/test_full_pipeline.py --full
>>>>>>> 5958d4264453e67be10726dc0518d9639ae9d00f
```

### Graph Generation

```python
from src.graph_conversion import GraphConversionPipeline

# Convert structures to graphs
pipeline = GraphConversionPipeline(
    structure_dir="data/outputs/calculations/structures",
    properties_file="data/outputs/calculations/properties.json",
    output_dir="data/outputs/graphs"
)

pipeline.convert_all()
pipeline.compute_statistics()
```

### Dataset Creation

```python
from src.graph_conversion import MaterialPropertyDataset

# Create PyTorch dataset
dataset = MaterialPropertyDataset(
    graph_dir="data/outputs/graphs/graphs",
    normalize=True
)

# Use with PyTorch DataLoader
loader = DataLoader(dataset, batch_size=32, shuffle=True)
```

## 🔧 Configuration

### Main Config (config.yaml)

```yaml
system:
  alloy_system: "AlGaAs"          # Any system with YAML definition
  compositions:
    x_values: [0.0, 0.25, 0.5, 0.75, 1.0]
  data_source: "literature"       # or "mp_api"

features:
  enable_charge_density: true     # Real-space interpolation
  enable_relaxation: true        # ML structure optimization
  enable_tight_binding: true     # Electronic structure calculations
```

### Adding New Materials

1. **Create material YAML** in `materials/properties/`:
```yaml
material:
  name: "InAs"
  formula: "InAs"
  mp_id: "mp-20305"

literature:
<<<<<<< HEAD
  band_gap: 0.354
  lattice_constant: 6.0583
=======
  source: "Adachi, S. The Handbook on Optical Constants of Semiconductors In Tables and Figures"
  temperature: 300
  physical:
    lattice_constant: 6.0583
  electronic:
    band_gap: 0.354
    band_gap_type: "direct"
>>>>>>> 5958d4264453e67be10726dc0518d9639ae9d00f
  # ... more properties
```

2. **Create alloy YAML**:
```yaml
alloy_system:
  name: "InGaAs"
  binary_endpoints:
    - material: "GaAs"
    - material: "InAs"

bowing_parameters:
  band_gap: 0.477
  lattice_constant: 0.0
```

## 📈 Output Formats

### Properties JSON
```json
{
  "metadata": {
    "alloy_system": "AlGaAs",
    "data_source": "literature",
    "compositions": [0.0, 0.25, 0.5, 0.75, 1.0]
  },
  "compositions": {
    "x_0.500": {
      "x": 0.5,
      "properties": {
        "band_gap": 1.85,
        "lattice_constant": 5.65,
        "bulk_modulus": 74.2
      }
    }
  }
}
```

### Graph Data (PyTorch Geometric)
```python
graph.x          # Node features [num_atoms, 10-11]
graph.edge_index # Edge connectivity [2, num_edges]
graph.edge_attr  # Edge features [num_edges, 4]
graph.y          # Target properties [20]
graph.composition # Alloy composition
```

## 🧪 Testing

```bash
# Quick test
python tests/test_full_pipeline.py --quick

# Full pipeline test
python tests/test_full_pipeline.py --full

# Specific module tests
python -m pytest tests/test_calculation.py -v
```

<<<<<<< HEAD
## 📊 Performance
=======
## 📈 Output Structure (Alpha Edition)
>>>>>>> 5958d4264453e67be10726dc0518d9639ae9d00f

- **Structure Generation**: ~1-5 seconds per composition
- **Property Calculation**: ~0.1-1 second per composition
- **Graph Conversion**: ~0.5-2 seconds per structure
- **Memory Usage**: ~100-500MB depending on system size

## 🔄 Version History

### v1.0.0 (Current)
- **Material-Agnostic Architecture**: Support for any binary alloy system
- **Complete Pipeline Integration**: Data acquisition → calculation → graphs
- **Advanced Electronic Structure**: Tight-binding with direct/indirect transitions
- **Charge Density Interpolation**: Real-space alloy charge density
- **ML Structure Relaxation**: CHGNet and EMT potential support
- **Rich Graph Features**: 10-11 node features, 4 edge features
- **Comprehensive Validation**: Data quality checks and anomaly detection

### v0.1.0 (Previous)
- Basic AlGaAs support
- Limited property calculations
- Simple structure generation
- Basic graph conversion
## 🔄 Major Updates from v0.1.0

### Architecture Overhaul
- **Material-Agnostic Design**: Complete rewrite to support any binary alloy system
- **Modular Architecture**: Separated concerns into focused modules (calculation, data acquisition, graph conversion, utils)
- **Extensible Configuration**: YAML-based material definitions for easy addition of new systems

### New Capabilities
- **20+ Material Properties**: Comprehensive property calculation suite
- **Tight-Binding Electronic Structure**: Advanced band structure calculations with direct/indirect gap handling
- **Charge Density Interpolation**: Real-space alloy charge density from binary endpoints
- **ML Structure Relaxation**: CHGNet and EMT potential integration
- **Rich Graph Features**: 10-11 dimensional node features, 4-dimensional edge features
- **PyTorch Geometric Integration**: Production-ready GNN dataset creation

### Data Pipeline Enhancement
- **Materials Project API Integration**: Official MPRester client with smart caching
- **Comprehensive Validation**: Data quality checks, anomaly detection, provenance tracking
- **CIF Processing**: Automatic crystal structure analysis and metadata extraction
- **Parallel Processing**: Multi-threaded data acquisition with rate limiting

### Quality Improvements
- **Data Validation**: Multi-level validation (structure, band structure, phonon, charge density)
- **Error Handling**: Robust error recovery and detailed logging
- **Caching System**: Intelligent caching with time-based invalidation
- **Configuration Management**: Centralized config with validation

### Developer Experience
- **Comprehensive Documentation**: Module-level READMEs with examples and API reference
- **Type Hints**: Full type annotation coverage
- **Testing Framework**: Unit and integration tests
- **Logging System**: Centralized logging with file rotation

### Breaking Changes
- **API Changes**: Function signatures updated for material-agnostic design
- **Configuration Format**: New YAML structure for materials and alloys
- **Output Structure**: Reorganized output directories and file formats
- **Dependencies**: Updated to latest compatible versions

### Migration Guide
1. **Update Configuration**: Convert old config to new YAML format
2. **Add Material Files**: Create YAML files for materials in `materials/properties/`
3. **Update API Calls**: Use new material-agnostic function signatures
4. **Reinstall Dependencies**: Update to new requirements.txt
5. **Validate Data**: Run validation on existing data

For detailed migration instructions, see the module-specific README files in `src/*/README.md`.

<<<<<<< HEAD
## 🤝 Contributing

1. **Add New Materials**: Create YAML files in `materials/properties/`
2. **Extend Properties**: Add new property calculations in `PropertyCalculator`
3. **Improve Features**: Enhance graph features in `FeatureExtractor`
4. **Add Validation**: Extend data validation in `DataValidator`

## 📚 Documentation

- **Module Documentation**: Each `src/` folder contains detailed README.md
- **API Reference**: Comprehensive docstrings in all modules
- **Examples**: Jupyter notebooks in `examples/` (future)
- **Tutorials**: Step-by-step guides (future)

## 🙏 Acknowledgments

- **Materials Project**: For providing comprehensive materials data
- **PyMatGen**: Crystal structure manipulation library
- **PyTorch Geometric**: Graph neural network framework
- **CHGNet**: Universal ML potential for structure relaxation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Authors**: Abdullah Hasan Dafa, Razasyattar M. N.  
**Version**: 1.0.0  
**Date**: 2025-10-23  
**Repository**: https://github.com/hasandafa/s-cgcnn
=======
## 📚 Documentation

- **QUICK_START.md**: Quick start guide for users
- **materials/properties/README.md**: Material file format guide

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
---

**Version**: 0.1-improved (Thicc Changes)  
**Date**: 2025-10-17  
**Authors**: Abdullah Hasan Dafa, Razasyattar M. N.
>>>>>>> 5958d4264453e67be10726dc0518d9639ae9d00f
