"""
Input Validation Utilities for s-CGCNN v0.1.1

Helper functions for validating inputs and configurations.

Author: Abdullah Hasan Dafa
"""

from typing import Any, Union, List, Dict, Optional
from pathlib import Path


# ============================================================================
# COMPOSITION VALIDATION
# ============================================================================

def validate_composition(x: float, allow_negative: bool = False) -> float:
    """
    Validate Al composition value.
    
    Args:
        x: Al composition (0.0 to 1.0)
        allow_negative: Allow negative values (for testing)
    
    Returns:
        Validated composition
    
    Raises:
        ValueError: If composition is out of range
    """
    if not isinstance(x, (int, float)):
        raise TypeError(f"Composition must be numeric, got {type(x)}")
    
    x = float(x)
    
    if not allow_negative and x < 0.0:
        raise ValueError(f"Composition must be >= 0.0, got {x}")
    
    if x > 1.0:
        raise ValueError(f"Composition must be <= 1.0, got {x}")
    
    return x


def validate_composition_range(
    x_min: float,
    x_max: float,
    x_step: float
) -> tuple:
    """
    Validate composition range parameters.
    
    Args:
        x_min: Minimum composition
        x_max: Maximum composition
        x_step: Step size
    
    Returns:
        Validated (x_min, x_max, x_step)
    
    Raises:
        ValueError: If range is invalid
    """
    x_min = validate_composition(x_min)
    x_max = validate_composition(x_max)
    
    if x_min > x_max:
        raise ValueError(f"x_min ({x_min}) must be <= x_max ({x_max})")
    
    if x_step <= 0:
        raise ValueError(f"x_step must be positive, got {x_step}")
    
    if x_step > (x_max - x_min):
        raise ValueError(
            f"x_step ({x_step}) is larger than range ({x_max - x_min})"
        )
    
    return x_min, x_max, x_step


# ============================================================================
# DATA SOURCE VALIDATION
# ============================================================================

def validate_data_source(source: str) -> str:
    """
    Validate data source selection.
    
    Args:
        source: Data source ("literature" or "mp_api")
    
    Returns:
        Validated source string
    
    Raises:
        ValueError: If source is invalid
    """
    valid_sources = ["literature", "mp_api"]
    
    source = source.lower().strip()
    
    if source not in valid_sources:
        raise ValueError(
            f"Invalid data source: {source}. "
            f"Must be one of: {', '.join(valid_sources)}"
        )
    
    return source


def validate_interpolation_mode(mode: str) -> str:
    """
    Validate interpolation mode (alias for validate_data_source).
    
    Args:
        mode: Interpolation mode
    
    Returns:
        Validated mode string
    """
    return validate_data_source(mode)


# ============================================================================
# PROPERTY VALIDATION
# ============================================================================

def validate_property_name(property_name: str, allow_custom: bool = True) -> str:
    """
    Validate property name.
    
    Args:
        property_name: Property name
        allow_custom: Allow custom property names
    
    Returns:
        Validated property name
    
    Raises:
        ValueError: If property name is invalid
    """
    if not isinstance(property_name, str):
        raise TypeError(f"Property name must be string, got {type(property_name)}")
    
    property_name = property_name.strip()
    
    if not property_name:
        raise ValueError("Property name cannot be empty")
    
    # Known properties (from constants.py)
    known_properties = {
        # Physical
        "lattice_constant", "density", "thermal_expansion", "volume",
        # Electronic
        "band_gap", "band_gap_type", "electron_affinity",
        "effective_mass_electron", "effective_mass_hole_heavy",
        "effective_mass_hole_light", "effective_mass_hole_split_off",
        "vbm", "cbm", "is_gap_direct", "is_metal", "fermi_energy",
        # Optical
        "dielectric_constant_static", "dielectric_constant_high_freq",
        "dielectric_constant_electronic", "dielectric_constant_ionic",
        "refractive_index",
        # Mechanical
        "elastic_constant_c11", "elastic_constant_c12", "elastic_constant_c44",
        "bulk_modulus", "shear_modulus", "youngs_modulus",
        "elastic_tensor", "elastic_anisotropy", "poissons_ratio",
        # Thermal
        "thermal_conductivity", "specific_heat", "debye_temperature",
        # Transport
        "electron_mobility", "hole_mobility",
        # Thermodynamic
        "formation_energy_per_atom", "energy_above_hull", "decomposition_enthalpy",
        # Magnetic
        "total_magnetization", "is_magnetic",
    }
    
    if not allow_custom and property_name not in known_properties:
        raise ValueError(
            f"Unknown property: {property_name}. "
            f"Set allow_custom=True to allow custom properties."
        )
    
    return property_name


def validate_property_value(
    value: Any,
    property_name: str,
    allow_none: bool = True
) -> Any:
    """
    Validate property value based on expected type.
    
    Args:
        value: Property value
        property_name: Property name (for context)
        allow_none: Allow None values
    
    Returns:
        Validated value
    
    Raises:
        ValueError: If value is invalid
    """
    if value is None:
        if allow_none:
            return None
        else:
            raise ValueError(f"Property '{property_name}' cannot be None")
    
    # Type-specific validation
    if property_name in ["band_gap_type", "is_gap_direct", "is_metal", "is_magnetic"]:
        # Boolean or string properties
        return value
    
    elif property_name in ["lattice_constant", "density", "band_gap"]:
        # Must be positive
        if not isinstance(value, (int, float)):
            raise TypeError(f"{property_name} must be numeric, got {type(value)}")
        if value < 0:
            raise ValueError(f"{property_name} must be positive, got {value}")
        return float(value)
    
    else:
        # Generic numeric validation
        if isinstance(value, (int, float)):
            return float(value)
        return value


# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================

def validate_supercell_size(size: Union[List, tuple]) -> tuple:
    """
    Validate supercell size.
    
    Args:
        size: Supercell size (e.g., [2, 2, 2])
    
    Returns:
        Validated tuple
    
    Raises:
        ValueError: If size is invalid
    """
    if not isinstance(size, (list, tuple)):
        raise TypeError(f"Supercell size must be list or tuple, got {type(size)}")
    
    if len(size) != 3:
        raise ValueError(f"Supercell size must have 3 dimensions, got {len(size)}")
    
    size = tuple(size)
    
    for i, dim in enumerate(size):
        if not isinstance(dim, int):
            raise TypeError(f"Supercell dimension {i} must be int, got {type(dim)}")
        if dim < 1:
            raise ValueError(f"Supercell dimension {i} must be >= 1, got {dim}")
    
    return size


def validate_log_level(level: str) -> str:
    """
    Validate log level.
    
    Args:
        level: Log level string
    
    Returns:
        Validated level (uppercase)
    
    Raises:
        ValueError: If level is invalid
    """
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    
    level = level.upper().strip()
    
    if level not in valid_levels:
        raise ValueError(
            f"Invalid log level: {level}. "
            f"Must be one of: {', '.join(valid_levels)}"
        )
    
    return level


def validate_config_dict(config: Dict, required_keys: List[str]):
    """
    Validate configuration dictionary has required keys.
    
    Args:
        config: Configuration dictionary
        required_keys: List of required key names
    
    Raises:
        KeyError: If required key is missing
        TypeError: If config is not a dict
    """
    if not isinstance(config, dict):
        raise TypeError(f"Config must be dictionary, got {type(config)}")
    
    missing_keys = []
    for key in required_keys:
        if key not in config:
            missing_keys.append(key)
    
    if missing_keys:
        raise KeyError(
            f"Config missing required keys: {', '.join(missing_keys)}"
        )


# ============================================================================
# FILE PATH VALIDATION
# ============================================================================

def validate_file_path(
    filepath: Union[str, Path],
    must_exist: bool = True,
    file_type: str = "File"
) -> Path:
    """
    Validate file path.
    
    Args:
        filepath: Path to file
        must_exist: File must exist
        file_type: Description of file type (for error messages)
    
    Returns:
        Path object
    
    Raises:
        FileNotFoundError: If must_exist=True and file doesn't exist
        TypeError: If filepath is invalid type
    """
    if not isinstance(filepath, (str, Path)):
        raise TypeError(f"Filepath must be string or Path, got {type(filepath)}")
    
    filepath = Path(filepath)
    
    if must_exist and not filepath.exists():
        raise FileNotFoundError(f"{file_type} not found: {filepath}")
    
    return filepath


def validate_dir_path(
    dirpath: Union[str, Path],
    must_exist: bool = True,
    create_if_missing: bool = False
) -> Path:
    """
    Validate directory path.
    
    Args:
        dirpath: Path to directory
        must_exist: Directory must exist
        create_if_missing: Create if doesn't exist
    
    Returns:
        Path object
    
    Raises:
        FileNotFoundError: If must_exist=True and dir doesn't exist
        NotADirectoryError: If path exists but is not a directory
    """
    if not isinstance(dirpath, (str, Path)):
        raise TypeError(f"Dirpath must be string or Path, got {type(dirpath)}")
    
    dirpath = Path(dirpath)
    
    if dirpath.exists() and not dirpath.is_dir():
        raise NotADirectoryError(f"Not a directory: {dirpath}")
    
    if not dirpath.exists():
        if must_exist and not create_if_missing:
            raise FileNotFoundError(f"Directory not found: {dirpath}")
        elif create_if_missing:
            dirpath.mkdir(parents=True, exist_ok=True)
    
    return dirpath


# ============================================================================
# NUMERIC VALIDATION
# ============================================================================

def validate_positive_number(
    value: Union[int, float],
    name: str = "Value",
    allow_zero: bool = False
) -> float:
    """
    Validate positive number.
    
    Args:
        value: Number to validate
        name: Name for error messages
        allow_zero: Allow zero value
    
    Returns:
        Validated number
    
    Raises:
        ValueError: If value is not positive
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric, got {type(value)}")
    
    value = float(value)
    
    if allow_zero:
        if value < 0:
            raise ValueError(f"{name} must be >= 0, got {value}")
    else:
        if value <= 0:
            raise ValueError(f"{name} must be > 0, got {value}")
    
    return value


def validate_range(
    value: Union[int, float],
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    name: str = "Value"
) -> float:
    """
    Validate number is within range.
    
    Args:
        value: Number to validate
        min_val: Minimum allowed value (None = no minimum)
        max_val: Maximum allowed value (None = no maximum)
        name: Name for error messages
    
    Returns:
        Validated number
    """
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric, got {type(value)}")
    
    value = float(value)
    
    if min_val is not None and value < min_val:
        raise ValueError(f"{name} must be >= {min_val}, got {value}")
    
    if max_val is not None and value > max_val:
        raise ValueError(f"{name} must be <= {max_val}, got {value}")
    
    return value


# ============================================================================
# BATCH VALIDATION
# ============================================================================

def validate_all(
    validators: Dict[str, tuple],
    raise_on_first_error: bool = True
) -> Dict[str, Any]:
    """
    Run multiple validators and collect results.
    
    Args:
        validators: Dict of {name: (validator_func, value, kwargs)}
        raise_on_first_error: Stop on first error
    
    Returns:
        Dict of validated values
    
    Raises:
        ValueError: If validation fails
    """
    results = {}
    errors = {}
    
    for name, (validator, value, kwargs) in validators.items():
        try:
            results[name] = validator(value, **kwargs)
        except Exception as e:
            errors[name] = str(e)
            if raise_on_first_error:
                raise ValueError(f"Validation failed for '{name}': {e}")
    
    if errors and not raise_on_first_error:
        error_msg = "\n".join([f"  {k}: {v}" for k, v in errors.items()])
        raise ValueError(f"Validation failed:\n{error_msg}")
    
    return results


# ============================================================================
# MODULE METADATA
# ============================================================================

__version__ = "0.1.1"
__author__ = "Abdullah Hasan Dafa"

__all__ = [
    # Composition
    "validate_composition",
    "validate_composition_range",
    # Data source
    "validate_data_source",
    "validate_interpolation_mode",
    # Property
    "validate_property_name",
    "validate_property_value",
    # Configuration
    "validate_supercell_size",
    "validate_log_level",
    "validate_config_dict",
    # File paths
    "validate_file_path",
    "validate_dir_path",
    # Numeric
    "validate_positive_number",
    "validate_range",
    # Batch
    "validate_all",
]