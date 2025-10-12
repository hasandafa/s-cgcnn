# s-CGCNN v0.2 - Interactive Visualization & Analysis

**Simplified Crystal Graph Convolutional Neural Networks for AlₓGa₁₋ₓAs Screening**

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.2.0-green.svg)](https://github.com/hasandafa/s-cgcnn)

---

## 🎯 Overview

Version 0.2 introduces a **complete visualization and analysis suite** for exploring AlₓGa₁₋ₓAs semiconductor alloy properties. This release provides interactive 3D structure viewers, property evolution plots, and publication-ready figures.

### **New in v0.2:**
- ✅ Interactive 3D structure viewer (Crystal-toolkit + Dash)
- ✅ Property evolution plots (Plotly)
- ✅ Publication-ready figures (matplotlib + seaborn)
- ✅ Comprehensive analysis tools
- ✅ 6 interactive Jupyter notebooks
- ✅ Complete testing suite

---

## 📁 Project Structure

```
s-cgcnn/
├── src/
│   ├── data_acquisition/          # v0.1.1 (Data fetching & interpolation)
│   │   ├── mp_fetcher.py
│   │   └── structure_interpolator.py
│   ├── visualization/              # ✨ NEW v0.2 (Visualization modules)
│   │   ├── structure_viewer.py      # 3D structure viewer
│   │   ├── property_plotter.py      # Interactive plots
│   │   ├── figure_generator.py      # Publication figures
│   │   └── comparison_tools.py      # Analysis utilities
│   └── utils/
│       ├── constants.py
│       ├── logger_config.py
│       ├── file_io.py
│       └── validators.py
│
├── apps/                           # ✨ NEW (Standalone applications)
│   └── structure_viewer_app.py     # Dash app (port 8050)
│
├── notebooks/                      # ✨ UPDATED (6 new notebooks)
│   ├── 01_data_fetching.ipynb
│   ├── 02_structure_interpolation.ipynb
│   ├── 03_property_analysis.ipynb
│   ├── 04_interactive_viewer.ipynb
│   ├── 05_property_visualization.ipynb
│   └── 06_publication_figures_v0.1-0.2.ipynb
│
├── data/
│   └── structures/
│       ├── cif/                    # 41 CIF files (v0.1.1)
│       └── metadata/               # 41 JSON metadata (v0.1.1)
│
├── results/                        # ✨ NEW (Generated outputs)
│   ├── interactive/                # HTML interactive plots
│   ├── figures/                    # Publication figures (PDF/PNG/SVG)
│   └── analysis/                   # Analysis reports
│
├── tests/
│   ├── 1. Data Acquisition and Structure Interpolation Testing.py  # v0.1
│   ├── 1.1 Adding Interpolation Source Selection.py                # v0.1.1
│   ├── 2. Visualization Module Testing.py                          # ✨ NEW v0.2
│   ├── 2.1 Structure Viewer Testing.py                             # ✨ NEW v0.2
│   ├── 2.2 Property Plotter Testing.py                             # ✨ NEW v0.2
│   └── 2.3 Figure Generator Testing.py                             # ✨ NEW v0.2
│
├── config/
│   ├── config_v0.1.1.yaml
│   └── mp_api_key.txt
│
├── run_version_0.2.py              # ✨ NEW (Master pipeline)
├── requirements.txt
├── README_v0.2.md                  # This file
└── VERSION_0.2_CHECKLIST.md        # ✨ NEW (Verification checklist)
```

---

## 🚀 Quick Start

### **1. Launch Interactive Structure Viewer**

```bash
python apps/structure_viewer_app.py
```

Open browser: http://localhost:8050

### **2. Run Complete Visualization Pipeline**

```bash
# Generate all visualizations
python run_version_0.2.py --mode all

# Or run specific modes:
python run_version_0.2.py --mode interactive  # Plotly HTML plots
python run_version_0.2.py --mode publication  # PDF/PNG/SVG figures
python run_version_0.2.py --mode analysis     # Statistical analysis
python run_version_0.2.py --mode app          # Launch Dash app
```

### **3. Explore Jupyter Notebooks**

```bash
jupyter notebook notebooks/
```

Start with:
1. `01_data_fetching.ipynb` - Data acquisition demo
2. `02_structure_interpolation.ipynb` - Structure generation
3. `05_property_visualization.ipynb` - Interactive plots

---

## 📊 Features

### **1. Interactive 3D Structure Viewer**

```python
from src.visualization import StructureViewer

viewer = StructureViewer()
viewer.load_structures()
viewer.create_dash_app()
viewer.run_app()
```

**Features:**
- 🔄 Rotate, zoom, pan 3D structures
- 📊 Dropdown composition selector (41 compositions)
- 🎨 Atom coloring by element
- 📏 Unit cell display toggle
- 💾 Export high-resolution images

### **2. Property Evolution Plots (Plotly)**

```python
from src.visualization import PropertyPlotter

plotter = PropertyPlotter()
plotter.load_data()

# Band gap evolution
fig = plotter.plot_band_gap(show_type=True)
fig.show()

# Multi-property dashboard (2x3 grid)
fig = plotter.plot_multi_property_dashboard()
fig.write_html('results/dashboard.html')
```

**Plots Available:**
- 📈 Band gap vs composition (direct/indirect)
- 📐 Lattice constant (Vegard's Law)
- 🔧 Elastic properties
- 🌡️ Thermal conductivity
- 💡 Optical properties
- ⚡ Transport properties

### **3. Publication-Ready Figures**

```python
from src.visualization import FigureGenerator

generator = FigureGenerator(style='mp')  # Materials Project style
generator.load_data()

# Generate all figures
generator.generate_all_figures(
    output_dir='results/figures',
    formats=['pdf', 'png', 'svg']
)
```

**Output:**
- `figure1_band_gap.pdf` - Band gap evolution
- `figure2_lattice.pdf` - Lattice constant
- `figure3_properties.pdf` - Multi-property panel (2x3)
- `figure4_comparison.pdf` - Literature vs MP-API

**Quality:** 300 DPI, vector graphics, professional typography

### **4. Analysis Tools**

```python
from src.visualization import ComparisonTools

tools = ComparisonTools()
tools.load_data()

# Statistical summary
stats = tools.calculate_statistics()

# Correlation analysis
corr = tools.calculate_correlations()
tools.plot_correlation_heatmap('heatmap.png')

# Find optimal composition
x_opt, value = tools.find_optimal_composition('band_gap', target_value=1.5)

# Device-relevant compositions
suitable = tools.identify_device_compositions({
    'band_gap': (1.4, 1.6),
    'electron_mobility': (8000, None)
})
```

---

## 📚 Jupyter Notebooks

### **Notebook 01: Data Fetching**
- Fetch GaAs & AlAs from Materials Project
- Compare with literature data
- API usage demonstration

### **Notebook 02: Structure Interpolation**
- Generate AlₓGa₁₋ₓAs structures (41 compositions)
- Verify composition accuracy
- Lattice parameter evolution
- Band gap trends with direct/indirect transition

### **Notebook 03: Property Analysis**
- Load all 41 structure metadata
- Statistical analysis
- Property correlations
- Device-relevant composition identification

### **Notebook 04: Interactive Viewer**
- Crystal-toolkit 3D visualization
- Interactive structure exploration
- Dropdown composition selector
- Image export functionality

### **Notebook 05: Property Visualization**
- Interactive Plotly plots
- Band gap evolution
- Multi-property dashboards
- HTML export for sharing

### **Notebook 06: Publication Figures**
- Generate journal-ready figures
- Materials Project style plots
- High DPI (300+) vector graphics
- Complete figure set for papers

---

## 🧪 Testing

### **Run All Tests**

```bash
# Master test suite
python "tests/2. Visualization Module Testing.py"

# Specific tests
python "tests/2.1 Structure Viewer Testing.py"
python "tests/2.2 Property Plotter Testing.py"
python "tests/2.3 Figure Generator Testing.py"
```

### **Expected Output**

```
================================================================================
  s-CGCNN v0.2 - Visualization Testing Suite
================================================================================

TEST 1: Module Imports
  ✓ All visualization modules imported successfully
  ✓ All dependencies available

TEST 2: StructureViewer
  ✓ StructureViewer initialized
  ✓ Loaded 41 structures
  ✓ Structure retrieval working

TEST 3: PropertyPlotter
  ✓ PropertyPlotter initialized
  ✓ Loaded data for 41 compositions
  ✓ All required data columns present

TEST 4: FigureGenerator
  ✓ FigureGenerator initialized
  ✓ Loaded data for 41 compositions

TEST 5: ComparisonTools
  ✓ ComparisonTools initialized
  ✓ Statistics calculation working

TEST 6: Plot Generation
  ✓ Band gap plot generated
  ✓ Lattice constant plot generated
  ✓ Multi-property dashboard generated

TEST 7: Figure Export
  ✓ Band gap figure exported to PNG

TEST 8: Integration
  ✓ Data consistency verified
  ✓ Integration test passed

================================================================================
  ✓✓✓ ALL TESTS PASSED - VERSION 0.2 READY ✓✓✓
================================================================================
```

---

## 🔧 Dependencies

**Core (v0.1.1):**
- `pymatgen==2025.10.7`
- `mp-api==0.41.2`
- `numpy==1.26.4`
- `torch==2.1.0+cpu`
- `torch-geometric==2.6.1`

**Visualization (v0.2):**
- `plotly==6.3.1`
- `dash==3.2.0`
- `crystal-toolkit==2025.10.8`
- `matplotlib==3.10.7`
- `seaborn==0.13.2`

All dependencies are already installed in your environment.

---

## 📖 Documentation

### **API Reference**

#### **StructureViewer**
```python
class StructureViewer(data_dir=None)
```
- `load_structures(cif_dir)` - Load CIF files
- `get_structure(x)` - Get structure by composition
- `create_dash_app()` - Create Dash application
- `run_app(port=8050)` - Launch interactive app

#### **PropertyPlotter**
```python
class PropertyPlotter(data_dir=None)
```
- `load_data(metadata_dir)` - Load metadata
- `plot_band_gap()` - Band gap evolution plot
- `plot_lattice_constant()` - Lattice constant plot
- `plot_multi_property_dashboard()` - 2x3 property grid
- `export_all_plots(output_dir)` - Batch export

#### **FigureGenerator**
```python
class FigureGenerator(data_dir=None, style='mp')
```
- `load_data(metadata_dir)` - Load data
- `figure_band_gap_evolution()` - Figure 1
- `figure_lattice_constant()` - Figure 2
- `figure_multi_property()` - Figure 3
- `generate_all_figures()` - Batch generation

#### **ComparisonTools**
```python
class ComparisonTools(data_dir=None)
```
- `load_data(metadata_dir)` - Load data
- `calculate_statistics()` - Statistical summary
- `calculate_correlations()` - Correlation matrix
- `find_optimal_composition()` - Optimization
- `export_summary_report()` - Generate report

---

## 🎓 Citation

If you use this software in your research, please cite:

```bibtex
@software{scgcnn2025,
  author = {Dafa, Abdullah Hasan},
  title = {s-CGCNN: Simplified Crystal Graph Convolutional Neural Networks},
  year = {2025},
  version = {0.2.0},
  url = {https://github.com/hasandafa/s-cgcnn}
}
```

---

## 👤 Author

**Abdullah Hasan Dafa**  
B.Eng. in Physics Engineering (Instrumentation & Control)  
Universitas Nasional, Indonesia

📧 Email: [Your Email]  
🔗 GitHub: [@hasandafa](https://github.com/hasandafa)

---

## 📝 License

This project is licensed under the MIT License.

---

## 🗺️ Roadmap

### **v0.1.1 ✅ COMPLETE**
- Data acquisition (MP-API)
- Structure interpolation
- Dual data source support

### **v0.2 ✅ COMPLETE**
- Interactive visualization
- Publication figures
- Analysis tools

### **v0.3 🚧 PLANNED**
- Graph neural network implementation
- Property prediction model
- Training pipeline

### **v0.4 🔮 FUTURE**
- Band structure prediction
- Density of states visualization
- Device performance optimization

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📞 Support

For issues, questions, or suggestions:
- 🐛 [GitHub Issues](https://github.com/hasandafa/s-cgcnn/issues)
- 📧 Email the author
- 💬 Discussion forum (coming soon)

---

**✨ Enjoy exploring AlₓGa₁₋ₓAs properties with s-CGCNN v0.2!**