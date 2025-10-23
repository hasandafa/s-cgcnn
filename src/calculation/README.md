# Calculation Module

The `src/calculation/` module provides a comprehensive, material-agnostic framework for alloy structure generation, property calculation, and electronic structure analysis. This module is designed to work with any binary alloy system defined in the materials registry.

## Overview

This module enables:
- **Structure Generation**: Create alloy structures through supercell interpolation
- **Property Calculation**: Compute material properties using Vegard's Law with bowing corrections
- **Electronic Structure**: Perform tight-binding band structure calculations
- **Charge Density Interpolation**: Real-space charge density interpolation between binary endpoints
- **Structure Relaxation**: ML-based structure relaxation using CHGNet or EMT potentials

## Key Features

- **Material-Agnostic**: Works with any binary alloy system (AlGaAs, InGaAs, GaN-AlN, etc.)
- **Dual Data Sources**: Supports both literature (experimental) and MP-API (DFT) data
- **Advanced Interpolation**: Vegard's Law with bowing parameters, cubic splines, and scipy methods
- **Electronic Structure**: Tight-binding calculations for band gaps and effective masses
- **Charge Density**: Real-space interpolation for GNN node features
- **ML Relaxation**: Fast structure relaxation using CHGNet or EMT potentials

## Module Structure

### Core Files

| File | Purpose |
|------|---------|
| `main.py` | Main pipeline orchestration and high-level API |
| `constants.py` | Material properties database and registry access |
| `property_calculator.py` | Property calculations with tight-binding electronic structure |
| `electronic_structure.py` | Tight-binding band structure and DOS calculations |
| `structure_interpolator.py` | Structure generation with charge density and relaxation |
| `charge_density_interpolator.py` | Real-space charge density interpolation |
| `structure_relaxer.py` | ML-based structure relaxation (CHGNet/EMT) |

### Key Classes

- **`PropertyCalculator`**: Calculates alloy properties using Vegard's Law with bowing corrections
- **`StructureInterpolator`**: Generates alloy structures through supercell substitution
- **`ChargeDensityInterpolator`**: Interpolates charge density between binary materials
- **`StructureRelaxer`**: Relaxes structures using ML potentials
- **`AlloyTightBinding`**: Tight-binding electronic structure calculations

## Quick Start

### Basic Usage

```python
from src.calculation import run_full_pipeline

# Run complete pipeline for AlGaAs
results = run_full_pipeline(
    alloy_system="AlGaAs",
    material1="GaAs",
    material2="AlAs",
    enable_all_features=True
)
```

### Advanced Usage

```python
from src.calculation import PropertyCalculator, StructureInterpolator

# Calculate properties for AlGaAs at x=0.5
calculator = PropertyCalculator("AlGaAs", data_source="literature")
properties = calculator.calculate_multiple_properties(
    ["band_gap", "lattice_constant", "bulk_modulus"], x=0.5
)

# Generate alloy structures
structures = load_binary_structures("GaAs", "AlAs")
interpolator = StructureInterpolator(
    structure1=structures[0],
    structure2=structures[1],
    material1_name="GaAs",
    material2_name="AlAs",
    alloy_name="AlGaAs",
    enable_charge_density=True,
    enable_relaxation=True
)

alloys = interpolator.generate_composition_range(x_max=1.0, x_step=0.1)
```

## Data Sources

### Literature (Experimental)
- **Source**: Adachi's handbooks (300K experimental values)
- **Advantages**: Accurate for device applications, room temperature
- **Limitations**: Limited properties, no formation energies

### MP-API (DFT)
- **Source**: Materials Project database
- **Advantages**: Complete dataset, thermodynamics, consistent
- **Limitations**: Band gaps underestimated (30-50%), 0K only, needs corrections

## Property Calculation Methods

### Vegard's Law with Bowing
```python
# Linear interpolation with bowing correction
P(x) = (1-x)P₁ + x·P₂ - b·x·(1-x)
```

### Tight-Binding Electronic Structure
- Band gap transitions (direct/indirect)
- Effective masses (electron/hole)
- Band structure calculations

### Advanced Interpolation
- Cubic splines through endpoints and midpoint
- Scipy-based interpolation methods
- Bowing parameter corrections

## Structure Generation

### Supercell Substitution
1. Load primitive cubic structures
2. Create supercells (e.g., 2×2×2 = 8 atoms)
3. Random substitution of cations
4. Vegard interpolation of lattice parameters

### Features
- **Charge Density**: Real-space interpolation for GNN features
- **Relaxation**: ML-based structure optimization
- **Metadata**: Complete structure information and provenance

## Electronic Structure

### Tight-Binding Calculations
```python
from src.calculation import calculate_electronic_structure

# Calculate band structure for AlGaAs at x=0.5
results = calculate_electronic_structure(
    "AlGaAs", x=0.5,
    calculate_bs=True,
    calculate_dos=True,
    calculate_masses=True
)

print(f"Band gap: {results['band_gap']:.3f} eV")
print(f"Direct gap: {results['is_direct']}")
```

### Available Properties
- Band gap (direct/indirect transitions)
- Effective masses (electron, heavy/light holes)
- Band structure (k-path, energies)
- Density of states (DOS)

## Charge Density Interpolation

### Real-Space Interpolation
```python
from src.calculation import ChargeDensityInterpolator

# Create interpolator for any binary pair
interpolator = ChargeDensityInterpolator.from_material_pair(
    "GaAs", "AlAs", data_dir=Path("data")
)

# Interpolate for alloy structure
charge_data = interpolator.interpolate(x=0.5, target_structure=alloy_structure)

# Get per-atom values for GNN
per_atom_density = interpolator.get_per_atom_charge_density(
    x=0.5, target_structure=alloy_structure
)
```

### Export Formats
- **CHGCAR**: VASP charge density format
- **Cube**: Gaussian cube format for visualization
- **PNG**: 2D slice visualizations

## Structure Relaxation

### ML-Based Relaxation
```python
from src.calculation import StructureRelaxer

# Initialize relaxer (auto-selects CHGNet if available)
relaxer = StructureRelaxer(method='auto', fmax=0.05)

# Relax structure
result = relaxer.relax(structure, relax_cell=False)

print(f"Energy change: {result.energy_change:.3f} eV")
print(f"Max force: {result.max_force:.3f} eV/Å")
print(f"Converged: {result.converged}")
```

### Methods
- **CHGNet**: Pre-trained universal ML potential
- **EMT**: Effective Medium Theory (fast approximation)

## Configuration

### Config File (config.yaml)
```yaml
system:
  compositions:
    x_values: [0.0, 0.25, 0.5, 0.75, 1.0]

features:
  enable_charge_density: true
  enable_relaxation: true
  enable_tight_binding: true

paths:
  data_dir: "data/"
  output_dir: "data/outputs/"
```

### Environment Variables
- `MATERIALS_PROJECT_API_KEY`: For MP-API access
- `PYTHONPATH`: Include materials directory

## Dependencies

### Required
- `pymatgen`: Crystal structures and materials analysis
- `numpy`: Numerical computations
- `scipy`: Advanced interpolation methods
- `matplotlib`: Visualization (optional)

### Optional
- `chgnet`: ML potential for relaxation
- `ase`: Atomic simulation environment
- `materials-project-api`: DFT data access

## Output Structure

```
data/outputs/calculations/
├── structures/
│   ├── AlGaAs_x0.000.cif
│   ├── AlGaAs_x0.250.cif
│   └── ...
├── metadata/
│   ├── AlGaAs_x0.000.json
│   └── ...
└── properties.json
```

## Examples

### Complete Pipeline
```python
from src.calculation import run_full_pipeline

# AlGaAs system
results = run_full_pipeline(
    alloy_system="AlGaAs",
    material1="GaAs",
    material2="AlAs"
)

# Access results
structures = results['structures']
properties = results['properties']
```

### Custom Alloy System
```python
# Add new alloy to materials/properties/
# Then use with any system
results = run_full_pipeline(
    alloy_system="InGaAs",
    material1="GaAs",
    material2="InAs"
)
```

## Troubleshooting

### Common Issues

1. **Missing CHGCAR files**: Charge density interpolation requires VASP CHGCAR files
2. **MP-API access**: Set `MATERIALS_PROJECT_API_KEY` for DFT data
3. **Memory usage**: Large supercells (4×4×4) require significant RAM
4. **Convergence**: Some structures may not relax within step limits

### Performance Tips
- Use smaller supercells for faster generation
- Disable charge density for quick property calculations
- Use EMT instead of CHGNet for fast relaxation
- Parallelize composition range calculations

## Contributing

When adding new alloy systems:
1. Add material YAML files to `materials/properties/`
2. Add alloy system YAML with bowing parameters
3. Test with `run_full_pipeline()`
4. Update documentation

## References

- Adachi, S. (2012). Properties of Semiconductor Alloys
- Materials Project: https://materialsproject.org
- CHGNet: https://github.com/CederGroupHub/chgnet