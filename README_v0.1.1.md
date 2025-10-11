# s-CGCNN v0.1.1 - Complete Guide

**Simplified Crystal Graph Convolutional Neural Networks for AlₓGa₁₋ₓAs Semiconductor Alloys**

Author: **Abdullah Hasan Dafa**, B.Eng. Physics Engineering  
Institution: Universitas Nasional, Indonesia  
GitHub: [hasandafa/s-cgcnn](https://github.com/hasandafa/s-cgcnn)

---

## 🎯 What's New in v0.1.1

### ✨ Major Features

1. **Dual Data Source Support**
   - **Literature Mode**: Experimental values from ioffe.ru (recommended for device engineering)
   - **MP-API Mode**: DFT-calculated values from Materials Project (for computational studies)

2. **Flexible Property Calculation**
   - Choose data source via configuration
   - Automatic fallback to literature values when MP data unavailable
   - Band gap correction for DFT underestimation

3. **Comparison Mode**
   - Side-by-side comparison of Literature vs MP-API results
   - Statistical analysis of differences
   - Publication-ready comparison tables

4. **Enhanced MP-API Integration**
   - Comprehensive property fetching (electronic, mechanical, thermal, optical)
   - Automatic retry on connection errors
   - Property export to JSON

---

## 📦 Installation

### Prerequisites
- Python 3.10+ (NOT 3.13 - compatibility issues)
- Windows/Linux/macOS
- CPU-only (no GPU required)

### Step 1: Clone Repository
```bash
git clone https://github.com/hasandafa/s-cgcnn.git
cd s-cgcnn
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Setup Materials Project API Key
1. Get your free API key from [materialsproject.org](https://materialsproject.org)
2. Create file `config/mp_api_key.txt`
3. Paste your API key (single line, no quotes)

```bash
# Windows PowerShell
New-Item -ItemType File -Path config/mp_api_key.txt
# Then edit and paste your key

# Linux/macOS
echo "YOUR_API_KEY_HERE" > config/mp_api_key.txt
```

### Step 5: Verify Installation
```bash
python check_requirements.py
```

---

## 🚀 Quick Start

### Option 1: Literature Mode (Recommended)
Uses experimental values - best for device engineering applications.

```bash
python run_version_0.1.1.py --mode literature
```

**Output:**
- 41 AlGaAs structures (x = 0.0 to 1.0, step 0.025)
- CIF files in `data/structures/cif/`
- Property metadata in `data/structures/metadata/`
- Summary in `results/summary_v0.1.1_literature.json`

### Option 2: MP-API Mode
Uses DFT-calculated values from Materials Project.

```bash
python run_version_0.1.1.py --mode mp_api
```

**Features:**
- Fetches properties from Materials Project
- Applies band gap correction (scissor shift)
- Fallback to literature for missing properties
- Output in `results/summary_v0.1.1_mp_api.json`

### Option 3: Comparison Mode
Generate both datasets and compare.

```bash
python run_comparison_mode.py
```

**Output:**
- Both literature and MP-API datasets
- Comparison table: `results/comparison_v0.1.1/analysis/comparison_table.csv`
- Statistical summary: `results/comparison_v0.1.1/analysis/comparison_summary.json`

---

## ⚙️ Configuration

Edit `config/config_v0.1.1.yaml` to customize:

### Data Source Selection
```yaml
interpolation:
  mode: "literature"  # or "mp_api"
  mp_api_fallback_to_literature: true
  
  mp_bandgap_correction:
    enabled: true
    correction_factor: 1.5  # Scissor shift
```

### Composition Range
```yaml
structure_interpolation:
  composition:
    x_min: 0.0
    x_max: 1.0
    x_step: 0.025  # 41 compositions
```

### Properties to Calculate
```yaml
property_calculation:
  properties:
    electronic:
      - "band_gap"
      - "band_gap_type"
      - "electron_mobility"
    mechanical:
      - "bulk_modulus"
      - "elastic_constant_c11"
    # ... add more properties
```

---

## 📊 Understanding the Data

### Literature Mode Properties
**Source:** ioffe.ru/SVA/NSM/Semicond/AlGaAs/

**Key values:**
- GaAs band gap: **1.424 eV** (experimental, 300K)
- AlAs band gap: **2.168 eV** (experimental, 300K)
- Direct-to-indirect transition: **x = 0.45**

**Use cases:**
- HEMT design
- Laser diode engineering
- Solar cell optimization
- Device performance prediction

### MP-API Mode Properties
**Source:** Materials Project (DFT-GGA calculations)

**Key features:**
- GaAs band gap: ~0.19 eV (DFT, needs correction)
- AlAs band gap: ~1.50 eV (DFT, needs correction)
- Includes formation energy, stability metrics
- 0K calculations (not room temperature)

**Use cases:**
- DFT validation studies
- Thermodynamic stability analysis
- Computational materials research
- High-throughput screening

### Band Gap Correction
DFT-GGA underestimates band gaps by 30-50%. We apply **scissor shift correction**:

```
E_corrected = E_DFT × correction_factor
```

Default factor: **1.5** (configurable)

---

## 🧪 Testing

### Run Complete Test Suite
```bash
python tests/test_v0.1.1_complete.py
```

**Tests include:**
- Constants module (literature + MP-API)
- MP API fetcher
- Structure interpolator (both modes)
- Property calculation (Vegard's Law)
- File I/O operations

### Test Categories
- ✅ **Unit tests**: Individual components
- ✅ **Integration tests**: Full pipeline
- ✅ **File I/O tests**: CIF and JSON export

**Expected result:** All tests pass (or skip if MP API unavailable)

---

## 📁 Project Structure

```
s-cgcnn/
├── config/
│   ├── config_v0.1.1.yaml       # Main configuration
│   └── mp_api_key.txt           # Your MP API key (not in git)
│
├── src/
│   ├── __init__.py
│   ├── data_acquisition/
│   │   ├── __init__.py
│   │   ├── mp_fetcher.py        # MP API interface
│   │   └── structure_interpolator.py  # Alloy generation
│   └── utils/
│       ├── __init__.py
│       ├── constants.py         # Material properties (lit + MP)
│       └── logger_config.py     # Logging setup
│
├── tests/
│   ├── __init__.py
│   └── test_v0.1.1_complete.py  # Test suite
│
├── data/
│   └── structures/
│       ├── cif/                 # Generated CIF files
│       └── metadata/            # Property JSON files
│
├── results/
│   ├── summary_v0.1.1_literature.json
│   ├── summary_v0.1.1_mp_api.json
│   └── comparison_v0.1.1/
│
├── logs/
│   ├── v0.1.1_pipeline.log
│   └── v0.1.1_test_report.json
│
├── run_version_0.1.1.py         # Main pipeline
├── run_comparison_mode.py       # Comparison script
├── check_requirements.py        # Dependency checker
├── requirements.txt
├── README_v0.1.1.md            # This file
└── CHANGELOG.md
```

---

## 🔬 Example Workflows

### Workflow 1: Device Engineering (HEMT Design)
```bash
# Use literature mode for accurate device parameters
python run_version_0.1.1.py --mode literature

# Analyze results for high-mobility compositions
# Check data/structures/metadata/ for properties
```

**Target:** x = 0.25-0.30 (direct gap, high mobility)

### Workflow 2: DFT Validation Study
```bash
# Compare your DFT results with MP database
python run_version_0.1.1.py --mode mp_api

# Examine formation energies and stability
# results/summary_v0.1.1_mp_api.json
```

### Workflow 3: Literature vs DFT Comparison
```bash
# Generate both datasets for publication
python run_comparison_mode.py

# Analyze differences
# results/comparison_v0.1.1/analysis/comparison_table.csv
```

---

## 🎓 Research Applications

### 1. High Electron Mobility Transistor (HEMT)
- **Target composition:** x = 0.25-0.35
- **Key properties:** electron_mobility, band_offset
- **Data source:** Literature mode

### 2. Laser Diode / LED
- **Target composition:** x = 0.0-0.45 (direct gap)
- **Key properties:** band_gap (1.4-2.0 eV), refractive_index
- **Data source:** Literature mode

### 3. Solar Cell
- **Target composition:** x ~ 0.0 (near GaAs)
- **Key properties:** band_gap (optimal ~1.42 eV)
- **Data source:** Literature mode

### 4. Computational Materials Science
- **Target:** All compositions
- **Key properties:** formation_energy, energy_above_hull
- **Data source:** MP-API mode

---

## 🐛 Troubleshooting

### Issue: "MP API key file not found"
**Solution:**
```bash
# Create the file
echo "YOUR_KEY_HERE" > config/mp_api_key.txt
```

### Issue: "ImportError: No module named 'mp_api'"
**Solution:**
```bash
pip install mp-api==0.41.2
```

### Issue: Band gap values seem wrong
**Check:**
1. Are you in literature or MP-API mode?
2. Is band gap correction enabled (MP-API mode)?
3. DFT values are expected to be ~50% lower

### Issue: "Property is None" warnings
**Explanation:**
- Some MP-API properties may not be available for all materials
- Fallback to literature values is automatic (if enabled)
- Check `mp_api_fallback_to_literature: true` in config

### Issue: Composition mismatch (x=0.025 → x=0.000)
**Explanation:**
- With 8 Ga sites, only 9 discrete compositions possible
- Target compositions are rounded to nearest achievable value
- **This is normal and expected**

---

## 📚 Key Concepts

### Vegard's Law with Bowing
Property interpolation formula:

```
P(x) = (1-x)·P_GaAs + x·P_AlAs - b·x·(1-x)
```

Where:
- `x`: Al composition (0.0 to 1.0)
- `b`: Bowing parameter (material-dependent)
- For band gap: `b = 0.37 eV`

### Direct-to-Indirect Transition
- **x < 0.45:** Direct band gap (Γ valley)
- **x ≥ 0.45:** Indirect band gap (X valley)

Critical for optoelectronic device design!

### Scissor Shift Correction
DFT band gap correction:

```
E_corrected = E_DFT × factor
```

Compensates for DFT-GGA underestimation.

---

## 📖 Citation

If you use s-CGCNN in your research, please cite:

```bibtex
@software{scgcnn2025,
  author = {Dafa, Abdullah Hasan},
  title = {s-CGCNN: Simplified Crystal Graph Convolutional Neural Networks 
           for AlGaAs Semiconductor Alloys},
  year = {2025},
  version = {0.1.1},
  url = {https://github.com/hasandafa/s-cgcnn}
}
```

---

## 🤝 Contributing

This is a research project. Contributions welcome via:
1. GitHub issues
2. Pull requests
3. Email: [via GitHub profile]

---

## 📄 License

© 2025 Abdullah Hasan Dafa. All Rights Reserved.

This software is currently in research and development phase.

---

## 🔗 Resources

### Documentation
- [ioffe.ru - AlGaAs Properties](https://www.ioffe.ru/SVA/NSM/Semicond/AlGaAs/)
- [Materials Project API Docs](https://docs.materialsproject.org/)
- [PyMatGen Documentation](https://pymatgen.org/)

### Related Work
- Xie & Grossman (2018): Crystal Graph Convolutional Neural Networks
- Materials Project Database
- CGCNN for materials property prediction

---

## 📧 Contact

**Abdullah Hasan Dafa**  
B.Eng. Physics Engineering (Instrumentation & Control)  
Universitas Nasional, Indonesia

GitHub: [hasandafa/s-cgcnn](https://github.com/hasandafa/s-cgcnn)

---

*Last updated: 2025-Q4 (v0.1.1)*