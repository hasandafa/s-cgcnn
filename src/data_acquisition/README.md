# Data Acquisition Module

The `src/data_acquisition/` module handles fetching, validating, and processing materials data from external sources, primarily the Materials Project API. This module provides a robust pipeline for acquiring high-quality crystal structure and electronic structure data.

## Overview

This module enables:
- **API Data Fetching**: Automated retrieval of materials data from Materials Project
- **Data Validation**: Comprehensive validation of fetched data quality
- **CIF Processing**: Crystal structure analysis from CIF files
- **Caching**: Smart caching to avoid redundant API calls
- **Parallel Processing**: Efficient batch data acquisition

## Key Features

- **Materials Project Integration**: Official MPRester API client
- **Comprehensive Validation**: Structure, band structure, phonon, and charge density validation
- **Crystal Structure Analysis**: CIF file processing and metadata extraction
- **Smart Caching**: Time-based cache with automatic invalidation
- **Parallel Fetching**: Multi-threaded data acquisition
- **Provenance Tracking**: Complete data lineage and validation metadata

## Module Structure

### Core Files

| File | Purpose |
|------|---------|
| `data_acquisition.py` | Materials Project API scraper with caching |
| `validator.py` | Comprehensive data validation and quality checks |
| `cif_processor.py` | CIF file processing and crystal structure analysis |
| `__init__.py` | Module initialization and public API |

### Key Classes

- **`MaterialsProjectScraper`**: Handles API communication and data fetching
- **`DataValidator`**: Validates data quality and detects anomalies
- **`CIFProcessor`**: Processes CIF files and extracts crystal structure metadata
- **`MaterialData`**: Container for fetched material data
- **`ValidationResult`**: Validation results and anomaly reporting

## Quick Start

### Basic Data Fetching

```python
from src.data_acquisition import scrape_binary_compounds

# Fetch data for materials defined in config.yaml
results = scrape_binary_compounds()

for material_id, data in results.items():
    print(f"{material_id}: {data.formula}, Eg={data.band_gap} eV")
```

### Advanced Usage

```python
from src.data_acquisition import MaterialsProjectScraper

# Initialize scraper with custom settings
with MaterialsProjectScraper(api_key="your_key", cache_days=7) as scraper:
    # Fetch single material with all data types
    material_data = scraper.fetch_material_data(
        "mp-149",
        fetch_structure=True,
        fetch_bandstructure=True,
        fetch_dos=True,
        fetch_phonon=True,
        fetch_charge_density=True
    )

    # Save data
    scraper.save_material_data(material_data, "data/")
```

## Data Sources

### Materials Project API
- **Source**: https://materialsproject.org
- **Data Types**: Structures, band structures, DOS, phonons, charge density
- **Access**: Requires API key (free registration)
- **Rate Limits**: 2000 requests/day for academic users

### CIF Files
- **Format**: Crystallographic Information File (.cif)
- **Processing**: Automatic structure extraction and analysis
- **Metadata**: Lattice parameters, space groups, k-paths

## Data Validation

### Validation Checks

#### Structure Validation
- **Completeness**: Atom coordinates, lattice parameters
- **Quality**: Valid ranges, no missing data
- **Symmetry**: Space group determination
- **Composition**: Chemical formula verification

#### Band Structure Validation
- **K-points**: Valid k-path coverage
- **Energies**: Reasonable energy ranges
- **Labels**: High-symmetry point identification
- **Gap**: Band gap consistency

#### Phonon Validation
- **Frequencies**: No negative frequencies (imaginary modes)
- **K-path**: Complete Brillouin zone coverage
- **Stability**: Acoustic mode behavior

#### Charge Density Validation
- **Data Integrity**: Valid grid dimensions
- **Physical Values**: No negative densities
- **Format**: Compatible with VASP CHGCAR format

### Validation Results

```python
from src.data_acquisition import validate_material_data

result = validate_material_data(material_data)

print(f"Valid: {result.is_valid}")
print(f"Anomalies: {result.anomalies}")
print(f"Warnings: {result.warnings}")
print(f"Metadata: {result.metadata}")
```

## CIF Processing

### Crystal Structure Analysis

```python
from src.data_acquisition import process_all_materials

# Process all CIF files and update YAML metadata
success = process_all_materials(
    data_dir=Path("data"),
    properties_dir=Path("materials/properties")
)
```

### Extracted Metadata
- **Lattice Parameters**: a, b, c, α, β, γ
- **Space Group**: International symbol and number
- **Crystal System**: Cubic, hexagonal, tetragonal, etc.
- **K-path**: High-symmetry k-points for band structure
- **Basis Atoms**: Atomic positions and types

## Caching System

### Smart Caching
- **Time-based**: Configurable cache validity (default: 7 days)
- **Automatic**: Invalidates expired data
- **Disk Storage**: JSON format in cache directory
- **Metadata**: Cache timestamps and data sources

### Cache Management

```python
from src.utils import get_cache_manager

cache = get_cache_manager()

# Check if data is cached
if cache.is_cached("material_mp-149", days=7):
    entry = cache.get_entry("material_mp-149")
    # Load cached data
```

## Parallel Processing

### Multi-threaded Fetching

```python
# Automatic parallel fetching (up to 3 threads)
material_ids = ["mp-149", "mp-66", "mp-134"]
results = scraper.fetch_multiple_materials(material_ids)
```

### Jupyter Compatibility
- **Sequential Mode**: Automatic fallback in Jupyter notebooks
- **Context Issues**: Avoids asyncio context variable problems
- **Progress Tracking**: Individual material status reporting

## Configuration

### Config File (config.yaml)

```yaml
data_acquisition:
  cache_days: 7
  max_workers: 3
  rate_limit_delay: 0.2

system:
  binary_compounds:
    - mp_id: "mp-149"
      formula: "GaAs"
    - mp_id: "mp-66"
      formula: "AlAs"
```

### API Key Setup

1. **Register**: https://materialsproject.org/api
2. **Create**: `key.env` file with `your_api_key_here`
3. **Environment**: Or set `MATERIALS_PROJECT_API_KEY`

## Output Structure

```
data/
├── mp-149/
│   ├── material_data.json      # Complete material data
│   ├── mp-149.cif             # Crystal structure (CIF)
│   ├── mp-149_CHGCAR.vasp     # Charge density (VASP)
│   └── provenance.json        # Validation metadata
├── mp-66/
│   └── ...
└── cache/
    └── material_mp-149.json   # Cached data
```

## Data Formats

### Material Data JSON
```json
{
  "material_id": "mp-149",
  "formula": "GaAs",
  "structure": {...},
  "band_gap": 1.42,
  "is_gap_direct": true,
  "bandstructure": {...},
  "dos": {...},
  "phonon_bandstructure": {...},
  "charge_density": {...},
  "validation_result": {...}
}
```

### Provenance Metadata
```json
{
  "material_id": "mp-149",
  "fetch_timestamp": "2024-01-15T10:30:00Z",
  "api_version": "mp-api",
  "validation_result": {...},
  "data_sources": {
    "structure": true,
    "bandstructure": true,
    "dos": true,
    "phonon_bs": true,
    "charge_density": true
  }
}
```

## Error Handling

### Common Issues

1. **API Key Missing**: Set `MATERIALS_PROJECT_API_KEY` or create `key.env`
2. **Rate Limits**: Automatic rate limiting (200ms delays)
3. **Network Issues**: Automatic retry with exponential backoff
4. **Data Corruption**: Validation catches malformed data
5. **Cache Issues**: Automatic cache invalidation

### Error Recovery
- **Validation Failures**: Detailed anomaly reporting
- **Partial Data**: Continues with available data types
- **Cache Corruption**: Automatic cache cleanup
- **API Errors**: Graceful degradation to cached data

## Dependencies

### Required
- `mp-api`: Materials Project API client
- `pymatgen`: Crystal structure manipulation
- `requests`: HTTP client for API calls

### Optional
- `matplotlib`: Visualization (if available)
- `scipy`: Advanced data processing

## Examples

### Complete Pipeline

```python
from src.data_acquisition import scrape_binary_compounds
from src.data_acquisition import process_all_materials

# 1. Fetch data from Materials Project
materials_data = scrape_binary_compounds()

# 2. Process CIF files and update YAML metadata
process_all_materials()

# 3. Validate all fetched data
from src.data_acquisition import validate_material_data
for mat_id, data in materials_data.items():
    result = validate_material_data(data)
    if not result.is_valid:
        print(f"Validation failed for {mat_id}: {result.anomalies}")
```

### Custom Material Fetching

```python
# Fetch specific materials with custom options
with MaterialsProjectScraper() as scraper:
    # Only fetch structure and band structure
    data = scraper.fetch_multiple_materials(
        ["mp-149", "mp-2534"],
        fetch_structure=True,
        fetch_bandstructure=True,
        fetch_dos=False,
        fetch_phonon=False,
        fetch_charge_density=False
    )
```

## Contributing

When adding new data sources:
1. Extend `MaterialsProjectScraper` for new APIs
2. Add validation checks in `DataValidator`
3. Update `CIFProcessor` for new file formats
4. Add configuration options
5. Update documentation

## References

- Materials Project: https://materialsproject.org
- pymatgen Documentation: https://pymatgen.org
- MPRester API: https://docs.materialsproject.org/downloading-data/mpresponder
- CIF Format: https://www.iucr.org/resources/cif