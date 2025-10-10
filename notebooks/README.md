# 📓 Jupyter Notebooks - s-CGCNN v0.1

Interactive tutorials and demonstrations for AlGaAs data acquisition and analysis.

---

## 📋 Notebook Overview

| Notebook | Description | Time | Prerequisites |
|----------|-------------|------|---------------|
| **01_Data_Fetching_Demo.ipynb** | Fetch GaAs & AlAs from Materials Project | ~5 min | API key |
| **02_Structure_Interpolation_Demo.ipynb** | Generate 41 AlGaAs structures | ~5 min | Notebook 01 |
| **03_Property_Analysis.ipynb** | Comprehensive property analysis | ~10 min | Notebook 02 |

**Total time:** ~20 minutes for all notebooks

---

## 🚀 Quick Start

### 1. Launch Jupyter

```bash
# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Start Jupyter
jupyter notebook
```

This will open Jupyter in your browser at `http://localhost:8888`

### 2. Navigate to Notebooks

In the Jupyter interface:
1. Click `notebooks/` folder
2. Open `01_Data_Fetching_Demo.ipynb`
3. Run cells sequentially (Shift+Enter)

### 3. Run in Order

**Important:** Run notebooks in sequence:
1. First: 01_Data_Fetching_Demo
2. Second: 02_Structure_Interpolation_Demo
3. Third: 03_Property_Analysis

Each notebook builds on the previous one.

---

## 📖 Notebook Details

### 01_Data_Fetching_Demo.ipynb

**Purpose:** Fetch and explore GaAs and AlAs data from Materials Project

**What you'll learn:**
- How to use MPDataFetcher
- Accessing Materials Project API
- Exploring crystal structures
- Comparing GaAs vs AlAs properties

**Outputs:**
- `data/raw/mp_2534_GaAs.json`
- `data/raw/mp_2172_AlAs.json`

**Key sections:**
1. API setup and initialization
2. Data fetching (or loading if cached)
3. Property exploration
4. Side-by-side comparison

---

### 02_Structure_Interpolation_Demo.ipynb

**Purpose:** Generate AlₓGa₁₋ₓAs alloy structures through interpolation

**What you'll learn:**
- Ordered supercell method
- Ga→Al substitution
- Vegard's Law application
- Band gap evolution
- Direct-to-indirect crossover

**Outputs:**
- 41 CIF files (`data/structures/cif/`)
- 41 metadata JSON files (`data/structures/metadata/`)

**Key sections:**
1. Structure interpolator setup
2. Sample structure generation
3. Composition verification
4. Lattice constant evolution
5. Band gap analysis with crossover
6. Batch generation of all 41 structures

**Visualizations:**
- Composition accuracy plot
- Lattice constant (Vegard's Law)
- Band gap with direct/indirect transition
- Multi-property dashboard

---

### 03_Property_Analysis.ipynb

**Purpose:** Deep dive into property trends across all compositions

**What you'll learn:**
- Property evolution patterns
- Correlation analysis
- Device-relevant property combinations
- Optimal composition identification

**Outputs:**
- `results/algaas_properties_analysis.csv`
- `results/property_summary_statistics.csv`

**Key sections:**
1. Load all 41 compositions
2. Electronic properties (band gap, affinity, dielectric, mobility)
3. Mechanical properties (elastic constants, moduli)
4. Thermal properties (conductivity, expansion)
5. Transport properties (carrier mobility)
6. Correlation heatmap
7. Device recommendations

**Visualizations:**
- 10+ property evolution plots
- Correlation matrix heatmap
- Device-relevant scatter plots
- Mobility analysis (log scale)

**Device Analysis:**
- HEMT (High mobility candidates)
- Laser diodes (Direct gap range)
- Solar cells (Optimal band gap)
- Microprocessors (Mobility + thermal)

---

## 💡 Tips for Using Notebooks

### Running Cells

- **Run current cell:** `Shift + Enter`
- **Run and stay:** `Ctrl + Enter`
- **Insert cell below:** `B`
- **Insert cell above:** `A`
- **Delete cell:** `D + D` (press D twice)

### If Something Fails

1. **Restart kernel:** `Kernel → Restart & Clear Output`
2. **Run all cells:** `Cell → Run All`
3. **Check prerequisites:** Make sure previous notebooks were run

### Customization

Feel free to:
- Modify x values in interpolation
- Change plot styles
- Add your own analysis
- Export additional data

---

## 📊 Expected Outputs

After running all three notebooks:

```
data/
├── raw/
│   ├── mp_2534_GaAs.json          ← From Notebook 01
│   └── mp_2172_AlAs.json
│
└── structures/
    ├── cif/
    │   └── AlGaAs_x_*.cif (41 files)  ← From Notebook 02
    └── metadata/
        └── AlGaAs_x_*.json (41 files)

results/
├── algaas_properties_analysis.csv     ← From Notebook 03
└── property_summary_statistics.csv
```

---

## 🐛 Troubleshooting

### Issue: Kernel dies / Out of memory

**Solution:** You're likely running multiple notebooks. Close other notebooks or restart kernel.

### Issue: API key not found

**Solution:** 
```bash
echo "YOUR_API_KEY" > config/mp_api_key.txt
```

### Issue: Module not found

**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: Matplotlib plots not showing

**Solution:** Add to first cell:
```python
%matplotlib inline
```

### Issue: "No data found" in Notebook 02 or 03

**Solution:** Run previous notebooks first in order.

---

## 📚 Additional Resources

### Jupyter Basics
- Official docs: https://jupyter-notebook.readthedocs.io
- Keyboard shortcuts: Help → Keyboard Shortcuts
- Markdown guide: Help → Markdown Reference

### Python Scientific Stack
- NumPy: https://numpy.org/doc/
- Pandas: https://pandas.pydata.org/docs/
- Matplotlib: https://matplotlib.org/stable/contents.html

### Materials Science
- PyMatGen: https://pymatgen.org
- Materials Project: https://materialsproject.org

---

## 🎯 Learning Goals

By completing these notebooks, you will:

✅ Understand Materials Project API usage  
✅ Learn structure interpolation techniques  
✅ Master Vegard's Law and bowing parameters  
✅ Analyze electronic, mechanical, thermal properties  
✅ Identify optimal compositions for devices  
✅ Gain hands-on experience with AlGaAs system

---

## 🔜 What's Next?

After mastering Version 0.1 notebooks:

**Version 0.2 Notebooks** (coming soon):
- Interactive 3D structure visualization
- Advanced property plotting
- Publication-quality figure generation

**Version 0.3+ Notebooks:**
- Graph neural network preprocessing
- Model training and evaluation
- Device recommendation system

---

## 💬 Feedback

Found an issue or have suggestions?
- Open an issue on GitHub
- Check existing documentation
- Run the test suite for validation

---

**Happy Learning!** 📓✨

Last Updated: 2025-10-10  
Version: 0.1.0