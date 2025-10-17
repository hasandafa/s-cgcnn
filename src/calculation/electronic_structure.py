"""
Electronic Structure Calculator - Material-Agnostic Version

This module provides tight-binding calculations for any material or alloy
system defined in the materials registry.

Author: Abdullah Hasan Dafa && Razasyattar M. N.
"""

import sys
from pathlib import Path
from typing import Dict, Tuple, Optional

# Add materials directory to path
materials_path = Path(__file__).parent.parent.parent / "materials"
if str(materials_path) not in sys.path:
    sys.path.insert(0, str(materials_path))

from materials.tight_binding import (
    GenericTightBinding,
    AlloyTightBinding,
    BandStructureData,
    DOSData,
    EffectiveMasses
)
from materials import MaterialRegistry

__all__ = [
    'BandStructureData',
    'DOSData',
    'EffectiveMasses',
    'TightBindingMaterial',
    'TightBindingAlloy',
    'calculate_electronic_structure',
    'calculate_material_electronic_structure',
    'export_band_structure_to_json'
]




# ============================================================================
# NEW MATERIAL-AGNOSTIC CLASSES
# ============================================================================

class TightBindingMaterial:
    """
    Tight-binding calculator for any binary material.
    
    Works with any material that has tight-binding parameters defined
    in the materials registry.
    """
    
    def __init__(self, material_name: str, registry: Optional[MaterialRegistry] = None):
        """
        Initialize tight-binding calculator for a material.
        
        Args:
            material_name: Name of the material (e.g., 'GaAs', 'AlAs')
            registry: MaterialRegistry instance (uses global if None)
        """
        self.material_name = material_name
        self._tb = GenericTightBinding(material_name, registry)
    
    def calculate_band_structure(self) -> BandStructureData:
        """Calculate band structure"""
        return self._tb.calculate_band_structure()
    
    def calculate_dos(self, energy_range: Tuple[float, float] = (-10, 5),
                      n_energy: int = 500, n_kpoints: int = 20) -> DOSData:
        """Calculate density of states"""
        return self._tb.calculate_dos(energy_range, n_energy, n_kpoints)
    
    def calculate_effective_masses(self) -> EffectiveMasses:
        """Calculate effective masses"""
        return self._tb.calculate_effective_masses()


class TightBindingAlloy:
    """
    Tight-binding calculator for any alloy system.
    
    Works with any alloy that has bowing parameters and endpoint materials
    defined in the materials registry.
    """
    
    def __init__(self, alloy_name: str, x: float, 
                 registry: Optional[MaterialRegistry] = None):
        """
        Initialize tight-binding calculator for an alloy.
        
        Args:
            alloy_name: Name of the alloy system (e.g., 'AlGaAs')
            x: Composition variable
            registry: MaterialRegistry instance (uses global if None)
        """
        self.alloy_name = alloy_name
        self.x = x
        self._tb = AlloyTightBinding(alloy_name, x, registry)
    
    def calculate_band_structure(self) -> BandStructureData:
        """Calculate band structure"""
        return self._tb.calculate_band_structure()
    
    def calculate_dos(self, energy_range: Tuple[float, float] = (-10, 5),
                      n_energy: int = 500, n_kpoints: int = 20) -> DOSData:
        """Calculate density of states"""
        return self._tb.calculate_dos(energy_range, n_energy, n_kpoints)
    
    def calculate_effective_masses(self) -> EffectiveMasses:
        """Calculate effective masses"""
        return self._tb.calculate_effective_masses()


# ============================================================================
# HIGH-LEVEL API
# ============================================================================

def calculate_electronic_structure(
    alloy_name: str,
    x: float,
    calculate_bs: bool = True,
    calculate_dos: bool = True,
    calculate_masses: bool = True
) -> Dict:
    """
    Calculate electronic structure for an alloy composition.

    Args:
        alloy_name: Name of alloy system
        x: Composition variable
        calculate_bs: Calculate band structure
        calculate_dos: Calculate DOS
        calculate_masses: Calculate effective masses

    Returns:
        Dictionary with results
    """
    tb = TightBindingAlloy(alloy_name, x)
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
        dos = tb.calculate_dos()
        results['dos'] = dos

    if calculate_masses:
        masses = tb.calculate_effective_masses()
        results['effective_masses'] = masses

    return results


def calculate_material_electronic_structure(
    material_name: str,
    calculate_bs: bool = True,
    calculate_dos: bool = True,
    calculate_masses: bool = True
) -> Dict:
    """
    Calculate electronic structure for a binary material.
    
    Args:
        material_name: Name of the material (e.g., 'GaAs', 'AlAs')
        calculate_bs: Calculate band structure
        calculate_dos: Calculate DOS
        calculate_masses: Calculate effective masses
    
    Returns:
        Dictionary with results
    """
    tb = TightBindingMaterial(material_name)
    results = {'material': material_name}
    
    if calculate_bs:
        bs = tb.calculate_band_structure()
        results['band_structure'] = bs
        results['band_gap'] = bs.band_gap
        results['is_direct'] = bs.is_direct
    
    if calculate_dos:
        dos = tb.calculate_dos()
        results['dos'] = dos
    
    if calculate_masses:
        masses = tb.calculate_effective_masses()
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
    # Example 1: Generic alloy calculation
    print("Example 1: AlGaAs at x=0.5")
    results = calculate_electronic_structure("AlGaAs", 0.5)
    print(f"  Band gap: {results['band_gap']:.3f} eV")
    print(f"  Direct: {results['is_direct']}")

    # Example 2: Binary material calculation
    print("\nExample 2: Pure GaAs")
    results_gaas = calculate_material_electronic_structure("GaAs")
    print(f"  Band gap: {results_gaas['band_gap']:.3f} eV")
    print(f"  Direct: {results_gaas['is_direct']}")

    print("\nAll calculations completed successfully!")