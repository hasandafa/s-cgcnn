"""
AlGaAs Material Properties Constants - Version 0.1.1
Enhanced with dual data source: Literature vs MP-API

Author: Abdullah Hasan Dafa
Source: ioffe.ru/SVA/NSM/Semicond/AlGaAs/ (Literature)
        Materials Project API (MP-API)
"""

from typing import Dict, Any, Literal
from dataclasses import dataclass, field

# ============================================================================
# DATA SOURCE TYPES
# ============================================================================
DataSourceType = Literal["literature", "mp_api"]


# ============================================================================
# LITERATURE-BASED PROPERTIES (Experimental Values from ioffe.ru)
# ============================================================================
@dataclass
class LiteratureProperties:
    """Experimental properties from Ioffe Institute Database"""
    
    # Reference information
    source: str = "ioffe.ru/SVA/NSM/Semicond/AlGaAs/"
    reference: str = "Ioffe Institute NSM Archive"
    note: str = "Experimental values - recommended for device engineering"
    
    # Temperature for measurements
    temperature: float = 300.0  # K (room temperature)


# GaAs Properties (Literature - Experimental)
GAAS_PROPERTIES_LITERATURE = {
    # ========== Physical Properties ==========
    "lattice_constant": 5.6533,  # Å at 300K
    "density": 5.3176,  # g/cm³
    "thermal_expansion": 5.73e-6,  # 1/K at 300K
    
    # ========== Electronic Properties ==========
    "band_gap": 1.424,  # eV at 300K (DIRECT GAP - Experimental)
    "band_gap_type": "direct",  # Γ valley minimum
    "band_gap_temperature_coeff": -0.000454,  # eV/K (dEg/dT)
    "electron_affinity": 4.07,  # eV
    
    # Effective masses (in units of free electron mass m₀)
    "effective_mass_electron": 0.067,  # mₑ* (Γ valley)
    "effective_mass_hole_heavy": 0.45,  # mₕₕ*
    "effective_mass_hole_light": 0.082,  # mₗₕ*
    "effective_mass_hole_split_off": 0.154,  # mₛₒ*
    
    # ========== Optical Properties ==========
    "dielectric_constant_static": 12.9,  # εₛ (static)
    "dielectric_constant_high_freq": 10.9,  # ε∞ (high frequency/optical)
    "refractive_index": 3.3,  # n at 1.0 eV
    
    # ========== Mechanical Properties (Elastic Constants) ==========
    "elastic_constant_c11": 1188.0,  # GPa
    "elastic_constant_c12": 538.0,   # GPa
    "elastic_constant_c44": 594.0,   # GPa
    "bulk_modulus": 75.5,  # GPa (K = (C₁₁ + 2C₁₂)/3)
    "shear_modulus": 33.0,  # GPa (approximate)
    "youngs_modulus": 85.5,  # GPa
    
    # ========== Thermal Properties ==========
    "thermal_conductivity": 0.46,  # W/(cm·K) at 300K
    "specific_heat": 0.35,  # J/(g·K) at 300K
    "debye_temperature": 344.0,  # K
    
    # ========== Transport Properties ==========
    "electron_mobility": 8500.0,  # cm²/(V·s) at 300K (undoped)
    "hole_mobility": 400.0,  # cm²/(V·s) at 300K (undoped)
}


# AlAs Properties (Literature - Experimental)
ALAS_PROPERTIES_LITERATURE = {
    # ========== Physical Properties ==========
    "lattice_constant": 5.6611,  # Å at 300K
    "density": 3.760,  # g/cm³
    "thermal_expansion": 5.2e-6,  # 1/K at 300K
    
    # ========== Electronic Properties ==========
    "band_gap": 2.168,  # eV at 300K (INDIRECT GAP - Experimental)
    "band_gap_type": "indirect",  # X valley minimum
    "band_gap_temperature_coeff": -0.000396,  # eV/K (dEg/dT)
    "electron_affinity": 3.5,  # eV
    
    # Effective masses (in units of free electron mass m₀)
    "effective_mass_electron": 0.15,  # mₑ* (X valley for indirect gap)
    "effective_mass_hole_heavy": 0.51,  # mₕₕ*
    "effective_mass_hole_light": 0.18,  # mₗₕ*
    "effective_mass_hole_split_off": 0.25,  # mₛₒ*
    
    # ========== Optical Properties ==========
    "dielectric_constant_static": 10.06,  # εₛ (static)
    "dielectric_constant_high_freq": 8.16,  # ε∞ (high frequency/optical)
    "refractive_index": 2.95,  # n at 2.0 eV
    
    # ========== Mechanical Properties (Elastic Constants) ==========
    "elastic_constant_c11": 1250.0,  # GPa
    "elastic_constant_c12": 534.0,   # GPa
    "elastic_constant_c44": 542.0,   # GPa
    "bulk_modulus": 77.6,  # GPa (K = (C₁₁ + 2C₁₂)/3)
    "shear_modulus": 30.0,  # GPa (approximate)
    "youngs_modulus": 79.0,  # GPa
    
    # ========== Thermal Properties ==========
    "thermal_conductivity": 0.91,  # W/(cm·K) at 300K
    "specific_heat": 0.48,  # J/(g·K) at 300K
    "debye_temperature": 417.0,  # K
    
    # ========== Transport Properties ==========
    "electron_mobility": 280.0,  # cm²/(V·s) at 300K (undoped)
    "hole_mobility": 180.0,  # cm²/(V·s) at 300K (undoped)
}


# ============================================================================
# MP-API BASED PROPERTIES (DFT-Calculated from Materials Project)
# ============================================================================
# Note: These are PLACEHOLDERS - actual values fetched dynamically from MP API
# DFT-GGA values typically underestimate band gaps by 30-50%

GAAS_PROPERTIES_MP_API = {
    # ========== Physical Properties ==========
    "lattice_constant": None,  # Fetched from MP structure
    "density": None,  # Calculated from MP structure
    "volume": None,  # From MP
    
    # ========== Electronic Properties (DFT) ==========
    "band_gap": None,  # DFT value (typically ~0.19 eV, underestimated!)
    "band_gap_type": "direct",  # DFT structure
    "vbm": None,  # Valence Band Maximum (eV)
    "cbm": None,  # Conduction Band Minimum (eV)
    "is_gap_direct": None,  # Boolean
    "is_metal": False,
    
    # ========== Thermodynamic Properties ==========
    "formation_energy_per_atom": None,  # eV/atom
    "energy_above_hull": None,  # eV/atom (stability metric)
    "decomposition_enthalpy": None,  # eV/atom
    
    # ========== Mechanical Properties ==========
    "bulk_modulus": None,  # GPa (from elastic tensor)
    "shear_modulus": None,  # GPa (from elastic tensor)
    "elastic_tensor": None,  # Full 6x6 tensor
    "elastic_anisotropy": None,
    "poissons_ratio": None,
    
    # ========== Optical/Dielectric Properties ==========
    "dielectric_constant_static": None,  # Total dielectric tensor
    "dielectric_constant_electronic": None,  # Electronic contribution
    "dielectric_constant_ionic": None,  # Ionic contribution
    "refractive_index": None,  # Calculated from ε∞
    
    # ========== Magnetic Properties ==========
    "total_magnetization": None,  # μB/unit cell
    "is_magnetic": False,
    
    # ========== MP Metadata ==========
    "mp_id": "mp-2534",
    "formula": "GaAs",
    "space_group": None,
    "crystal_system": "cubic",
    "point_group": None,
}


ALAS_PROPERTIES_MP_API = {
    # ========== Physical Properties ==========
    "lattice_constant": None,  # Fetched from MP structure
    "density": None,  # Calculated from MP structure
    "volume": None,  # From MP
    
    # ========== Electronic Properties (DFT) ==========
    "band_gap": None,  # DFT value (typically ~1.50 eV, underestimated!)
    "band_gap_type": "indirect",  # DFT structure
    "vbm": None,  # Valence Band Maximum (eV)
    "cbm": None,  # Conduction Band Minimum (eV)
    "is_gap_direct": None,  # Boolean
    "is_metal": False,
    
    # ========== Thermodynamic Properties ==========
    "formation_energy_per_atom": None,  # eV/atom
    "energy_above_hull": None,  # eV/atom (stability metric)
    "decomposition_enthalpy": None,  # eV/atom
    
    # ========== Mechanical Properties ==========
    "bulk_modulus": None,  # GPa (from elastic tensor)
    "shear_modulus": None,  # GPa (from elastic tensor)
    "elastic_tensor": None,  # Full 6x6 tensor
    "elastic_anisotropy": None,
    "poissons_ratio": None,
    
    # ========== Optical/Dielectric Properties ==========
    "dielectric_constant_static": None,  # Total dielectric tensor
    "dielectric_constant_electronic": None,  # Electronic contribution
    "dielectric_constant_ionic": None,  # Ionic contribution
    "refractive_index": None,  # Calculated from ε∞
    
    # ========== Magnetic Properties ==========
    "total_magnetization": None,  # μB/unit cell
    "is_magnetic": False,
    
    # ========== MP Metadata ==========
    "mp_id": "mp-2172",
    "formula": "AlAs",
    "space_group": None,
    "crystal_system": "cubic",
    "point_group": None,
}


# ============================================================================
# BOWING PARAMETERS (Used for both Literature and MP-API modes)
# ============================================================================
# Vegard's Law deviation: P(x) = xP(AlAs) + (1-x)P(GaAs) - bx(1-x)

BOWING_PARAMETERS = {
    # Electronic properties
    "band_gap": 0.37,  # eV (most important for direct-indirect transition)
    "electron_affinity": 0.0,  # Approximately linear
    
    # Optical properties  
    "dielectric_constant_static": 0.0,  # Approximately linear
    "dielectric_constant_high_freq": 0.0,  # Approximately linear
    "refractive_index": 0.0,  # Small bowing
    
    # Mechanical properties
    "elastic_constant_c11": 0.0,  # Small bowing
    "elastic_constant_c12": 0.0,  # Small bowing
    "elastic_constant_c44": 0.0,  # Small bowing
    "bulk_modulus": 0.0,  # Approximately linear
    
    # Transport properties
    "electron_mobility": 0.0,  # Complex behavior, use linear approximation
    "hole_mobility": 0.0,  # Complex behavior, use linear approximation
    
    # All other properties assumed linear (bowing = 0.0)
}


# ============================================================================
# DIRECT-TO-INDIRECT TRANSITION (Critical for AlGaAs!)
# ============================================================================
CROSSOVER_COMPOSITION = 0.45  # x value where transition occurs

BAND_GAP_BEHAVIOR = {
    "direct_range": (0.0, 0.45),  # x < 0.45: Direct gap (Γ valley)
    "indirect_range": (0.45, 1.0),  # x ≥ 0.45: Indirect gap (X valley)
    "crossover_x": CROSSOVER_COMPOSITION,
    "note": "Direct-indirect crossover is composition-dependent"
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_properties(
    material: Literal["GaAs", "AlAs"],
    source: DataSourceType = "literature"
) -> Dict[str, Any]:
    """
    Get material properties from specified data source.
    
    Args:
        material: "GaAs" or "AlAs"
        source: "literature" (experimental) or "mp_api" (DFT)
    
    Returns:
        Dictionary of material properties
    """
    if source == "literature":
        if material == "GaAs":
            return GAAS_PROPERTIES_LITERATURE.copy()
        elif material == "AlAs":
            return ALAS_PROPERTIES_LITERATURE.copy()
        else:
            raise ValueError(f"Unknown material: {material}")
    
    elif source == "mp_api":
        if material == "GaAs":
            return GAAS_PROPERTIES_MP_API.copy()
        elif material == "AlAs":
            return ALAS_PROPERTIES_MP_API.copy()
        else:
            raise ValueError(f"Unknown material: {material}")
    
    else:
        raise ValueError(f"Unknown data source: {source}. Use 'literature' or 'mp_api'")


def is_property_available(
    property_name: str,
    source: DataSourceType
) -> bool:
    """
    Check if a property is available in the specified data source.
    
    Args:
        property_name: Name of the property
        source: Data source type
    
    Returns:
        True if property is available (not None)
    """
    if source == "literature":
        gaas = GAAS_PROPERTIES_LITERATURE
        alas = ALAS_PROPERTIES_LITERATURE
    else:  # mp_api
        gaas = GAAS_PROPERTIES_MP_API
        alas = ALAS_PROPERTIES_MP_API
    
    return (
        property_name in gaas and gaas[property_name] is not None and
        property_name in alas and alas[property_name] is not None
    )


def get_bowing_parameter(property_name: str) -> float:
    """
    Get bowing parameter for Vegard's Law.
    
    Args:
        property_name: Name of the property
    
    Returns:
        Bowing parameter (0.0 if not specified = linear interpolation)
    """
    return BOWING_PARAMETERS.get(property_name, 0.0)


def determine_band_gap_type(x: float) -> str:
    """
    Determine if band gap is direct or indirect based on composition.
    
    Args:
        x: Al composition (0.0 to 1.0)
    
    Returns:
        "direct" or "indirect"
    """
    return "direct" if x < CROSSOVER_COMPOSITION else "indirect"


# ============================================================================
# DATA SOURCE COMPARISON UTILITIES
# ============================================================================

def get_literature_vs_mp_comparison(material: Literal["GaAs", "AlAs"]) -> Dict:
    """
    Compare literature vs MP-API values for a material.
    
    Returns dictionary with comparison data for available properties.
    """
    lit = get_properties(material, "literature")
    mp = get_properties(material, "mp_api")
    
    comparison = {}
    
    # Only compare properties available in both sources
    common_keys = set(lit.keys()) & set(mp.keys())
    
    for key in common_keys:
        if lit[key] is not None and mp[key] is not None:
            comparison[key] = {
                "literature": lit[key],
                "mp_api": mp[key],
                "difference": None if isinstance(lit[key], str) else (mp[key] - lit[key]),
                "relative_diff_percent": None if isinstance(lit[key], str) else 
                    (100 * (mp[key] - lit[key]) / lit[key] if lit[key] != 0 else None)
            }
    
    return comparison


# ============================================================================
# EXPORT DATA SOURCE CONFIGURATION
# ============================================================================

DATA_SOURCE_INFO = {
    "literature": {
        "name": "Experimental Literature Values",
        "source": "ioffe.ru/SVA/NSM/Semicond/AlGaAs/",
        "description": "Room temperature experimental measurements",
        "recommended_for": ["device_engineering", "HEMT", "laser", "solar_cell"],
        "advantages": [
            "Accurate for real devices",
            "Experimentally verified",
            "Room temperature values"
        ],
        "limitations": [
            "Limited temperature range",
            "May not include all properties",
            "No formation energy data"
        ]
    },
    "mp_api": {
        "name": "Materials Project DFT Calculations",
        "source": "materialsproject.org",
        "description": "DFT-GGA calculated properties at 0K",
        "recommended_for": ["DFT_validation", "research", "comparative_studies"],
        "advantages": [
            "Complete property set",
            "Thermodynamic stability data",
            "Consistent computational method"
        ],
        "limitations": [
            "Band gaps underestimated (30-50%)",
            "0K calculations (not room temp)",
            "DFT approximations",
            "Requires scissor shift correction"
        ]
    }
}


# ============================================================================
# MODULE METADATA
# ============================================================================

__version__ = "0.1.1"
__author__ = "Abdullah Hasan Dafa"
__description__ = "AlGaAs material properties with dual data source support"