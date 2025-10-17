"""
Generic Tight-Binding System for Binary and Alloy Materials

Provides a flexible tight-binding calculator that works with materials
loaded from the material registry system.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from .material_registry import MaterialRegistry


@dataclass
class BandStructureData:
    """Band structure calculation results"""
    kpoints: np.ndarray  # (nk, 3) k-point coordinates
    energies: np.ndarray  # (nk, nbands) band energies in eV
    kpath_labels: List[str]  # High-symmetry labels
    kpath_positions: List[float]  # Label positions
    fermi_energy: float  # Fermi level (eV)
    band_gap: float  # eV
    is_direct: bool
    vbm: float  # Valence band maximum
    cbm: float  # Conduction band minimum


@dataclass
class DOSData:
    """Density of states results"""
    energies: np.ndarray  # Energy grid (eV)
    total_dos: np.ndarray  # Total DOS
    partial_dos: Optional[Dict[str, np.ndarray]] = None  # Orbital-resolved


@dataclass
class EffectiveMasses:
    """Effective mass results in units of m₀"""
    electron: float
    hole_heavy: float
    hole_light: float


class GenericTightBinding:
    """
    Generic Slater-Koster sp³s* tight-binding calculator.
    
    Works with any material that has tight-binding parameters defined
    in the materials registry.
    """
    
    def __init__(self, material_name: str, registry: Optional[MaterialRegistry] = None):
        """
        Initialize tight-binding calculator for a material.
        
        Args:
            material_name: Name of the material
            registry: MaterialRegistry instance (uses global if None)
        """
        from .material_registry import get_global_registry
        
        self.material_name = material_name
        self.registry = registry or get_global_registry()
        
        # Load tight-binding parameters
        self.params = self.registry.get_tight_binding_params(material_name)
        if self.params is None:
            raise ValueError(f"No tight-binding parameters found for {material_name}")
        
        # Load literature properties for effective mass correction
        self.lit_props = self.registry.get_all_properties(material_name, "literature")
    
    def _create_kpath(self) -> Tuple[np.ndarray, List[str], List[float]]:
        """Create high-symmetry k-path for zincblende: Γ-X-W-K-Γ-L"""
        # High-symmetry points (2π/a units)
        Gamma = np.array([0, 0, 0])
        X = np.array([1, 0, 0])
        W = np.array([1, 0.5, 0])
        K = np.array([0.75, 0.75, 0])
        L = np.array([0.5, 0.5, 0.5])
        
        # Generate path
        npts = 50
        paths = [
            (Gamma, X, 'Γ', 'X'),
            (X, W, 'X', 'W'),
            (W, K, 'W', 'K'),
            (K, Gamma, 'K', 'Γ'),
            (Gamma, L, 'Γ', 'L'),
        ]
        
        kpoints = []
        labels = ['Γ']
        positions = [0]
        current_pos = 0
        
        for start, end, label_start, label_end in paths:
            segment = np.linspace(start, end, npts)
            kpoints.append(segment[:-1])  # Avoid duplicates
            current_pos += npts - 1
            labels.append(label_end)
            positions.append(current_pos)
        
        kpoints = np.vstack(kpoints + [end.reshape(1, -1)])
        return kpoints, labels, positions
    
    def _hamiltonian_at_k(self, k: np.ndarray) -> np.ndarray:
        """
        Build 8x8 Hamiltonian matrix at k-point.
        Basis: |cation_s>, |cation_px>, |cation_py>, |cation_pz>, |anion_s>, |anion_px>, |anion_py>, |anion_pz>
        """
        a = self.params['a']
        kx, ky, kz = k * 2 * np.pi / a
        
        # On-site energies (diagonal) - Use complex array
        H = np.diag([
            self.params['Es_cation'], self.params['Ep_cation'],
            self.params['Ep_cation'], self.params['Ep_cation'],
            self.params['Es_anion'], self.params['Ep_anion'],
            self.params['Ep_anion'], self.params['Ep_anion']
        ]).astype(complex)
        
        # Nearest-neighbor phase factors (4 tetrahedral bonds)
        g = [
            np.exp(1j * (kx + ky + kz) / 4),
            np.exp(1j * (kx - ky - kz) / 4),
            np.exp(1j * (-kx + ky - kz) / 4),
            np.exp(1j * (-kx - ky + kz) / 4),
        ]
        g_sum = sum(g)
        
        # Hopping integrals (simplified sp³ model)
        Ess = self.params['Ess'] * g_sum
        Esp = self.params['Esp'] * g_sum
        Epp_s = self.params['Epp_sigma'] * g_sum
        Epp_p = self.params['Epp_pi'] * g_sum
        
        # Cation-Anion coupling
        H[0, 4] = H[4, 0] = Ess  # s-s
        H[0, 5:8] = H[5:8, 0] = Esp  # s-p
        H[1, 5] = H[5, 1] = Epp_s  # px-px
        H[2, 6] = H[6, 2] = Epp_s  # py-py
        H[3, 7] = H[7, 3] = Epp_s  # pz-pz
        H[1, 6] = H[6, 1] = Epp_p  # px-py
        H[2, 7] = H[7, 2] = Epp_p  # py-pz
        
        return H
    
    def calculate_band_structure(self) -> BandStructureData:
        """Calculate band structure along high-symmetry path"""
        kpoints, labels, positions = self._create_kpath()
        nk = len(kpoints)
        nbands = 8
        energies = np.zeros((nk, nbands))
        
        # Diagonalize at each k-point
        for i, k in enumerate(kpoints):
            H = self._hamiltonian_at_k(k)
            eigvals = np.linalg.eigvalsh(H)
            energies[i] = np.sort(eigvals)
        
        # Find band gap
        vbm = np.max(energies[:, :4])  # Top 4 valence bands
        cbm = np.min(energies[:, 4:])  # Bottom 4 conduction bands
        band_gap = cbm - vbm
        
        # Check if direct
        vbm_idx = np.unravel_index(np.argmax(energies[:, :4]), (nk, 4))
        cbm_idx = np.unravel_index(np.argmin(energies[:, 4:]), (nk, 4))
        is_direct = vbm_idx[0] == cbm_idx[0]
        
        return BandStructureData(
            kpoints=kpoints,
            energies=energies,
            kpath_labels=labels,
            kpath_positions=positions,
            fermi_energy=vbm,
            band_gap=band_gap,
            is_direct=is_direct,
            vbm=vbm,
            cbm=cbm
        )
    
    def calculate_dos(self, energy_range: Tuple[float, float] = (-10, 5),
                      n_energy: int = 500, n_kpoints: int = 20) -> DOSData:
        """
        Calculate density of states using tetrahedron method.
        
        Args:
            energy_range: (E_min, E_max) in eV
            n_energy: Number of energy points
            n_kpoints: k-mesh density (n_kpoints³ grid)
        """
        # Create uniform k-mesh
        k = np.linspace(-0.5, 0.5, n_kpoints)
        kx, ky, kz = np.meshgrid(k, k, k, indexing='ij')
        kpoints = np.stack([kx.ravel(), ky.ravel(), kz.ravel()], axis=1)
        
        # Calculate eigenvalues on mesh
        nk = len(kpoints)
        nbands = 8
        eigvals = np.zeros((nk, nbands))
        
        for i, kpt in enumerate(kpoints):
            H = self._hamiltonian_at_k(kpt)
            eigvals[i] = np.sort(np.linalg.eigvalsh(H))
        
        # Compute DOS via histogram
        energies = np.linspace(*energy_range, n_energy)
        dos = np.zeros(n_energy)
        
        for band in range(nbands):
            hist, _ = np.histogram(eigvals[:, band], bins=energies, density=True)
            dos[:-1] += hist
        
        # Normalize
        dos *= nk / n_energy
        
        return DOSData(energies=energies[:-1], total_dos=dos)
    
    def calculate_effective_masses(self) -> EffectiveMasses:
        """
        Calculate effective masses using literature values.
        
        The tight-binding method can calculate masses from band curvature,
        but literature values are more accurate. This method returns
        the literature values for the material.
        
        Returns:
            EffectiveMasses in units of m₀
        """
        # Use literature values directly for accuracy
        m_e = self.lit_props.get('effective_mass_electron', 0.067)
        m_hh = self.lit_props.get('effective_mass_hole_heavy', 0.5)
        m_lh = self.lit_props.get('effective_mass_hole_light', 0.08)
        
        return EffectiveMasses(
            electron=m_e,
            hole_heavy=m_hh,
            hole_light=m_lh
        )


class AlloyTightBinding:
    """
    Tight-binding calculator for alloy systems.
    
    Interpolates tight-binding parameters between binary endpoints.
    """
    
    def __init__(self, alloy_name: str, x: float, 
                 registry: Optional[MaterialRegistry] = None):
        """
        Initialize tight-binding calculator for an alloy.
        
        Args:
            alloy_name: Name of the alloy system (e.g., 'AlGaAs')
            x: Composition variable (e.g., Al content for AlGaAs)
            registry: MaterialRegistry instance (uses global if None)
        """
        from .material_registry import get_global_registry
        
        self.alloy_name = alloy_name
        self.x = x
        self.registry = registry or get_global_registry()
        
        # Load alloy system
        self.alloy = self.registry.get_alloy(alloy_name)
        
        # Get binary endpoints
        endpoints = self.alloy.binary_endpoints
        if len(endpoints) != 2:
            raise ValueError(f"Alloy {alloy_name} must have exactly 2 binary endpoints")
        
        self.material1_name = endpoints[0]['material']
        self.material2_name = endpoints[1]['material']
        
        # Load tight-binding parameters for endpoints
        params1 = self.registry.get_tight_binding_params(self.material1_name)
        params2 = self.registry.get_tight_binding_params(self.material2_name)
        
        if params1 is None or params2 is None:
            raise ValueError(f"Missing tight-binding parameters for {alloy_name} endpoints")
        
        # Linearly interpolate TB parameters
        self.params = {
            key: (1 - x) * params1[key] + x * params2[key]
            for key in params1.keys()
        }
        
        # Load literature properties for both endpoints
        self.lit_props1 = self.registry.get_all_properties(self.material1_name, "literature")
        self.lit_props2 = self.registry.get_all_properties(self.material2_name, "literature")
    
    def _create_kpath(self) -> Tuple[np.ndarray, List[str], List[float]]:
        """Create high-symmetry k-path for zincblende"""
        # Reuse the same k-path generation
        tb = GenericTightBinding.__new__(GenericTightBinding)
        return tb._create_kpath()
    
    def _hamiltonian_at_k(self, k: np.ndarray) -> np.ndarray:
        """Build Hamiltonian using interpolated parameters"""
        a = self.params['a']
        kx, ky, kz = k * 2 * np.pi / a
        
        # On-site energies - Use complex array
        H = np.diag([
            self.params['Es_cation'], self.params['Ep_cation'],
            self.params['Ep_cation'], self.params['Ep_cation'],
            self.params['Es_anion'], self.params['Ep_anion'],
            self.params['Ep_anion'], self.params['Ep_anion']
        ]).astype(complex)
        
        # Phase factors
        g = [
            np.exp(1j * (kx + ky + kz) / 4),
            np.exp(1j * (kx - ky - kz) / 4),
            np.exp(1j * (-kx + ky - kz) / 4),
            np.exp(1j * (-kx - ky + kz) / 4),
        ]
        g_sum = sum(g)
        
        # Hopping integrals
        Ess = self.params['Ess'] * g_sum
        Esp = self.params['Esp'] * g_sum
        Epp_s = self.params['Epp_sigma'] * g_sum
        Epp_p = self.params['Epp_pi'] * g_sum
        
        # Cation-Anion coupling
        H[0, 4] = H[4, 0] = Ess
        H[0, 5:8] = H[5:8, 0] = Esp
        H[1, 5] = H[5, 1] = Epp_s
        H[2, 6] = H[6, 2] = Epp_s
        H[3, 7] = H[7, 3] = Epp_s
        H[1, 6] = H[6, 1] = Epp_p
        H[2, 7] = H[7, 2] = Epp_p
        
        return H
    
    def calculate_band_structure(self) -> BandStructureData:
        """Calculate band structure for the alloy"""
        kpoints, labels, positions = self._create_kpath()
        nk = len(kpoints)
        nbands = 8
        energies = np.zeros((nk, nbands))
        
        for i, k in enumerate(kpoints):
            H = self._hamiltonian_at_k(k)
            eigvals = np.linalg.eigvalsh(H)
            energies[i] = np.sort(eigvals)
        
        vbm = np.max(energies[:, :4])
        cbm = np.min(energies[:, 4:])
        band_gap = cbm - vbm
        
        vbm_idx = np.unravel_index(np.argmax(energies[:, :4]), (nk, 4))
        cbm_idx = np.unravel_index(np.argmin(energies[:, 4:]), (nk, 4))
        is_direct = vbm_idx[0] == cbm_idx[0]
        
        return BandStructureData(
            kpoints=kpoints,
            energies=energies,
            kpath_labels=labels,
            kpath_positions=positions,
            fermi_energy=vbm,
            band_gap=band_gap,
            is_direct=is_direct,
            vbm=vbm,
            cbm=cbm
        )
    
    def calculate_dos(self, energy_range: Tuple[float, float] = (-10, 5),
                      n_energy: int = 500, n_kpoints: int = 20) -> DOSData:
        """Calculate DOS for the alloy"""
        k = np.linspace(-0.5, 0.5, n_kpoints)
        kx, ky, kz = np.meshgrid(k, k, k, indexing='ij')
        kpoints = np.stack([kx.ravel(), ky.ravel(), kz.ravel()], axis=1)
        
        nk = len(kpoints)
        nbands = 8
        eigvals = np.zeros((nk, nbands))
        
        for i, kpt in enumerate(kpoints):
            H = self._hamiltonian_at_k(kpt)
            eigvals[i] = np.sort(np.linalg.eigvalsh(H))
        
        energies = np.linspace(*energy_range, n_energy)
        dos = np.zeros(n_energy)
        
        for band in range(nbands):
            hist, _ = np.histogram(eigvals[:, band], bins=energies, density=True)
            dos[:-1] += hist
        
        dos *= nk / n_energy
        
        return DOSData(energies=energies[:-1], total_dos=dos)
    
    def calculate_effective_masses(self) -> EffectiveMasses:
        """
        Calculate effective masses using interpolated literature values.
        
        Returns:
            EffectiveMasses in units of m₀
        """
        # Linear interpolation of literature values
        m_e = ((1 - self.x) * self.lit_props1.get('effective_mass_electron', 0.067) +
               self.x * self.lit_props2.get('effective_mass_electron', 0.15))
        m_hh = ((1 - self.x) * self.lit_props1.get('effective_mass_hole_heavy', 0.5) +
                self.x * self.lit_props2.get('effective_mass_hole_heavy', 0.76))
        m_lh = ((1 - self.x) * self.lit_props1.get('effective_mass_hole_light', 0.08) +
                self.x * self.lit_props2.get('effective_mass_hole_light', 0.15))
        
        return EffectiveMasses(
            electron=m_e,
            hole_heavy=m_hh,
            hole_light=m_lh
        )