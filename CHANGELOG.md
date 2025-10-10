# Changelog

All notable changes to s-CGCNN will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned for v0.2
- Interactive crystal structure visualization (crystal-toolkit)
- Property comparison plots (plotly)
- Academic-style figure generation
- Enhanced data export options

### Planned for v0.3
- Graph neural network data preprocessing
- PyTorch Geometric graph conversion
- Property feature engineering
- Dataset splitting utilities

### Planned for v0.4
- Simplified CGCNN architecture implementation
- CPU-optimized training pipeline
- Cross-validation framework
- Model checkpointing

### Planned for v0.5
- Band structure prediction
- DOS prediction
- Materials Project style visualization
- Brillouin zone plotting

### Planned for v1.0
- Device recommendation system
- Comprehensive evaluation metrics
- Full pipeline integration
- Production-ready deployment

---

## [0.1.0] - 2025-10-10

### 🎉 Initial Release - Data Acquisition & Structure Interpolation

#### Added
- **Materials Project Integration**
  - `MPDataFetcher` class for API communication
  - Automatic fetching of GaAs (mp-2534) and AlAs (mp-2172)
  - Property extraction (band gap, density, elastic tensor, dielectric)
  - JSON export for fetched data
  - Cached data loading to avoid redundant API calls

- **Structure Interpolation**
  - `StructureInterpolator` class for alloy generation
  - Ordered supercell method (2×2×2 default)
  - 41 compositions (x = 0.0 to 1.0, step 0.025)
  - Systematic Ga→Al substitution
  - Lattice parameter adjustment via Vegard's Law

- **Property Calculation**
  - Comprehensive property interpolation with bowing parameters
  - Physical: lattice constant, density, elastic constants, bulk/shear modulus
  - Electronic: band gap (direct/indirect), electron affinity, effective masses, dielectric constants, refractive index
  - Thermal: conductivity, expansion, specific heat, Debye temperature
  - Transport: electron/hole mobility estimates
  - Direct-to-indirect band gap crossover at x ≈ 0.45

- **Constants & Reference Data**
  - Extensive AlGaAs property database from ioffe.ru
  - Bowing parameters from literature
  - Brillouin zone k-path definitions
  - Atomic data (masses, radii, numbers)
  - Utility functions for property calculation

- **Data Export**
  - CIF file generation for all 41 structures
  - JSON metadata with full property sets
  - Generation summary statistics
  - Organized directory structure

- **Logging & Configuration**
  - YAML-based configuration system
  - Comprehensive logging framework
  - Tqdm-compatible logging for progress bars
  - Multiple log levels (DEBUG, INFO, WARNING, ERROR)

- **Testing Framework**
  - Comprehensive test suite for v0.1
  - 4 test categories: MP fetching, structure generation, property calculation, data validation
  - Automated validation of all outputs
  - JSON test reports

- **Documentation**
  - Complete README with installation guide
  - Quick start guide (< 10 minutes setup)
  - Git workflow documentation
  - Code comments and docstrings
  - Troubleshooting guide

- **Pipeline Automation**
  - `run_version_0.1.py` for end-to-end execution
  - Prerequisite checking
  - Step-by-step progress display
  - Error handling and recovery
  - Execution timing and summary

- **Package Structure**
  - Proper Python package with setup.py
  - Organized module structure
  - Entry points for CLI usage
  - Requirements specification

#### Technical Specifications
- **Python Version**: >=3.8
- **Dependencies**: 
  - Core: numpy, pandas, scipy
  - Materials: pymatgen, mp-api, matminer
  - ML: torch, torch-geometric (prepared for future)
  - Visualization: plotly, matplotlib (prepared for v0.2)
- **API**: Materials Project API v0.41+
- **Data Format**: CIF (structures), JSON (metadata)
- **Supercell**: 2×2×2 (16 atoms)
- **Compositions**: 41 (Δx = 0.025)

#### Validated
- ✅ Materials Project API connectivity
- ✅ Structure generation accuracy
- ✅ Property interpolation correctness
- ✅ Data integrity and completeness
- ✅ Bowing parameter implementation
- ✅ Direct-indirect crossover at x=0.45
- ✅ CIF file validity
- ✅ Metadata consistency

#### Known Limitations
- Supercell size fixed at 2×2×2 (sufficient for ordered structures)
- Linear interpolation with bowing (no cluster expansion)
- Band structure not yet predicted (only band gap values)
- Transport properties are estimates (not DFT-derived)
- CPU-only operation (GPU support in future versions)

#### Performance
- **Fetch Time**: ~30-60 seconds (one-time, with caching)
- **Generation Time**: ~60-120 seconds (41 structures)
- **Total Pipeline**: ~2-3 minutes
- **Disk Usage**: ~50 MB for complete dataset

---

## Version Roadmap

### v0.1.0 ✅ (Current)
Data acquisition and structure interpolation

### v0.2.0 🚧 (Next)
Structure visualization and property plotting

### v0.3.0 📋 (Planned)
Graph building and feature engineering

### v0.4.0 📋 (Planned)
s-CGCNN model architecture and training

### v0.5.0 📋 (Planned)
BS/DOS prediction and visualization

### v1.0.0 🎯 (Target)
Complete device recommendation system

---

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m 'Add YourFeature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

---

## Citation

If you use s-CGCNN in your research, please cite:

```bibtex
@software{scgcnn2025,
  author = {Dafa, Abdullah Hasan},
  title = {s-CGCNN: Simplified Graph Neural Networks for CPU-Efficient Screening of AlGaAs Alloys},
  year = {2025},
  url = {https://github.com/hasandafa/s-cgcnn},
  version = {0.1.0}
}
```

---

## License

© 2025 Abdullah Hasan Dafa. All rights reserved.

---

## Links

- **Repository**: https://github.com/hasandafa/s-cgcnn
- **Issues**: https://github.com/hasandafa/s-cgcnn/issues
- **Materials Project**: https://materialsproject.org
- **Ioffe Database**: https://www.ioffe.ru/SVA/NSM/Semicond/AlGaAs/

---

**Last Updated**: 2025-10-10