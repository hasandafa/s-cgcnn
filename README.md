# S-CGCNN: Material-Agnostic Semiconductor Research Pipeline

A comprehensive computational framework for studying semiconductor alloys and their properties using machine learning and first-principles calculations.

## 🚀 Features

- **Material-Agnostic**: Support for any binary semiconductor alloy system
- **Full Pipeline**: From data acquisition to property prediction
- **ML-Enhanced**: Structure relaxation and property prediction using S-CGCNN
- **Electronic Structure**: Tight-binding calculations for band structures
- **Charge Density**: Real-space interpolation for alloy systems
- **Extensible**: Easy addition of new materials via YAML configuration

## 📦 Quick Start

### For AlGaAs (Default System)
```python
from src.calculation.main import run_full_pipeline

results = run_full_pipeline(
    alloy_system="AlGaAs",
    material1="GaAs",
    material2="AlAs"
)
```

### For Any Other Alloy System
```python
# Example: InGaAs system
results = run_full_pipeline(
    alloy_system="InGaAs",
    material1="GaAs",
    material2="InAs"
)
```

## 🏗️ Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd s-cgcnn
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up Materials Project API key**
```bash
# Add your API key to key.env
echo "MP_API_KEY=your_api_key_here" > key.env
```

## 📁 Project Structure

```
s-cgcnn/
├── src/
│   ├── calculation/          # Core calculation modules
│   │   ├── main.py          # Main pipeline entry point
│   │   ├── constants.py     # Material properties (dynamic)
│   │   ├── electronic_structure.py  # Tight-binding calculations
│   │   ├── property_calculator.py   # Alloy property calculations
│   │   └── structure_interpolator.py # Structure generation
│   ├── data_acquisition/    # Materials Project data acquisition
│   └── utils/               # Utility functions
├── materials/               # Material definitions
│   ├── properties/          # YAML material files
│   │   ├── GaAs.yaml       # GaAs properties
│   │   ├── AlAs.yaml       # AlAs properties
│   │   └── AlGaAs.yaml     # AlGaAs alloy config
│   └── material_registry.py # Material management
├── data/                   # Downloaded material data
├── tests/                  # Test suite
├── config.yaml            # System configuration
└── QUICK_START.md         # Quick start guide
```

## 🔬 Usage Examples

### Basic Property Calculation
```python
from src.calculation.constants import get_properties, calculate_alloy_property

# Get individual material properties
gaas_props = get_properties("GaAs", "literature")
print(f"GaAs band gap: {gaas_props['band_gap']} eV")

# Calculate alloy properties
band_gap = calculate_alloy_property("AlGaAs", "band_gap", 0.3)
print(f"Al₀.₃Ga₀.₇As band gap: {band_gap} eV")
```

### Electronic Structure Calculation
```python
from src.calculation.electronic_structure import TightBindingAlloy

# Calculate band structure for AlGaAs at x=0.3
tb = TightBindingAlloy("AlGaAs", 0.3)
bs = tb.calculate_band_structure()
print(f"Band gap: {bs.band_gap:.3f} eV")
print(f"Direct gap: {bs.is_direct}")
```

### Full Pipeline with All Features
```python
from src.calculation.main import run_full_pipeline

# Run complete pipeline with charge density and relaxation
results = run_full_pipeline(
    alloy_system="AlGaAs",
    material1="GaAs",
    material2="AlAs",
    enable_all_features=True  # Includes charge density, relaxation, TB
)
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Test material system functionality
python test_materials_system.py

# Test full pipeline (quick mode)
python tests/test_full_pipeline.py --quick

# Test full pipeline with all features
python tests/test_full_pipeline.py --full
```

## 📊 Adding New Materials

1. **Create material YAML file** in `materials/properties/`:
```yaml
material:
  name: "InAs"
  formula: "InAs"
  mp_id: "mp-20305"
  structure_type: "zincblende"

literature:
  source: "Adachi Handbook"
  temperature: 300
  physical:
    lattice_constant: 6.0583
  electronic:
    band_gap: 0.354
    band_gap_type: "direct"
  # ... more properties

tight_binding:
  method: "Slater-Koster sp³s*"
  parameters:
    Es_cation: -7.123
    Es_anion: -9.456
    # ... TB parameters
```

2. **Create alloy system YAML** (if needed):
```yaml
alloy_system:
  name: "InGaAs"
  formula: "In_x Ga_{1-x} As"
  binary_endpoints:
    - material: "GaAs"
      x_value: 0.0
    - material: "InAs"
      x_value: 1.0

bowing_parameters:
  band_gap: 0.477
  lattice_constant: 0.0
```

3. **Download material data**:
```python
from src import scrape_binary_compounds
scrape_binary_compounds()
```

## 🔧 Configuration

The system is configured via `config.yaml`:

```yaml
paths:
  data_dir: "data/"
  output_dir: "outputs/"

system:
  alloy_system: "AlGaAs"
  binary_compounds:
    - name: "GaAs"
      mp_id: "mp-2534"
    - name: "AlAs"
      mp_id: "mp-2172"

features:
  enable_charge_density: false
  enable_relaxation: false
  enable_tight_binding: true
```

## 📈 Output Structure

Results are saved in `data/outputs/calculations/`:

```
data/outputs/calculations/
├── properties.json          # Calculated properties for all compositions
└── structures/
    ├── cif/                 # CIF files for each composition
    └── metadata/            # Structure metadata and relaxation reports
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📚 Documentation

- **QUICK_START.md**: Quick start guide for users
- **REFACTORING_GUIDE.md**: Technical documentation and API reference
- **materials/properties/README.md**: Material file format guide

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions or issues:
1. Check the documentation in `REFACTORING_GUIDE.md`
2. Run the test suite to verify your setup
3. Open an issue on GitHub

---

**Version**: 2.0.0 (Breaking Changes)  
**Date**: 2025-10-17  
**Authors**: Abdullah Hasan Dafa, Razasyattar M. N.