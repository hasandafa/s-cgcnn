"""
Electronic Structure Calculator - Material-Agnostic Version

This module provides tight-binding calculations for any material or alloy
system defined in the materials registry.

Author: Abdullah Hasan Dafa && Razasyattar M. N.
"""

import sys
from pathlib import Path
from typing import Dict

# Add materials directory to path
materials_path = Path(__file__).parent.parent.parent / "materials"
if str(materials_path) not in sys.path:
    sys.path.insert(0, str(materials_path))

from materials.tight_binding import *
from pymatgen.electronic_structure.bandstructure import BandStructureSymmLine
from pymatgen.electronic_structure.dos import CompleteDos
from materials import MaterialRegistry

__all__ = [
    'BandStructureData',
    'DOSData',
    'EffectiveMasses',
    'BandStructureSymmLine',
    'CompleteDos',
    'calculate_electronic_structure',
    'calculate_material_electronic_structure',
    'export_band_structure_to_json'
]




# Direct access to tight-binding classes - no unnecessary wrappers
GenericTightBinding = GenericTightBinding
AlloyTightBinding = AlloyTightBinding


# ============================================================================
# HIGH-LEVEL API
# ============================================================================

def calculate_electronic_structure(
    alloy_name: str,
    x: float,
    calculate_bs: bool = True,
    calculate_dos: bool = True,
    calculate_masses: bool = True,
    dos_method: str = "gaussian_kde",
    dos_sigma: float = 0.1,
    masses_method: str = "literature"
) -> Dict:
    """
    Calculate electronic structure for an alloy composition with enhanced options.

    Args:
        alloy_name: Name of alloy system
        x: Composition variable
        calculate_bs: Calculate band structure
        calculate_dos: Calculate DOS
        calculate_masses: Calculate effective masses
        dos_method: DOS calculation method ("gaussian_kde", "gaussian_broadening", "histogram")
        dos_sigma: Broadening parameter for DOS calculation
        masses_method: Effective mass method ("literature" or "parabolic_fit")

    Returns:
        Dictionary with results
    """
    tb = AlloyTightBinding(alloy_name, x)
    results = {
        'alloy_system': alloy_name,
        'composition': x
    }

    if calculate_bs:
        bs = tb.calculate_band_structure()
        results['band_structure'] = bs
        results['band_gap'] = bs.band_gap
        results['is_direct'] = bs.is_direct

    if calculate_dos:
        dos = tb.calculate_dos(method=dos_method, sigma=dos_sigma)
        results['dos'] = dos

    if calculate_masses:
        masses = tb.calculate_effective_masses(method=masses_method)
        results['effective_masses'] = masses

    return results


def calculate_material_electronic_structure(
    material_name: str,
    calculate_bs: bool = True,
    calculate_dos: bool = True,
    calculate_masses: bool = True,
    dos_method: str = "gaussian_kde",
    dos_sigma: float = 0.1,
    masses_method: str = "literature"
) -> Dict:
    """
    Calculate electronic structure for a binary material with enhanced options.

    Args:
        material_name: Name of the material (e.g., 'GaAs', 'AlAs')
        calculate_bs: Calculate band structure
        calculate_dos: Calculate DOS
        calculate_masses: Calculate effective masses
        dos_method: DOS calculation method ("gaussian_kde", "gaussian_broadening", "histogram")
        dos_sigma: Broadening parameter for DOS calculation
        masses_method: Effective mass method ("literature" or "parabolic_fit")

    Returns:
        Dictionary with results
    """
    tb = GenericTightBinding(material_name)
    results = {'material': material_name}

    if calculate_bs:
        bs = tb.calculate_band_structure()
        results['band_structure'] = bs
        results['band_gap'] = bs.band_gap
        results['is_direct'] = bs.is_direct

    if calculate_dos:
        dos = tb.calculate_dos(method=dos_method, sigma=dos_sigma)
        results['dos'] = dos

    if calculate_masses:
        masses = tb.calculate_effective_masses(method=masses_method)
        results['effective_masses'] = masses

    return results


def export_band_structure_to_json(bs_data: BandStructureData, filepath: str):
    """
    Export band structure to JSON for plotting.
    
    Args:
        bs_data: BandStructureData object
        filepath: Path to save JSON file
    """
    import json
    
    data = {
        'kpoints': bs_data.kpoints.tolist(),
        'energies': bs_data.energies.tolist(),
        'labels': bs_data.kpath_labels,
        'label_positions': bs_data.kpath_positions,
        'fermi_energy': bs_data.fermi_energy,
        'band_gap': bs_data.band_gap,
        'is_direct': bs_data.is_direct,
        'vbm': bs_data.vbm,
        'cbm': bs_data.cbm,
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example 1: Generic alloy calculation with enhanced DOS
    print("Example 1: AlGaAs at x=0.5 with advanced DOS")
    results = calculate_electronic_structure(
        "AlGaAs", 0.5,
        dos_method="gaussian_kde",
        masses_method="parabolic_fit"
    )
    print(f"  Band gap: {results['band_gap']:.3f} eV")
    print(f"  Direct: {results['is_direct']}")
    print(f"  Electron mass: {results['effective_masses'].electron:.3f} m₀")

    # Example 2: Binary material calculation with pymatgen integration
    print("\nExample 2: Pure GaAs with pymatgen objects")
    results_gaas = calculate_material_electronic_structure(
        "GaAs",
        dos_method="gaussian_broadening",
        dos_sigma=0.05
    )
    print(f"  Band gap: {results_gaas['band_gap']:.3f} eV")
    print(f"  Direct: {results_gaas['is_direct']}")

    # Example 3: Direct class usage with new methods
    print("\nExample 3: Direct class usage")
    tb_material = GenericTightBinding("GaAs")
    bs_pmg = tb_material.get_pymatgen_band_structure()
    dos_pmg = tb_material.get_pymatgen_dos(method="histogram")

    print(f"  pymatgen BS type: {type(bs_pmg).__name__}")
    print(f"  pymatgen DOS type: {type(dos_pmg).__name__}")

    print("\nAll calculations completed successfully!")