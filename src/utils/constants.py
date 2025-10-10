"""
Physical Constants and Reference Data for AlGaAs System
Reference: ioffe.ru/SVA/NSM/Semicond/AlGaAs/
"""

import numpy as np

# ==========================================
# FUNDAMENTAL CONSTANTS
# ==========================================
ELEMENTARY_CHARGE = 1.602176634e-19  # C
PLANCK_CONSTANT = 6.62607015e-34  # J·s
BOLTZMANN_CONSTANT = 1.380649e-23  # J/K
ELECTRON_MASS = 9.1093837015e-31  # kg
SPEED_OF_LIGHT = 299792458  # m/s

# ==========================================
# ALGAAS REFERENCE DATA (at 300K)
# Source: ioffe.ru
# ==========================================

# GaAs Properties (x = 0.0)
GaAs_PROPERTIES = {
    # Structural
    "lattice_constant": 5.65325,  # Å at 300K
    "density": 5.3176,  # g/cm³
    
    # Electronic
    "band_gap_direct": 1.424,  # eV (Γ valley)
    "band_gap_indirect_X": 1.900,  # eV (X valley)
    "band_gap_indirect_L": 1.708,  # eV (L valley)
    "band_gap_type": "direct",
    "electron_affinity": 4.07,  # eV
    "work_function": 4.8,  # eV
    
    # Effective masses (in units of m₀)
    "electron_effective_mass_gamma": 0.067,
    "electron_effective_mass_L": 0.55,
    "electron_effective_mass_X": 0.85,
    "hole_effective_mass_heavy": 0.50,
    "hole_effective_mass_light": 0.082,
    "hole_effective_mass_split_off": 0.154,
    
    # Dielectric constants
    "static_dielectric_constant": 12.9,
    "optical_dielectric_constant": 10.89,
    "refractive_index": 3.3,  # at 1 eV
    
    # Elastic constants (GPa)
    "elastic_c11": 118.8,
    "elastic_c12": 53.8,
    "elastic_c44": 59.4,
    "bulk_modulus": 75.5,
    "shear_modulus": 33.5,
    
    # Thermal properties
    "thermal_conductivity": 46.0,  # W/m·K at 300K
    "thermal_expansion": 6.86e-6,  # 1/K at 300K
    "specific_heat": 330,  # J/kg·K
    "debye_temperature": 344,  # K
    
    # Transport (at 300K)
    "electron_mobility": 8500,  # cm²/V·s
    "hole_mobility": 400,  # cm²/V·s
}

# AlAs Properties (x = 1.0)
AlAs_PROPERTIES = {
    # Structural
    "lattice_constant": 5.6611,  # Å at 300K
    "density": 3.760,  # g/cm³
    
    # Electronic
    "band_gap_direct": 3.099,  # eV (Γ valley)
    "band_gap_indirect_X": 2.168,  # eV (X valley) - FUNDAMENTAL
    "band_gap_indirect_L": 2.46,  # eV (L valley)
    "band_gap_type": "indirect",
    "electron_affinity": 3.5,  # eV
    "work_function": 4.5,  # eV (estimated)
    
    # Effective masses (in units of m₀)
    "electron_effective_mass_gamma": 0.15,
    "electron_effective_mass_L": 0.68,
    "electron_effective_mass_X": 1.1,
    "hole_effective_mass_heavy": 0.76,
    "hole_effective_mass_light": 0.15,
    "hole_effective_mass_split_off": 0.28,
    
    # Dielectric constants
    "static_dielectric_constant": 10.06,
    "optical_dielectric_constant": 8.16,
    "refractive_index": 2.95,  # at 2 eV
    
    # Elastic constants (GPa)
    "elastic_c11": 125.0,
    "elastic_c12": 53.4,
    "elastic_c44": 54.2,
    "bulk_modulus": 77.3,
    "shear_modulus": 36.6,
    
    # Thermal properties
    "thermal_conductivity": 91.0,  # W/m·K at 300K
    "thermal_expansion": 5.2e-6,  # 1/K at 300K
    "specific_heat": 440,  # J/kg·K (estimated)
    "debye_temperature": 417,  # K
    
    # Transport (at 300K)
    "electron_mobility": 280,  # cm²/V·s (X valley)
    "hole_mobility": 200,  # cm²/V·s
}

# ==========================================
# BOWING PARAMETERS
# For property P: P(x) = (1-x)*P_GaAs + x*P_AlAs - b*x*(1-x)
# ==========================================
BOWING_PARAMETERS = {
    "lattice_constant": -0.0078,  # Å
    "band_gap_gamma": -0.127,  # eV (direct)
    "band_gap_X": 0.055,  # eV (indirect X)
    "band_gap_L": 0.055,  # eV (indirect L)
    "electron_affinity": 0.0,  # eV (assumed linear)
    "static_dielectric": 0.0,  # assumed linear
    "optical_dielectric": 0.0,  # assumed linear
    "refractive_index": -0.0,  # assumed linear
    "thermal_conductivity": -15.0,  # W/m·K (estimated)
    "thermal_expansion": 0.0,  # assumed linear
    "elastic_c11": 0.0,  # GPa (assumed linear)
    "elastic_c12": 0.0,
    "elastic_c44": 0.0,
}

# Direct-to-indirect crossover
CROSSOVER_X = 0.45  # Al fraction where band gap changes from direct to indirect

# ==========================================
# BRILLOUIN ZONE K-PATH (for FCC zinc-blende)
# Standard path: Γ-X-U|K-Γ-L-W-X
# ==========================================
KPATH_FCC = {
    "path": ["GAMMA", "X", "U", "K", "GAMMA", "L", "W", "X"],
    "special_points": {
        "GAMMA": [0.0, 0.0, 0.0],
        "X": [0.5, 0.0, 0.5],
        "L": [0.5, 0.5, 0.5],
        "W": [0.5, 0.25, 0.75],
        "K": [0.375, 0.375, 0.75],
        "U": [0.625, 0.25, 0.625],
    },
    "npoints": 100,  # Points between each high-symmetry point
}

# ==========================================
# ATOMIC DATA
# ==========================================
ATOMIC_NUMBERS = {
    "Ga": 31,
    "Al": 13,
    "As": 33,
}

ATOMIC_MASSES = {  # g/mol
    "Ga": 69.723,
    "Al": 26.982,
    "As": 74.922,
}

COVALENT_RADII = {  # Å
    "Ga": 1.22,
    "Al": 1.21,
    "As": 1.21,
}

# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def calculate_property_vegard(P_GaAs: float, P_AlAs: float, x: float, 
                               bowing: float = 0.0) -> float:
    """
    Calculate property using Vegard's Law with bowing parameter.
    
    P(x) = (1-x)*P_GaAs + x*P_AlAs - b*x*(1-x)
    
    Args:
        P_GaAs: Property value for GaAs (x=0)
        P_AlAs: Property value for AlAs (x=1)
        x: Al fraction (0 to 1)
        bowing: Bowing parameter
    
    Returns:
        Interpolated property value
    """
    return (1 - x) * P_GaAs + x * P_AlAs - bowing * x * (1 - x)


def get_band_gap_algaas(x: float) -> dict:
    """
    Calculate band gap for AlGaAs at composition x.
    Accounts for direct-to-indirect crossover.
    
    Args:
        x: Al fraction (0 to 1)
    
    Returns:
        dict with 'value', 'type', and 'valley' keys
    """
    # Direct gap (Γ valley)
    Eg_direct = calculate_property_vegard(
        GaAs_PROPERTIES["band_gap_direct"],
        AlAs_PROPERTIES["band_gap_direct"],
        x,
        BOWING_PARAMETERS["band_gap_gamma"]
    )
    
    # Indirect gap (X valley)
    Eg_indirect_X = calculate_property_vegard(
        GaAs_PROPERTIES["band_gap_indirect_X"],
        AlAs_PROPERTIES["band_gap_indirect_X"],
        x,
        BOWING_PARAMETERS["band_gap_X"]
    )
    
    # Determine fundamental gap
    if x < CROSSOVER_X:
        return {
            "value": Eg_direct,
            "type": "direct",
            "valley": "Gamma",
            "Eg_direct": Eg_direct,
            "Eg_indirect_X": Eg_indirect_X
        }
    else:
        return {
            "value": Eg_indirect_X,
            "type": "indirect",
            "valley": "X",
            "Eg_direct": Eg_direct,
            "Eg_indirect_X": Eg_indirect_X
        }


def get_lattice_constant(x: float) -> float:
    """Calculate lattice constant for AlₓGa₁₋ₓAs."""
    return calculate_property_vegard(
        GaAs_PROPERTIES["lattice_constant"],
        AlAs_PROPERTIES["lattice_constant"],
        x,
        BOWING_PARAMETERS["lattice_constant"]
    )


def get_density(x: float) -> float:
    """Calculate density for AlₓGa₁₋ₓAs (linear interpolation)."""
    return calculate_property_vegard(
        GaAs_PROPERTIES["density"],
        AlAs_PROPERTIES["density"],
        x,
        0.0  # No bowing for density
    )


# ==========================================
# COMPOSITION GENERATOR
# ==========================================

def generate_compositions(x_start: float = 0.0, x_end: float = 1.0, 
                         x_step: float = 0.025) -> np.ndarray:
    """
    Generate array of Al fractions.
    
    Args:
        x_start: Starting Al fraction
        x_end: Ending Al fraction
        x_step: Step size
    
    Returns:
        Array of x values
    """
    return np.arange(x_start, x_end + x_step/2, x_step)


# Generate default composition array
X_VALUES = generate_compositions(0.0, 1.0, 0.025)
N_COMPOSITIONS = len(X_VALUES)

print(f"AlGaAs Constants Module Loaded")
print(f"Total compositions: {N_COMPOSITIONS}")
print(f"X range: {X_VALUES[0]:.3f} to {X_VALUES[-1]:.3f}")