# Quick Start - Material-Agnostic System

## 🚀 Your Code Now Works With ANY Binary Alloy!

---

## For Existing Code (AlGaAs)

**Breaking Change:** Existing code must be updated to explicitly specify materials:

```python
from src.calculation.main import run_full_pipeline

# OLD CODE (no longer works):
# results = run_full_pipeline()

# NEW CODE (required):
results = run_full_pipeline(
    alloy_system="AlGaAs",
    material1="GaAs",
    material2="AlAs"
)
```

---

## Adding InGaAs (5-Minute Guide)

### 1. Get InAs Properties
Look up InAs properties from literature (Adachi handbook, etc.)

### 2. Create InAs.yaml
Copy and edit the template:
```bash
cp materials/properties/InAs_TEMPLATE.yaml materials/properties/InAs.yaml
# Edit InAs.yaml - replace EXAMPLE values with real data
```

### 3. Create InGaAs.yaml
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
  band_gap: 0.477  # eV for InGaAs
  lattice_constant: 0.0
  # ... fill in others (use 0.0 for linear)
```

### 4. Run Your Pipeline
```python
results = run_full_pipeline(
    alloy_system="InGaAs",
    material1="GaAs",
    material2="InAs"
)
```

**Done!** 🎉 No code changes needed!

---

## Key Points

### ✅ What Works Out of the Box
- Property calculations (Vegard's Law with bowing)
- Electronic structure (tight-binding)
- Structure generation (automatic element detection)
- File saving (generic naming)

### 📁 What You Need to Provide
1. Material YAML files with properties
2. Alloy YAML with bowing parameters
3. (Optional) CHGCAR files for charge density
4. Material data in `data/mp-XXXXX/` directory

---

## Examples

### Example 1: AlGaAs (Explicit)
```python
results = run_full_pipeline(
    alloy_system="AlGaAs",
    material1="GaAs",
    material2="AlAs"
)
```

### Example 2: InGaAs
```python
results = run_full_pipeline(
    alloy_system="InGaAs",
    material1="GaAs",
    material2="InAs"
)
```

### Example 3: AlGaN
```python
results = run_full_pipeline(
    alloy_system="AlGaN",
    material1="GaN",
    material2="AlN"
)
```

### Example 4: Custom Composition Points
```python
results = run_full_pipeline(
    alloy_system="InGaAs",
    material1="GaAs",
    material2="InAs",
    x_values=[0.0, 0.1, 0.2, 0.3, 0.53, 1.0]  # Custom points
)
```

---

## File Locations

```
materials/properties/
├── GaAs.yaml          ← Your material properties
├── AlAs.yaml          ← Your material properties
├── AlGaAs.yaml        ← Your alloy config
└── InAs_TEMPLATE.yaml ← Template for new materials

config.yaml            ← System configuration

data/
├── mp-2534/           ← GaAs data
├── mp-2172/           ← AlAs data
└── mp-XXXXX/          ← Your new material data

src/calculation/
└── main.py            ← Your entry point (now material-agnostic)
```

---

## Validation

Test your new material:

```bash
python test_materials_system.py
```

Or manually:

```python
from materials import MaterialLoader

loader = MaterialLoader()

# Check material loads
inas = loader.load_material("InAs")
print(f"InAs band gap: {inas.get_property('band_gap', 'literature')} eV")

# Check alloy system
ingaas = loader.load_alloy_system("InGaAs")
print(f"InGaAs bowing: {ingaas.get_bowing_parameter('band_gap')} eV")
```

---

## Common Issues & Solutions

### Issue: Material not found
**Solution:** Check that `YourMaterial.yaml` exists in `materials/properties/`

### Issue: Property is None
**Solution:** Verify property is defined in the YAML file under correct category

### Issue: CHGCAR not found
**Solution:** Either add CHGCAR file or disable charge density:
```python
results = run_full_pipeline(enable_all_features=False)
# Or set in config.yaml: features.enable_charge_density: false
```

### Issue: Import errors
**Solution:** Install dependencies:
```bash
pip install pymatgen pyyaml numpy scipy
```

---

## 📖 More Information

- **REFACTORING_GUIDE.md** - Complete technical documentation
- **MIGRATION_SUMMARY.md** - Executive summary of changes
- **materials/properties/README.md** - Material file format guide
- **test_materials_system.py** - Working examples

---

## 💡 Pro Tips

1. **Start Simple:** Test with existing AlGaAs first (with explicit parameters)
2. **Use Templates:** Copy InAs_TEMPLATE.yaml as starting point
3. **Validate Early:** Run tests after adding each material
4. **Check MP-IDs:** Verify Materials Project IDs are correct
5. **Linear First:** Use bowing=0.0 initially, refine later
6. **Update Code:** All existing code needs explicit material specification

---

**Happy Researching! 🔬**

Now you can study **any III-V semiconductor alloy** with the same pipeline!