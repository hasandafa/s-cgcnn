# s-CGCNN Version 0.1

## Simplified Graph Neural Networks for CPU-Efficient Screening of AlₓGa₁₋ₓAs Alloys in Microelectronics Applications

**Version:** 0.1.0  
**Phase:** Data Acquisition & Structure Interpolation  
**Author:** Abdullah Hasan Dafa  
**Status:** ✅ Development

---

## 📋 Overview

Version 0.1 establishes the foundation for the s-CGCNN project by implementing:

1. **Materials Project API Integration** - Fetches GaAs (mp-2534) and AlAs (mp-2172) reference structures
2. **Ordered Supercell Interpolation** - Generates 41 AlₓGa₁₋ₓAs structures (x = 0.0 to 1.0, step 0.025)
3. **Property Calculation** - Interpolates physical, electronic, and thermal properties using Vegard's Law with bowing parameters
4. **Data Export** - Saves structures as CIF files and metadata as JSON

---

## 🎯 Features

- ✅ Fetch crystal structures from Materials Project API
- ✅ Generate AlₓGa₁₋ₓAs compositions via ordered Ga→Al substitution
- ✅ Calculate interpolated properties with bowing corrections
- ✅ Export CIF files for all 41 compositions
- ✅ Comprehensive metadata for each structure
- ✅ Automated testing suite for validation

---

## 📁 Directory Structure

```
s-cgcnn/
├── config/
│   ├── config_v0.1.yaml      # Configuration file
│   └── mp_api_key.txt        # Your MP API key (create this!)
│
├── data/
│   ├── raw/                  # MP fetched data (JSON)
│   └── structures/
│       ├── cif/              # 41 CIF files
│       └── metadata/         # Property data (JSON)
│
├── src/
│   ├── data_acquisition/
│   │   ├── mp_fetcher.py
│   │   └── structure_interpolator.py
│   └── utils/
│       ├── constants.py
│       └── logger_config.py
│
├── tests/
│   └── 1. Data Acquisition and Structure Interpolation Testing.py
│
├── logs/                     # Execution logs
├── requirements.txt
└── README_v0.1.md
```

---

## 🚀 Installation

### 1. Clone Repository

```bash
git clone https://github.com/hasandafa/s-cgcnn.git
cd s-cgcnn
git checkout version-0.1
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Materials Project API Key

1. Get your API key from: https://next-gen.materialsproject.org/api
2. Create file `config/mp_api_key.txt` and paste your key

```bash
echo "YOUR_API_KEY_HERE" > config/mp_api_key.txt
```

---

## 📖 Usage

### Quick Start: Run All Tests

```bash
python "1. Data Acquisition and Structure Interpolation Testing.py"
```

This will:
1. Fetch GaAs and AlAs from Materials Project
2. Generate 41 interpolated structures
3. Calculate all properties
4. Validate data integrity
5. Generate comprehensive report

### Step-by-Step Usage

#### 1. Fetch MP Data

```python
from src.data_acquisition.mp_fetcher import MPDataFetcher

# Read API key
with open("config/mp_api_key.txt", 'r') as f:
    api_key = f.read().strip()

# Fetch data
fetcher = MPDataFetcher(api_key)
data = fetcher.fetch_all_materials()
```

#### 2. Generate Structures

```python
from src.data_acquisition.structure_interpolator import StructureInterpolator

# Load MP structures
gaas_data = fetcher.load_saved_data("GaAs")
alas_data = fetcher.load_saved_data("AlAs")

# Initialize interpolator
interpolator = StructureInterpolator(
    gaas_structure=gaas_data["structure"],
    alas_structure=alas_data["structure"],
    supercell_size=[2, 2, 2]
)

# Generate all structures
results = interpolator.generate_all_structures()
```

---

## 📊 Output Files

### CIF Files
Location: `data/structures/cif/`

Files: `AlGaAs_x_0_000.cif` through `AlGaAs_x_1_000.cif`

### Metadata Files
Location: `data/structures/metadata/`

Each JSON file contains:
- Composition and formula
- Lattice parameters
- Space group
- Calculated properties (band gap, lattice constant, elastic constants, etc.)
- Reference to CIF file

### Generation Summary
File: `data/structures/metadata/generation_summary.json`

Contains:
- Total structures generated
- Property ranges (min, max, mean)
- X values list

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
python "1. Data Acquisition and Structure Interpolation Testing.py"
```

**Tests included:**
1. ✅ Materials Project API connectivity
2. ✅ Structure interpolation accuracy
3. ✅ Property calculation validation
4. ✅ Data integrity checks

**Expected output:**
```
✓✓✓ ALL TESTS PASSED - VERSION 0.1 READY ✓✓✓
```

---

## 📝 Key Properties Calculated

### Physical Properties
- Lattice constant (Å)
- Density (g/cm³)
- Bulk modulus (GPa)
- Shear modulus (GPa)
- Elastic constants (c₁₁, c₁₂, c₄₄)

### Electronic Properties
- Band gap (direct/indirect, eV)
- Electron affinity (eV)
- Effective masses (electron/hole, m₀)
- Dielectric constants (static/optical)
- Refractive index

### Thermal Properties
- Thermal conductivity (W/m·K)
- Thermal expansion coefficient (10⁻⁶/K)
- Specific heat (J/kg·K)
- Debye temperature (K)

### Transport Properties
- Electron mobility (cm²/V·s)
- Hole mobility (cm²/V·s)

---

## 📚 References

### Data Sources
1. **Materials Project**: https://materialsproject.org
   - GaAs: mp-2534
   - AlAs: mp-2172

2. **Ioffe Institute Database**: https://www.ioffe.ru/SVA/NSM/Semicond/AlGaAs/
   - AlGaAs properties reference
   - Bowing parameters

### Literature
- Vegard's Law for lattice constant interpolation
- Virtual Crystal Approximation (VCA) for alloy properties
- Bowing parameter corrections from experimental data

---

## 🐛 Troubleshooting

### API Key Issues
```
Error: Invalid API key
Solution: Check your API key at https://next-gen.materialsproject.org/api
```

### Missing Dependencies
```bash
pip install --upgrade mp-api pymatgen
```

### Structure Generation Errors
- Ensure MP data is fetched first
- Check supercell size is appropriate (default: 2×2×2)

---

## 🚧 Known Limitations

1. **Supercell Size**: Fixed at 2×2×2 (16 atoms total)
   - May not capture all possible atomic configurations
   - Sufficient for ordered structures

2. **Property Interpolation**: Linear with bowing correction
   - More sophisticated methods possible (e.g., cluster expansion)
   - Current method validated against experimental data

3. **Band Structure**: Not yet predicted (coming in v0.4)
   - Only band gap values calculated

---

## ⏭️ Next Steps

**Version 0.2** will add:
- 🎨 Interactive crystal structure visualization (crystal-toolkit)
- 📊 Property comparison plots
- 💾 Enhanced data export options

---

## 👨‍💻 Author

**Abdullah Hasan Dafa**  
B.Eng. in Physics Engineering (Instrumentation & Control)  
Universitas Nasional, Indonesia

---

## 📄 License

© 2025 Abdullah Hasan Dafa. All rights reserved.

---

## 🙏 Acknowledgments

- Materials Project team for API access
- Ioffe Institute for AlGaAs reference data
- PyMatGen and PyTorch Geometric communities

---

**Last Updated:** October 2025  
**Version:** 0.1.0