# Utils Module

The `src/utils/` module provides essential utility functions and classes for the S-CGCNN project, including configuration management, logging, caching, and API validation.

## Overview

This module contains core utilities that support the entire pipeline:
- **Configuration Management**: YAML-based config loading and validation
- **Logging System**: Centralized logging with file and console output
- **Cache Management**: Intelligent caching with time-based invalidation
- **API Validation**: Materials Project API key validation and connectivity testing

## Key Features

- **Singleton Pattern**: Global instances for config, logging, and caching
- **Thread-Safe Operations**: Safe concurrent access to shared resources
- **Automatic Validation**: Config validation and API key verification
- **Smart Caching**: Time-based cache invalidation and metadata tracking
- **Comprehensive Logging**: Multi-level logging with rotation and formatting

## Module Structure

### Core Files

| File | Purpose |
|------|---------|
| `__init__.py` | Module initialization and public API |
| `config_loader.py` | YAML configuration loading and validation |
| `logger.py` | Centralized logging configuration |
| `cache_manager.py` | File caching with metadata and invalidation |
| `api_validator.py` | Materials Project API validation |

### Key Classes

- **`ConfigLoader`**: Loads and validates YAML configuration files
- **`Logger`**: Singleton logging manager with file/console output
- **`CacheManager`**: Manages cached data with time-based expiration
- **`APIValidator`**: Validates Materials Project API credentials
- **`CacheEntry`**: Represents individual cached items with metadata

## Quick Start

### Configuration Management

```python
from src.utils import get_config

# Get global config instance
config = get_config()

# Access configuration values
data_dir = config.get('paths.data_dir', 'data/')
x_values = config.get('system.compositions.x_values', [0.0, 0.5, 1.0])

# Update configuration
config.update_config({'features.enable_relaxation': True})
```

### Logging Setup

```python
from src.utils import get_logger, setup_logging

# Get logger for current module
logger = get_logger(__name__)

# Log messages
logger.info("Starting pipeline execution")
logger.debug("Processing composition x=0.5")
logger.error("Failed to load structure file")

# Setup logging from config
setup_logging()
```

### Cache Management

```python
from src.utils import get_cache_manager

# Get global cache manager
cache = get_cache_manager()

# Check if data is cached
if cache.is_cached("material_mp-149", max_age_days=7):
    entry = cache.get_entry("material_mp-149")
    # Load cached data
    pass

# Add new cache entry
cache.add_entry(
    key="material_mp-149",
    file_path="data/mp-149/material_data.json",
    metadata={"source": "mp_api", "version": "1.0"}
)
```

### API Validation

```python
from src.utils import validate_mp_api

# Validate API key
is_valid, message = validate_mp_api()

if is_valid:
    print("API key is valid:", message)
else:
    print("API validation failed:", message)
```

## Configuration Management

### ConfigLoader Class

The `ConfigLoader` handles YAML configuration files with validation:

```python
from src.utils.config_loader import ConfigLoader

# Load specific config file
config = ConfigLoader("my_config.yaml")
config_dict = config.load_config()

# Access nested values
value = config.get("system.compositions.x_values")
default_value = config.get("missing.key", "default")
```

### Configuration Structure

```yaml
# config.yaml
paths:
  data_dir: "data/"
  cache_dir: "cache/"
  output_dir: "data/outputs/"

system:
  binary_compounds:
    - mp_id: "mp-2534"
      formula: "GaAs"
    - mp_id: "mp-2172"
      formula: "AlAs"
  compositions:
    x_values: [0.0, 0.25, 0.5, 0.75, 1.0]

features:
  enable_charge_density: true
  enable_relaxation: true
  enable_tight_binding: true

hyperparameters:
  learning_rate: 0.001
  batch_size: 32
  epochs: 100
```

### Validation Rules

- **Required Keys**: `paths`, `system`, `hyperparameters`
- **Binary Compounds**: Exactly 2 compounds required
- **Compositions**: `x_values` array must be present
- **Paths**: Auto-creation of missing directories

## Logging System

### Logger Class

Centralized logging with multiple handlers:

```python
from src.utils.logger import Logger

# Get singleton instance
logger_instance = Logger()
logger = logger_instance.get_logger("my_module")

# Set logging level
logger_instance.set_level("DEBUG")
```

### Log Output

- **Console**: INFO level and above, simple format
- **File**: DEBUG level and above, detailed format with timestamps
- **Rotation**: 10MB files with 5 backups
- **Location**: `logs/s-cgcnn.log`

### Log Format

```
# Console (INFO+)
2024-01-15 10:30:15 - INFO - Starting pipeline execution

# File (DEBUG+)
2024-01-15 10:30:15 - src.calculation.main - INFO - run_full_pipeline:42 - Starting AlGaAs pipeline
```

## Cache Management

### CacheManager Class

Intelligent caching with metadata tracking:

```python
from src.utils.cache_manager import CacheManager

# Initialize with custom settings
cache = CacheManager(
    cache_dir="my_cache/",
    metadata_file="my_cache_metadata.json"
)

# Generate cache keys
key = cache._generate_key("material_data", {"mp_id": "mp-149", "version": "1.0"})
```

### Cache Operations

```python
# Check cache validity
is_cached = cache.is_cached("material_mp-149", max_age_days=7)

# Get cache entry
entry = cache.get_entry("material_mp-149")
if entry:
    print(f"Cached at: {entry.timestamp}")
    print(f"File size: {entry.size_bytes} bytes")

# Add/update entry
cache.add_entry(
    key="material_mp-149",
    file_path="data/mp-149/material_data.json",
    metadata={"api_version": "mp-api"}
)

# Remove entry
cache.remove_entry("material_mp-149")

# Clear cache
cache.clear_cache()  # All entries
cache.clear_cache("material_*")  # Pattern matching

# Get statistics
stats = cache.get_cache_stats()
print(f"Total entries: {stats['total_entries']}")
print(f"Total size: {stats['total_size_mb']} MB")
```

### Cache Entry Structure

```python
@dataclass
class CacheEntry:
    key: str                    # Unique cache identifier
    timestamp: datetime        # Creation/modification time
    file_path: Optional[str]   # Path to cached file
    metadata: Optional[Dict]   # Additional metadata
    size_bytes: Optional[int]  # File size in bytes
```

### Cache Maintenance

```python
# List entries
entries = cache.list_entries("material_*")

# Cleanup old entries
cache.cleanup_old_entries(max_age_days=30)

# Get cache statistics
stats = cache.get_cache_stats()
```

## API Validation

### APIValidator Class

Validates Materials Project API credentials:

```python
from src.utils.api_validator import APIValidator

# Initialize validator
validator = APIValidator(api_key="your_key_here")

# Validate API key
is_valid, message = validator.validate_api_key()

# Test connectivity
is_connected, conn_message = validator.test_connectivity()
```

### API Key File Format

```
# key.env
mp_api = your_api_key_here
```

### Validation Process

1. **Key Loading**: Reads from `key.env` file
2. **Format Check**: Validates `mp_api = <key>` format
3. **API Test**: Makes test request to Materials Project
4. **Connectivity**: Verifies network connection

### Error Handling

```python
try:
    is_valid, message = validate_mp_api()
    if not is_valid:
        print(f"API validation failed: {message}")
        # Handle invalid API key
except FileNotFoundError:
    print("key.env file not found")
except Exception as e:
    print(f"Validation error: {e}")
```

## Global Instances

### Singleton Pattern

All utilities use singleton patterns for global access:

```python
# Always returns the same instance
config1 = get_config()
config2 = get_config()
assert config1 is config2  # True

logger1 = get_logger()
logger2 = get_logger()
assert logger1 is logger2  # True

cache1 = get_cache_manager()
cache2 = get_cache_manager()
assert cache1 is cache2  # True
```

### Thread Safety

Global instances are thread-safe for concurrent access:

```python
import threading

def worker():
    config = get_config()
    logger = get_logger()
    # Safe concurrent access

threads = [threading.Thread(target=worker) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

## Error Handling

### Configuration Errors

```python
from src.utils.config_loader import ConfigLoader

try:
    config = ConfigLoader("missing_config.yaml")
    config.load_config()
except FileNotFoundError:
    print("Configuration file not found")
except yaml.YAMLError as e:
    print(f"Invalid YAML: {e}")
```

### Cache Errors

```python
try:
    entry = cache.get_entry("missing_key")
    if entry is None:
        print("Cache entry not found")
except Exception as e:
    print(f"Cache error: {e}")
```

### API Errors

```python
try:
    is_valid, message = validate_mp_api()
except FileNotFoundError:
    print("API key file not found")
except ConnectionError:
    print("Network connection failed")
except Exception as e:
    print(f"API validation error: {e}")
```

## Performance Considerations

### Memory Usage
- **Lazy Loading**: Config and cache loaded on first access
- **File Rotation**: Log files automatically rotated to prevent growth
- **Cache Cleanup**: Automatic removal of expired entries

### I/O Optimization
- **Buffered Writing**: Efficient file operations
- **JSON Serialization**: Fast data storage/retrieval
- **Path Caching**: Path objects cached to avoid repeated resolution

### Threading
- **Singleton Safety**: Thread-safe singleton implementation
- **Lock-Free Reads**: Concurrent read access to shared state
- **Atomic Writes**: Safe concurrent modifications

## Dependencies

### Required
- `pyyaml`: YAML configuration parsing
- `mp-api`: Materials Project API client (for API validation)

### Optional
- None (all dependencies are optional based on usage)

## Examples

### Complete Setup

```python
from src.utils import (
    get_config, get_logger, get_cache_manager, validate_mp_api
)

# Validate API
is_valid, message = validate_mp_api()
if not is_valid:
    raise RuntimeError(f"API validation failed: {message}")

# Setup logging
logger = get_logger(__name__)
logger.info("Starting S-CGCNN pipeline")

# Load configuration
config = get_config()
data_dir = config.get('paths.data_dir')

# Initialize cache
cache = get_cache_manager()

logger.info("Utils initialization complete")
```

### Custom Configuration

```python
from src.utils.config_loader import ConfigLoader

# Load custom config
config = ConfigLoader("production_config.yaml")
config_dict = config.load_config()

# Override settings
config.update_config({
    'hyperparameters': {
        'learning_rate': 0.0001,
        'batch_size': 64
    }
})

# Save modified config
config.save_config("modified_config.yaml")
```

## Contributing

When adding new utilities:
1. Follow singleton pattern for global services
2. Add comprehensive error handling
3. Include type hints and docstrings
4. Update `__init__.py` exports
5. Add unit tests
6. Update documentation

## References

- PyYAML Documentation: https://pyyaml.org/
- Python Logging: https://docs.python.org/3/library/logging.html
- Materials Project API: https://docs.materialsproject.org/