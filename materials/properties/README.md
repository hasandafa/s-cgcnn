# Materials Properties Directory

This directory contains YAML configuration files for all materials and alloy systems supported by the pipeline.

## File Structure

### Binary Materials
Each binary material (e.g., GaAs, AlAs, InAs) has its own YAML file containing:
- Literature properties (experimental, 300K)
- Materials Project API properties (DFT, 0K)
- Tight-binding parameters (sp³s* model)
- Property units and metadata

**Files:**
- `GaAs.yaml` - Gallium Arsenide
- `AlAs.yaml` - Aluminum Arsenide

### Alloy Systems
Each alloy system (e.g., AlGaAs, InGaAs) has its own YAML file containing:
- Binary endpoint definitions
- Bowing parameters (Vegard deviation)
- Band gap transition information
- Composition-dependent rules
- Application recommendations

**Files:**
- `AlGaAs.yaml` - Aluminum Gallium Arsenide alloy system

## Adding New Materials

### Step 1: Create Binary Material YAML

Create a new file `YourMaterial.yaml` with the following structure:

```yaml
material:
  name: "YourMaterial"
  formula: "ABC"
  mp_id: "mp-XXXX"  # Materials Project ID
  structure_type: "zincblende"  # or wurtzite, rocksalt, etc.
  space_group: "F-43m"

literature:
  source: "Your reference paper/book"
  temperature: 300  # K
  
  physical:
    lattice_constant: 5.6533  # Å
    density: 5.3175  # g/cm³
    thermal_expansion: 6.03e-6  # K⁻¹
  
  electronic:
    band_gap: 1.43  # eV
    band_gap_type: "direct"  # or "indirect"
    electron_affinity: 4.07  # eV
    effective_mass_electron: 0.067  # m₀
    effective_mass_hole_heavy: 0.5  # m₀
    effective_mass_hole_light: 0.08  # m₀
  
  optical:
    dielectric_constant_static: 12.9
    dielectric_constant_high_freq: 10.86
    refractive_index: 3.628
  
  mechanical:
    bulk_modulus: 75.5  # GPa
    elastic_constant_c11: 118.8  # GPa
    elastic_constant_c12: 53.8  # GPa
    elastic_constant_c44: 59.4  # GPa
  
  thermal:
    thermal_conductivity: 0.45  # W/(cm·K)
    specific_heat: 0.327  # J/(g·K)
  
  transport:
    electron_mobility: 8500.0  # cm²/(V·s)
    hole_mobility: 400.0  # cm²/(V·s)

mp_api:
  source: "materialsproject.org"
  temperature: 0  # K
  mp_id: "mp-XXXX"
  formula: "ABC"
  
  physical:
    lattice_constant: null  # Fetch from API
    density: null
  
  electronic:
    band_gap: null  # DFT underestimates
    band_gap_type: "direct"
  
  mechanical:
    bulk_modulus: null
  
  optical:
    dielectric_constant_static: null

tight_binding:
  method: "Slater-Koster sp³s*"
  source: "Your reference for TB parameters"
  
  parameters:
    Es_cation: -8.3414  # eV
    Es_anion: -8.3431  # eV
    Ep_cation: 1.0414  # eV
    Ep_anion: 1.7023  # eV
    Ess: -6.4513  # eV
    Esp: 4.48  # eV
    Epp_sigma: 1.9546  # eV
    Epp_pi: -4.2588  # eV
    a: 5.6533  # Å
```

### Step 2: Create Alloy System YAML (if making an alloy)

Create `YourAlloy.yaml`:

```yaml
alloy_system:
  name: "YourAlloy"
  formula: "A_x B_{1-x} C"
  type: "ternary_alloy"
  binary_endpoints:
    - material: "Material1"  # x=0
      composition_var: "x"
      x_value: 0.0
    - material: "Material2"  # x=1
      composition_var: "x"
      x_value: 1.0

bowing_parameters:
  band_gap: 0.37  # eV
  lattice_constant: 0.0
  electron_affinity: 0.0
  effective_mass_electron: 0.0
  # ... other properties with bowing=0.0 for linear

band_gap_transition:
  crossover_composition: 0.45
  direct_range: [0.0, 0.45]
  indirect_range: [0.45, 1.0]
  description: "Direct to indirect transition"

defaults:
  data_source: "literature"
  supercell_size: [2, 2, 2]
  enable_tight_binding: true
```

### Step 3: Use Your New Material

```python
from src.calculation.main import run_full_pipeline

# Run pipeline with your new alloy
results = run_full_pipeline(
    alloy_system="YourAlloy",
    material1="Material1",
    material2="Material2"
)
```

**That's it! No code changes needed!**

## Example: InGaAs System

To add InGaAs support:

1. Create `InAs.yaml` with InAs properties (similar to GaAs.yaml)
2. Create `InGaAs.yaml` with alloy parameters (similar to AlGaAs.yaml)
3. Add InAs data to `data/mp-XXXX/` directory
4. Run:
```python
results = run_full_pipeline(
    alloy_system="InGaAs",
    material1="GaAs",
    material2="InAs"
)
```

## Property Categories

Properties are organized into categories:

- **physical**: lattice_constant, density, thermal_expansion
- **electronic**: band_gap, effective_mass_*, electron_affinity
- **optical**: dielectric_constant_*, refractive_index
- **mechanical**: elastic_constant_*, bulk_modulus, shear_modulus
- **thermal**: thermal_conductivity, specific_heat, debye_temperature
- **transport**: electron_mobility, hole_mobility

## Data Sources

### Literature Source
- Experimental values at 300K
- Most accurate for device applications
- Limited to measured properties
- Sources: Adachi handbooks, research papers

### MP-API Source
- DFT calculations at 0K
- Comprehensive property set
- Band gaps underestimated by 30-50%
- Requires corrections for practical use

## Tight-Binding Parameters

The sp³s* Slater-Koster tight-binding model requires 9 parameters:
- `Es_cation`, `Es_anion`: On-site s-orbital energies
- `Ep_cation`, `Ep_anion`: On-site p-orbital energies
- `Ess`: s-s hopping integral
- `Esp`: s-p hopping integral
- `Epp_sigma`: p-p sigma hopping
- `Epp_pi`: p-p pi hopping
- `a`: Lattice constant for TB calculations

Reference: Jancu et al., Phys. Rev. B 57, 6493 (1998)

## Bowing Parameters

For alloys, bowing parameters describe deviation from linear (Vegard's Law):

**Formula:** `P(x) = (1-x)P₁ + xP₂ - b·x·(1-x)`

Where:
- `P(x)` = property at composition x
- `P₁, P₂` = endpoint values
- `b` = bowing parameter

Common values:
- Band gap: 0.37 eV (AlGaAs)
- Lattice constant: 0.0 (typically linear)
- Most mechanical properties: 0.0

## Validation

After adding new materials, validate with:

```bash
python test_materials_system.py
```

Or use Python:

```python
from materials import MaterialLoader

loader = MaterialLoader()
material = loader.load_material("YourMaterial")
print(material.get_property("band_gap", "literature"))
```

## References

### Data Sources
- Adachi, S. (2012). Handbook on Optical Constants of Semiconductors
- Adachi, S. (2005). Properties of Group-IV, III-V and II-VI Semiconductors
- Materials Project: https://materialsproject.org

### Tight-Binding
- Jancu et al., Phys. Rev. B 57, 6493 (1998)
- Vogl et al., J. Phys. Chem. Solids 44, 365 (1983)