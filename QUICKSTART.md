# 🚀 Quick Start Guide - s-CGCNN v0.1

Get up and running with s-CGCNN in 5 minutes!

---

## ✅ Prerequisites

- Python 3.8 or higher
- Materials Project API key ([get it here](https://next-gen.materialsproject.org/api))
- ~500 MB free disk space

---

## 📥 Step 1: Clone & Setup

```bash
# Clone repository
git clone https://github.com/hasandafa/s-cgcnn.git
cd s-cgcnn

# Checkout Version 0.1
git checkout version-0.1

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

---

## 📦 Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Installation time:** ~3-5 minutes

---

## 🔑 Step 3: Configure API Key

```bash
# Create config directory (if doesn't exist)
mkdir -p config

# Add your API key
echo "YOUR_MATERIALS_PROJECT_API_KEY" > config/mp_api_key.txt
```

**Get your API key:**
1. Visit https://next-gen.materialsproject.org/api
2. Sign in / Create account
3. Copy API key from dashboard

---

## 🏃 Step 4: Run First Test

```bash
python "1. Data Acquisition and Structure Interpolation Testing.py"
```

**What happens:**
1. ⬇️ Fetches GaAs & AlAs from Materials Project
2. 🔄 Generates 41 AlGaAs structures
3. 📊 Calculates properties for each composition
4. ✅ Validates all data
5. 📄 Generates report

**Expected time:** 2-3 minutes

**Expected output:**
```
✓✓✓ ALL TESTS PASSED - VERSION 0.1 READY ✓✓✓
```

---

## 📂 Step 5: Check Outputs

After successful run, you'll have:

```
data/
├── raw/
│   ├── mp_2534_GaAs.json      ← GaAs data
│   └── mp_2172_AlAs.json      ← AlAs data
└── structures/
    ├── cif/
    │   ├── AlGaAs_x_0_000.cif  ← 41 CIF files
    │   ├── AlGaAs_x_0_025.cif
    │   └── ...
    └── metadata/
        ├── AlGaAs_x_0_000.json ← Property data
        └── generation_summary.json
```

---

## 🎯 Next Steps

### Explore Your Data

**View a structure:**
```python
from pymatgen.core import Structure

# Load any composition
structure = Structure.from_file("data/structures/cif/AlGaAs_x_0_500.cif")
print(structure)
```

**Check properties:**
```python
import json

# Load metadata
with open("data/structures/metadata/AlGaAs_x_0_500.json", 'r') as f:
    data = json.load(f)

print(f"Band gap: {data['properties']['band_gap']:.3f} eV")
print(f"Type: {data['properties']['band_gap_type']}")
```

### View Summary

```python
import json

with open("data/structures/metadata/generation_summary.json", 'r') as f:
    summary = json.load(f)

print(f"Total structures: {summary['total_structures']}")
print(f"Band gap range: {summary['properties_summary']['band_gap']}")
```

---

## 🐛 Troubleshooting

### Problem: `ImportError: No module named 'mp_api'`

**Solution:**
```bash
pip install --upgrade mp-api pymatgen
```

### Problem: `FileNotFoundError: config/mp_api_key.txt`

**Solution:**
```bash
echo "YOUR_API_KEY_HERE" > config/mp_api_key.txt
```

### Problem: `API key invalid`

**Solution:**
1. Verify key at https://next-gen.materialsproject.org/api
2. Ensure no extra spaces in `mp_api_key.txt`
3. Try regenerating API key

### Problem: `Test failed - MP data not fetched`

**Solution:**
```bash
# Run fetcher directly
python -c "from src.data_acquisition.mp_fetcher import MPDataFetcher; import sys; with open('config/mp_api_key.txt') as f: key=f.read().strip(); fetcher=MPDataFetcher(key); fetcher.fetch_all_materials()"
```

---

## 📚 What's Next?

Version 0.1 complete! Move to:

**Version 0.2:** Crystal Structure Visualization
- Interactive 3D structure viewer
- Property comparison plots
- Academic-style figures

Check `README_v0.2.md` (coming soon)

---

## 💬 Need Help?

- 📖 Full documentation: `README_v0.1.md`
- 🐛 Issues: GitHub Issues
- 📧 Contact: [Your Email/GitHub]

---

## ⏱️ Time Summary

| Task | Duration |
|------|----------|
| Setup & Install | 5 minutes |
| First Run | 2-3 minutes |
| **Total** | **~8 minutes** |

---

**Happy AlGaAs screening! 🎉**