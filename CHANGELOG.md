# Changelog

All notable changes to s-CGCNN project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.1] - 2025-Q4

### 🎉 Major Features Added

#### Dual Data Source Support
- **Added** `interpolation.mode` configuration: choose between "literature" or "mp_api"
- **Added** `MPFetcher.fetch_all_properties()` for comprehensive property retrieval from MP API
- **Added** Automatic fallback to literature values when MP data unavailable
- **Added** `constants.get_properties()` function with data source parameter

#### Enhanced Property Calculation
- **Added** Band gap correction for DFT underestimation (scissor shift method)
- **Added** Configurable correction factor (default: 1.5x)
- **Added** MP-API property dictionaries in constants.py
- **Added** Support for 10+ new properties from MP API:
  - Formation energy per atom
  - Energy above hull (stability metric)
  - Full elastic tensor (C11, C12, C44)
  - Dielectric constants (static, electronic, ionic)
  - Magnetic properties
  - Thermodynamic properties

#### Comparison Mode
- **Added** `run_comparison_mode.py` script for side-by-side analysis
- **Added** Statistical comparison of literature vs MP-API results
- **Added** CSV export of comparison table
- **Added** JSON summary with mean, std, RMSE metrics

#### Structure & Organization
- **Added** Package-level `__init__.py` files for proper module structure
- **Added** Factory functions: `create_fetcher_from_config()`, `create_interpolator_from_config()`
- **Added** Data classes: `AlloyComposition`, `AlloyProperties`
- **Added** Type hints: `DataSourceType = Literal["literature", "mp_api"]`

#### Testing
- **Added** Comprehensive test suite `test_v0.1.1_complete.py`
- **Added** Tests for both literature and MP-API modes
- **Added** File I/O operation tests
- **Added** Automated test report generation

#### Documentation
- **Added** Complete `README_v0.1.1.md` with detailed usage guide
- **Added** Configuration guide with all options explained
- **Added** Troubleshooting section
- **Added** Citation information
- **Added** This CHANGELOG.md

### 🔧 Changed

#### Configuration
- **Changed** Config file to `config_v0.1.1.yaml` with enhanced structure
- **Changed** Added `mp_bandgap_correction` section
- **Changed** Added `comparison` section for comparison mode
- **Changed** Reorganized property lists by category

#### Core Modules
- **Changed** `constants.py` now has separate dictionaries for literature and MP-API
- **Changed** `structure_interpolator.py` now accepts `data_source` parameter
- **Changed** `mp_fetcher.py` enhanced with comprehensive property fetching
- **Changed** All functions use consistent `snake_case` naming

#### Pipeline Scripts
- **Changed** `run_version_0.1.1.py` with command-line mode override
- **Changed** Enhanced logging with data source information
- **Changed** Summary reports now include data source metadata

### 📊 Improved

#### Property Coverage
- **Improved** Band gap values now properly sourced (literature: 1.424 eV GaAs, MP-API: ~0.19 eV raw)
- **Improved** Direct-to-indirect transition handling (x = 0.45 crossover)
- **Improved** Bowing parameter implementation for Vegard's Law

#### Error Handling
- **Improved** Graceful fallback when MP-API properties unavailable
- **Improved** Try-except blocks for API connection issues
- **Improved** Detailed error messages and warnings

#### Code Quality
- **Improved** Type hints throughout codebase
- **Improved** Docstrings for all classes and functions
- **Improved** Consistent naming conventions
- **Improved** Modular architecture with clear separation of concerns

### 🐛 Fixed
- **Fixed** Potential issues with MP-API version compatibility (v0.41.2+)
- **Fixed** VBM/CBM float handling when MP returns unexpected format
- **Fixed** None value handling in property interpolation
- **Fixed** Composition rounding for discrete supercell values

### ⚠️ Important Notes

#### Data Source Selection
- **Literature mode (default)**: Recommended for device engineering
  - Uses experimental values (room temperature, 300K)
  - Accurate for HEMT, laser, solar cell design
  
- **MP-API mode**: Recommended for computational studies
  - Uses DFT-GGA calculated values (0K)
  - Requires band gap correction (enabled by default)
  - Includes thermodynamic stability data

#### Breaking Changes
- None (v0.1.1 is backward compatible with v0.1.0 workflows)
- Old `run_v0.1.py` scripts still work
- New features are opt-in via configuration

### 📦 Dependencies
- **Updated** `requirements.txt` with version specifications
- **Required** `mp-api==0.41.2` (fixed version)
- **Required** `pandas` for comparison mode
- **Required** Python 3.10+ (not 3.13)

---

## [0.1.0] - 2024-Q4

### 🎉 Initial Release

#### Core Features
- **Added** Materials Project API integration for GaAs and AlAs structures
- **Added** Structure interpolation via ordered supercell (2×2×2)
- **Added** 41 AlₓGa₁₋ₓAs composition generation (x = 0.0 to 1.0, step 0.025)
- **Added** Property calculation using Vegard's Law with bowing parameters
- **Added** 22 properties per composition:
  - Physical: lattice constant, density, thermal expansion
  - Electronic: band gap, effective masses, electron affinity
  - Optical: dielectric constants, refractive index
  - Mechanical: elastic constants, bulk modulus, Young's modulus
  - Thermal: thermal conductivity, specific heat, Debye temperature
  - Transport: electron mobility, hole mobility

#### Data Source
- **Added** Literature-based properties from ioffe.ru
- **Added** Experimental values at 300K (room temperature)
- **Added** Direct-to-indirect band gap transition at x = 0.45

#### Output Formats
- **Added** CIF file generation for all compositions
- **Added** JSON metadata with complete property sets
- **Added** Summary reports

#### Testing
- **Added** 4 test categories (100% pass rate)
- **Added** API connection test
- **Added** Structure generation test
- **Added** Property calculation test
- **Added** File output test

#### Documentation
- **Added** Complete project documentation (~15,000 words)
- **Added** 3 Jupyter notebooks for exploration
- **Added** README with installation and usage guide

#### Project Structure
- **Added** Modular architecture (src/data_acquisition, src/utils)
- **Added** Configuration system (YAML)
- **Added** Logging infrastructure
- **Added** Version control ready (gitignore)

---

## [Unreleased] - Future Plans

### Version 0.2 (Next - 2-3 weeks)
- Interactive 3D structure viewer (crystal-toolkit + Dash)
- Property evolution plots (Plotly)
- Publication-quality figures
- Band structure & DOS visualization
- Enhanced Jupyter notebooks

### Version 0.3 (Planned)
- Graph neural network preprocessing
- PyTorch Geometric data conversion
- Feature engineering
- Dataset preparation for ML

### Version 0.4 (Planned)
- s-CGCNN architecture (CPU-optimized)
- Multi-task learning implementation
- Cross-validation training
- Model evaluation metrics

### Version 0.5 (Planned)
- Band structure/DOS prediction
- Full property prediction pipeline
- Uncertainty quantification
- Model interpretability

### Version 1.0 (Target - Stable Release)
- Device recommendation system
- Complete end-to-end pipeline
- Production deployment ready
- Publication-ready results

---

## Version Numbering

Format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible API changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Current: **v0.1.1** (Minor feature release)

---

## Contributing

See individual version sections for changes. For contribution guidelines, see README.md.

---

*Last updated: 2025-Q4*