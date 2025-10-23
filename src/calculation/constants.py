"""
Material Properties - Dynamic Loading System

This module provides access to material properties through the materials registry.

Author: Abdullah Hasan Dafa && Razasyattar M. N.
"""

from typing import Dict, Any, Literal
import sys
from pathlib import Path

# Add materials directory to path
materials_path = Path(__file__).parent.parent.parent / "materials"
if str(materials_path) not in sys.path:
    sys.path.insert(0, str(materials_path))

from materials import MaterialRegistry

DataSourceType = Literal["literature", "mp_api"]

# Initialize global registry
_registry = MaterialRegistry()

# ============================================================================
# ALLOY SYSTEM ACCESS
# ============================================================================

def get_alloy_system(alloy_name: str):
    """
    Get an alloy system object.

    Args:
        alloy_name: Name of the alloy system

    Returns:
        AlloySystem object
    """
    return _registry.get_alloy(alloy_name)

def get_bowing_parameters(alloy_name: str) -> Dict[str, float]:
    """
    Get bowing parameters for an alloy system.

    Args:
        alloy_name: Name of the alloy system

    Returns:
        Dictionary of bowing parameters
    """
    alloy = _registry.get_alloy(alloy_name)
    return alloy.bowing_parameters

def get_crossover_composition(alloy_name: str) -> float:
    """
    Get the direct-to-indirect crossover composition for an alloy.

    Args:
        alloy_name: Name of the alloy system

    Returns:
        Crossover composition value
    """
    alloy = _registry.get_alloy(alloy_name)
    return alloy.get_crossover_composition()

def get_band_gap_behavior(alloy_name: str) -> Dict[str, Any]:
    """
    Get band gap behavior information for an alloy.

    Args:
        alloy_name: Name of the alloy system

    Returns:
        Dictionary with direct/indirect ranges and crossover
    """
    alloy = _registry.get_alloy(alloy_name)
    return {
        "direct_range": tuple(alloy.band_gap_transition.get("direct_range", [0.0, 0.45])),
        "indirect_range": tuple(alloy.band_gap_transition.get("indirect_range", [0.45, 1.0])),
        "crossover_x": alloy.get_crossover_composition(),
    }

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_properties(material: str, source: DataSourceType = "literature") -> Dict[str, Any]:
    """
    Get material properties.

    Args:
        material: Material name
        source: Data source ('literature' or 'mp_api')

    Returns:
        Dictionary of material properties
    """
    props = _registry.get_all_properties(material, source).copy()

    # Add MP-specific fields for API compatibility
    if source == "mp_api":
        material_obj = _registry.get_material(material)
        props.update({
            "mp_id": material_obj.mp_id,
            "formula": material_obj.formula,
            "vbm": None,
            "cbm": None,
            "is_gap_direct": None,
            "formation_energy_per_atom": None,
            "energy_above_hull": None,
            "elastic_tensor": None,
            "dielectric_constant_electronic": None,
        })

    return props


def get_bowing_parameter(alloy_name: str, property_name: str) -> float:
    """
    Get bowing parameter for a property in an alloy system.

    Args:
        alloy_name: Name of the alloy system
        property_name: Name of the property

    Returns:
        Bowing parameter value (0.0 if not defined)
    """
    alloy = _registry.get_alloy(alloy_name)
    return alloy.get_bowing_parameter(property_name)


def determine_band_gap_type(alloy_name: str, x: float) -> str:
    """
    Determine if direct or indirect gap at composition x for an alloy.

    Args:
        alloy_name: Name of the alloy system
        x: Composition variable (0.0 to 1.0)

    Returns:
        'direct' or 'indirect'
    """
    alloy = _registry.get_alloy(alloy_name)
    return alloy.determine_band_gap_type(x)


def is_property_available(material: str, property_name: str, source: DataSourceType) -> bool:
    """
    Check if property exists for a material in source.

    Args:
        material: Material name
        property_name: Name of the property
        source: Data source to check

    Returns:
        True if property is available and not None
    """
    try:
        val = _registry.get_property(material, property_name, source)
        return val is not None
    except:
        return False


def get_all_available_properties(material: str, source: DataSourceType) -> list:
    """
    Get list of all available property names for a material.

    Args:
        material: Material name
        source: Data source to query

    Returns:
        List of property names that are available
    """
    props = _registry.get_all_properties(material, source)
    return [k for k, v in props.items() if v is not None]


# ============================================================================
# PROPERTY METADATA
# ============================================================================

PROPERTY_METADATA = {
    "lattice_constant": {"unit": "Å", "category": "physical"},
    "band_gap": {"unit": "eV", "category": "electronic"},
    "effective_mass_electron": {"unit": "m₀", "category": "electronic"},
    "dielectric_constant_static": {"unit": "dimensionless", "category": "optical"},
    "bulk_modulus": {"unit": "GPa", "category": "mechanical"},
    "thermal_conductivity": {"unit": "W/(cm·K)", "category": "thermal"},
    "electron_mobility": {"unit": "cm²/(V·s)", "category": "transport"},
}

# ============================================================================
# DATA SOURCE INFO
# ============================================================================

DATA_SOURCE_INFO = {
    "literature": {
        "name": "Experimental 300K Values",
        "sources": [
            "Adachi, Sadao - The Handbook on Optical Constants of Semiconductors (2012)",
            "Adachi, Sadao - Properties of Group-IV, III-V and II-VI Semiconductors (2005)"
        ],
        "temperature": 300,  # K
        "advantages": ["Accurate for devices", "Room temperature", "Experimental"],
        "limitations": ["Limited properties", "No formation energy"],
    },
    "mp_api": {
        "name": "Materials Project DFT",
        "sources": ["materialsproject.org"],
        "temperature": 0,  # K (DFT)
        "advantages": ["Complete dataset", "Thermodynamics", "Consistent"],
        "limitations": ["Band gap underestimated 30-50%", "0K only", "Needs corrections"],
    }
}

# ============================================================================
# MATERIAL SYSTEM ACCESS
# ============================================================================

def get_material_registry() -> MaterialRegistry:
    """
    Get the material registry for advanced usage.

    Returns:
        MaterialRegistry instance
    """
    return _registry


# ============================================================================
# MATERIAL AND ALLOY MANAGEMENT
# ============================================================================

def list_available_materials() -> list:
    """
    List all materials available in the system.

    Returns:
        List of material names
    """
    return _registry.list_materials()


def list_available_alloys() -> list:
    """
    List all alloy systems available in the system.

    Returns:
        List of alloy system names
    """
    return _registry.list_alloys()

