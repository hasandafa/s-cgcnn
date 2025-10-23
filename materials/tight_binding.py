"""
Generic Tight-Binding System for Binary and Alloy Materials

Provides a flexible tight-binding calculator that works with materials
loaded from the material registry system.

"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings

from scipy.stats import gaussian_kde
from scipy.optimize import curve_fit
from scipy.sparse import csr_matrix, linalg as sparse_linalg

from pymatgen.core import Structure, Lattice
from pymatgen.electronic_structure.core import Spin
from pymatgen.electronic_structure.bandstructure import BandStructureSymmLine
from pymatgen.electronic_structure.dos import CompleteDos, Dos

from .material_registry import MaterialRegistry


# ============================================================================
# PHYSICAL CONSTANTS
# ============================================================================
HBAR = 1.054571817e-34  # J·s
M_E = 9.1093837015e-31  # kg (electron mass)
EV_TO_J = 1.602176634e-19  # J/eV
ANGSTROM_TO_M = 1e-10  # m/Å
# Effective mass unit conversion: m*/m_e = (ℏ²/m_e) / (eV·Å²)
M_EFF_UNIT = (HBAR**2 / M_E) / (EV_TO_J * ANGSTROM_TO_M**2)


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
    
    def __init__(self, material_name: str, registry: Optional[MaterialRegistry] = None,
                 structure: Optional[Structure] = None):
        """
        Initialize tight-binding calculator for a material.
        
        Args:
            material_name: Name of the material
            registry: MaterialRegistry instance (uses global if None)
            structure: pymatgen Structure object (for advanced k-path generation)
        """
        from .material_registry import get_global_registry
        
        self.material_name = material_name
        self.registry = registry or get_global_registry()
        self.structure = structure
        
        # Load tight-binding parameters
        self.params = self.registry.get_tight_binding_params(material_name)
        if self.params is None:
            raise ValueError(f"No tight-binding parameters found for {material_name}")
        
        # Load literature properties for effective mass correction
        self.lit_props = self.registry.get_all_properties(material_name, "literature")
        
        # Create structure from parameters if not provided
        if self.structure is None:
            self.structure = self._create_structure_from_params()
    
    def _create_structure_from_params(self) -> Structure:
        """Create a pymatgen Structure from tight-binding parameters"""
        a = self.params['a']
        lattice = Lattice.cubic(a)
        
        # Create a minimal structure for compatibility
        # In a more sophisticated implementation, this would be determined from material properties
        species = ['X', 'Y']  # Generic species
        coords = [[0, 0, 0], [0.25, 0.25, 0.25]]
        
        return Structure(lattice, species, coords)
    
    def _create_kpath(self, npts_per_segment: int = 50) -> Tuple[np.ndarray, List[str], List[float]]:
        """
        Create high-symmetry k-path using crystal structure metadata.
        
        Args:
            npts_per_segment: Number of k-points per segment
            
        Returns:
            Tuple of (kpoints array, labels, label positions)
        """
        # Use crystal structure metadata from YAML
        try:
            from .material_registry import get_global_registry
            registry = get_global_registry()
            crystal_metadata = registry.get_material(self.material_name).crystal_structure
            
            if crystal_metadata and 'kpath_points' in crystal_metadata and crystal_metadata['kpath_points']:
                # Use k-path points from crystal structure metadata
                kpts_dict = {}
                for point in crystal_metadata['kpath_points']:
                    # Convert label (handle LaTeX in labels)
                    label = point['label']
                    if label == '\\Gamma':
                        label = 'Γ'
                    kpts_dict[label] = np.array(point['coordinates'])
                
                # Define standard paths for cubic systems
                if crystal_metadata.get('crystal_system') == 'cubic':
                    path = [['Γ', 'X', 'W', 'K', 'Γ', 'L']]
                else:
                    # For other systems, use a simple path
                    labels = list(kpts_dict.keys())
                    path = [labels] if labels else []
                
                if path:
                    kpoints_list = []
                    labels = []
                    positions = [0]
                    current_pos = 0
                    
                    for segment in path:
                        for i in range(len(segment) - 1):
                            start_label = segment[i]
                            end_label = segment[i + 1]
                            
                            if start_label in kpts_dict and end_label in kpts_dict:
                                start_kpt = kpts_dict[start_label]
                                end_kpt = kpts_dict[end_label]
                                
                                # Generate segment
                                segment_kpts = np.linspace(start_kpt, end_kpt, npts_per_segment)
                                kpoints_list.append(segment_kpts[:-1])  # Avoid duplicates
                                
                                if i == 0:
                                    labels.append(start_label)
                                
                                current_pos += npts_per_segment - 1
                                labels.append(end_label)
                                positions.append(current_pos)
                        
                        # Add final point of segment if it exists
                        if segment and segment[-1] in kpts_dict:
                            end_kpt = kpts_dict[segment[-1]]
                            kpoints_list.append(end_kpt.reshape(1, -1))
                            current_pos += 1
                    
                    if kpoints_list:
                        kpoints = np.vstack(kpoints_list)
                        return kpoints, labels, positions
        except Exception as e:
            warnings.warn(f"Failed to use crystal structure metadata for k-path: {e}.")
        
        # If we can't generate a k-path from metadata, raise an error
        raise ValueError(f"Could not generate k-path for {self.material_name}. "
                         f"Crystal structure metadata is missing or invalid.")
    
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
    
    def calculate_band_structure(self, use_sparse: bool = False) -> BandStructureData:
        """
        Calculate band structure along high-symmetry path.
        
        Args:
            use_sparse: Use sparse matrix methods for large systems
            
        Returns:
            BandStructureData object
        """
        kpoints, labels, positions = self._create_kpath()
        nk = len(kpoints)
        nbands = 8
        energies = np.zeros((nk, nbands))
        
        # Diagonalize at each k-point
        for i, k in enumerate(kpoints):
            H = self._hamiltonian_at_k(k)
            
            if use_sparse and nbands > 20:
                # Use sparse methods for large systems
                H_sparse = csr_matrix(H)
                eigvals, _ = sparse_linalg.eigsh(H_sparse, k=min(nbands, H.shape[0]-1), which='SA')
                energies[i] = np.sort(eigvals)
            else:
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
    
    def get_pymatgen_band_structure(self) -> BandStructureSymmLine:
        """
        Get band structure as pymatgen BandStructureSymmLine object.
        
        Returns:
            BandStructureSymmLine object for analysis and plotting
        """
        bs_data = self.calculate_band_structure()
        
        # Convert k-points to pymatgen format
        from pymatgen.core.lattice import Lattice as PmgLattice
        from pymatgen.electronic_structure.core import Kpoint
        
        lattice = PmgLattice.cubic(self.params['a'])
        
        # Create eigenvals dict for pymatgen
        eigenvals = {Spin.up: bs_data.energies.T}  # Shape: (nbands, nkpts)
        
        # Create k-point objects
        kpoints_obj = [Kpoint(k, lattice) for k in bs_data.kpoints]
        
        # Create labels dictionary
        labels_dict = {label: kpoints_obj[int(pos)]
                      for label, pos in zip(bs_data.kpath_labels, bs_data.kpath_positions)}
        
        # Create BandStructureSymmLine
        bs = BandStructureSymmLine(
            kpoints=kpoints_obj,
            eigenvals=eigenvals,
            lattice=lattice.reciprocal_lattice,
            efermi=bs_data.fermi_energy,
            labels_dict=labels_dict
        )
        
        return bs
    
    def get_pymatgen_dos(self, **dos_kwargs) -> CompleteDos:
        """
        Get DOS as pymatgen CompleteDos object.
        
        Args:
            **dos_kwargs: Arguments passed to calculate_dos()
            
        Returns:
            CompleteDos object for analysis and plotting
        """
        dos_data = self.calculate_dos(**dos_kwargs)
        
        # Create Dos object
        dos_obj = Dos(
            efermi=0.0,  # Reference to VBM
            energies=dos_data.energies,
            densities={Spin.up: dos_data.total_dos}
        )
        
        # Create CompleteDos
        complete_dos = CompleteDos(
            structure=self.structure,
            total_dos=dos_obj
        )
        
        return complete_dos
    
    def calculate_dos(self, energy_range: Tuple[float, float] = (-10, 5),
                      n_energy: int = 500, n_kpoints: int = 20,
                      method: str = "gaussian_kde", sigma: float = 0.1) -> DOSData:
        """
        Calculate density of states using advanced methods.
        
        Args:
            energy_range: (E_min, E_max) in eV
            n_energy: Number of energy points
            n_kpoints: k-mesh density (n_kpoints³ grid)
            method: "gaussian_kde", "gaussian_broadening", or "histogram" (legacy)
            sigma: Broadening parameter (eV) for Gaussian methods
            
        Returns:
            DOSData with enhanced DOS calculation
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
        
        # Energy grid
        energies = np.linspace(*energy_range, n_energy)
        
        if method == "gaussian_kde":
            # Use Kernel Density Estimation for smooth DOS
            dos = np.zeros(n_energy)
            for band in range(nbands):
                band_energies = eigvals[:, band]
                # Use gaussian_kde with appropriate bandwidth
                try:
                    kde = gaussian_kde(band_energies, bw_method=sigma/band_energies.std())
                    dos += kde(energies)
                except np.linalg.LinAlgError:
                    # Fallback to histogram if KDE fails
                    hist, _ = np.histogram(band_energies, bins=energies, density=True)
                    dos[:-1] += hist
                    
        elif method == "gaussian_broadening":
            # Manual Gaussian broadening
            dos = np.zeros(n_energy)
            for band in range(nbands):
                for E_k in eigvals[:, band]:
                    dos += np.exp(-((energies - E_k) / sigma)**2) / (sigma * np.sqrt(np.pi))
            dos /= nk
            
        else:  # histogram (legacy method)
            dos = np.zeros(n_energy)
            for band in range(nbands):
                hist, _ = np.histogram(eigvals[:, band], bins=energies, density=True)
                dos[:-1] += hist
            dos *= nk / n_energy
            energies = energies[:-1]
        
        return DOSData(energies=energies, total_dos=dos)
    
    def calculate_effective_masses(self, method: str = "literature") -> EffectiveMasses:
        """
        Calculate effective masses using different methods.
        
        Args:
            method: "literature" (uses experimental values) or
                   "parabolic_fit" (calculates from band curvature)
        
        Returns:
            EffectiveMasses in units of m₀
        """
        if method == "literature":
            # Use literature values directly for accuracy
            m_e = self.lit_props.get('effective_mass_electron', 0.067)
            m_hh = self.lit_props.get('effective_mass_hole_heavy', 0.5)
            m_lh = self.lit_props.get('effective_mass_hole_light', 0.08)
            
            return EffectiveMasses(
                electron=m_e,
                hole_heavy=m_hh,
                hole_light=m_lh
            )
        
        elif method == "parabolic_fit":
            # Calculate from band curvature
            return self._calculate_effective_masses_from_bands()
        
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _calculate_effective_masses_from_bands(self) -> EffectiveMasses:
        """
        Calculate effective masses from parabolic fit near band extrema.
        
        Uses E(k) = E₀ + ℏ²k²/(2m*) approximation near Γ point.
        
        Returns:
            EffectiveMasses in units of m₀
        """
        # Generate k-points near Γ point
        k_range = np.linspace(-0.05, 0.05, 21)  # Small range around Γ
        kpoints = np.array([[k, 0, 0] for k in k_range])
        
        # Calculate band energies
        energies = np.zeros((len(kpoints), 8))
        for i, k in enumerate(kpoints):
            H = self._hamiltonian_at_k(k)
            energies[i] = np.sort(np.linalg.eigvalsh(H))
        
        # Parabolic fit function: E(k) = E0 + ak²
        def parabola(k, E0, a):
            return E0 + a * k**2
        
        try:
            # Electron mass (conduction band minimum - band 4)
            cb_energies = energies[:, 4]
            popt_e, _ = curve_fit(parabola, k_range, cb_energies, p0=[cb_energies[10], 1.0])
            # Convert curvature to effective mass: m* = ℏ²/(2·a·m_e)
            # a is in eV/Å², convert to SI then to m₀ units
            a = self.params['a']  # Lattice constant in Å
            curvature_e = popt_e[1] * (2 * np.pi / a)**2  # Convert to proper k-space
            m_e = M_EFF_UNIT / (2 * abs(curvature_e)) if curvature_e != 0 else 0.067
            
            # Heavy hole mass (valence band maximum - band 3)
            vb_heavy = energies[:, 3]
            popt_hh, _ = curve_fit(parabola, k_range, vb_heavy, p0=[vb_heavy[10], -1.0])
            curvature_hh = popt_hh[1] * (2 * np.pi / a)**2
            m_hh = M_EFF_UNIT / (2 * abs(curvature_hh)) if curvature_hh != 0 else 0.5
            
            # Light hole mass (valence band - band 2)
            vb_light = energies[:, 2]
            popt_lh, _ = curve_fit(parabola, k_range, vb_light, p0=[vb_light[10], -0.5])
            curvature_lh = popt_lh[1] * (2 * np.pi / a)**2
            m_lh = M_EFF_UNIT / (2 * abs(curvature_lh)) if curvature_lh != 0 else 0.08
            
        except (RuntimeError, TypeError) as e:
            warnings.warn(f"Effective mass fitting failed: {e}. Using literature values.")
            m_e = self.lit_props.get('effective_mass_electron', 0.067)
            m_hh = self.lit_props.get('effective_mass_hole_heavy', 0.5)
            m_lh = self.lit_props.get('effective_mass_hole_light', 0.08)
        
        return EffectiveMasses(
            electron=float(m_e),
            hole_heavy=float(m_hh),
            hole_light=float(m_lh)
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
    
    def _create_kpath(self, npts_per_segment: int = 50) -> Tuple[np.ndarray, List[str], List[float]]:
        """
        Create high-symmetry k-path using crystal structure metadata from endpoints.
        
        Args:
            npts_per_segment: Number of k-points per segment
            
        Returns:
            Tuple of (kpoints array, labels, label positions)
        """
        # Use crystal structure metadata from the first endpoint material
        try:
            from .material_registry import get_global_registry
            registry = get_global_registry()
            
            # Get crystal structure metadata from the first endpoint
            crystal_metadata = registry.get_material(self.material1_name).crystal_structure
            
            if crystal_metadata and 'kpath_points' in crystal_metadata and crystal_metadata['kpath_points']:
                # Use k-path points from crystal structure metadata
                kpts_dict = {}
                for point in crystal_metadata['kpath_points']:
                    # Convert label (handle LaTeX in labels)
                    label = point['label']
                    if label == '\\Gamma':
                        label = 'Γ'
                    kpts_dict[label] = np.array(point['coordinates'])
                
                # Define standard paths for cubic systems
                if crystal_metadata.get('crystal_system') == 'cubic':
                    path = [['Γ', 'X', 'W', 'K', 'Γ', 'L']]
                else:
                    # For other systems, use a simple path
                    labels = list(kpts_dict.keys())
                    path = [labels] if labels else []
                
                if path:
                    kpoints_list = []
                    labels = []
                    positions = [0]
                    current_pos = 0
                    
                    for segment in path:
                        for i in range(len(segment) - 1):
                            start_label = segment[i]
                            end_label = segment[i + 1]
                            
                            if start_label in kpts_dict and end_label in kpts_dict:
                                start_kpt = kpts_dict[start_label]
                                end_kpt = kpts_dict[end_label]
                                
                                # Generate segment
                                segment_kpts = np.linspace(start_kpt, end_kpt, npts_per_segment)
                                kpoints_list.append(segment_kpts[:-1])  # Avoid duplicates
                                
                                if i == 0:
                                    labels.append(start_label)
                                
                                current_pos += npts_per_segment - 1
                                labels.append(end_label)
                                positions.append(current_pos)
                        
                        # Add final point of segment if it exists
                        if segment and segment[-1] in kpts_dict:
                            end_kpt = kpts_dict[segment[-1]]
                            kpoints_list.append(end_kpt.reshape(1, -1))
                            current_pos += 1
                    
                    if kpoints_list:
                        kpoints = np.vstack(kpoints_list)
                        return kpoints, labels, positions
        except Exception as e:
            warnings.warn(f"Failed to use crystal structure metadata for k-path: {e}.")
        
        # If we can't generate a k-path from metadata, raise an error
        raise ValueError(f"Could not generate k-path for alloy {self.alloy_name}. "
                         f"Crystal structure metadata is missing or invalid for {self.material1_name}.")
    
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
                      n_energy: int = 500, n_kpoints: int = 20,
                      method: str = "gaussian_kde", sigma: float = 0.1) -> DOSData:
        """
        Calculate DOS for the alloy using advanced methods.
        
        Args:
            energy_range: (E_min, E_max) in eV
            n_energy: Number of energy points
            n_kpoints: k-mesh density (n_kpoints³ grid)
            method: "gaussian_kde", "gaussian_broadening", or "histogram"
            sigma: Broadening parameter (eV)
        """
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
        
        if method == "gaussian_kde":
            dos = np.zeros(n_energy)
            for band in range(nbands):
                band_energies = eigvals[:, band]
                try:
                    kde = gaussian_kde(band_energies, bw_method=sigma/band_energies.std())
                    dos += kde(energies)
                except np.linalg.LinAlgError:
                    hist, _ = np.histogram(band_energies, bins=energies, density=True)
                    dos[:-1] += hist
        elif method == "gaussian_broadening":
            dos = np.zeros(n_energy)
            for band in range(nbands):
                for E_k in eigvals[:, band]:
                    dos += np.exp(-((energies - E_k) / sigma)**2) / (sigma * np.sqrt(np.pi))
            dos /= nk
        else:  # histogram
            dos = np.zeros(n_energy)
            for band in range(nbands):
                hist, _ = np.histogram(eigvals[:, band], bins=energies, density=True)
                dos[:-1] += hist
            dos *= nk / n_energy
            energies = energies[:-1]
        
        return DOSData(energies=energies, total_dos=dos)
    
    def calculate_effective_masses(self, method: str = "literature") -> EffectiveMasses:
        """
        Calculate effective masses using different methods.
        
        Args:
            method: "literature" (interpolated experimental values) or
                   "parabolic_fit" (calculated from band curvature)
        
        Returns:
            EffectiveMasses in units of m₀
        """
        if method == "literature":
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
        
        elif method == "parabolic_fit":
            # Calculate from band curvature
            return self._calculate_effective_masses_from_bands()
        
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _calculate_effective_masses_from_bands(self) -> EffectiveMasses:
        """Calculate effective masses from parabolic fit near band extrema."""
        k_range = np.linspace(-0.05, 0.05, 21)
        kpoints = np.array([[k, 0, 0] for k in k_range])
        
        energies = np.zeros((len(kpoints), 8))
        for i, k in enumerate(kpoints):
            H = self._hamiltonian_at_k(k)
            energies[i] = np.sort(np.linalg.eigvalsh(H))
        
        def parabola(k, E0, a):
            return E0 + a * k**2
        
        try:
            # Electron mass
            cb_energies = energies[:, 4]
            popt_e, _ = curve_fit(parabola, k_range, cb_energies, p0=[cb_energies[10], 1.0])
            a = self.params['a']
            curvature_e = popt_e[1] * (2 * np.pi / a)**2
            m_e = M_EFF_UNIT / (2 * abs(curvature_e)) if curvature_e != 0 else 0.067
            
            # Heavy hole mass
            vb_heavy = energies[:, 3]
            popt_hh, _ = curve_fit(parabola, k_range, vb_heavy, p0=[vb_heavy[10], -1.0])
            curvature_hh = popt_hh[1] * (2 * np.pi / a)**2
            m_hh = M_EFF_UNIT / (2 * abs(curvature_hh)) if curvature_hh != 0 else 0.5
            
            # Light hole mass
            vb_light = energies[:, 2]
            popt_lh, _ = curve_fit(parabola, k_range, vb_light, p0=[vb_light[10], -0.5])
            curvature_lh = popt_lh[1] * (2 * np.pi / a)**2
            m_lh = M_EFF_UNIT / (2 * abs(curvature_lh)) if curvature_lh != 0 else 0.08
            
        except (RuntimeError, TypeError) as e:
            warnings.warn(f"Effective mass fitting failed: {e}. Using literature values.")
            m_e = ((1 - self.x) * self.lit_props1.get('effective_mass_electron', 0.067) +
                   self.x * self.lit_props2.get('effective_mass_electron', 0.15))
            m_hh = ((1 - self.x) * self.lit_props1.get('effective_mass_hole_heavy', 0.5) +
                    self.x * self.lit_props2.get('effective_mass_hole_heavy', 0.76))
            m_lh = ((1 - self.x) * self.lit_props1.get('effective_mass_hole_light', 0.08) +
                    self.x * self.lit_props2.get('effective_mass_hole_light', 0.15))
        
        return EffectiveMasses(
            electron=float(m_e),
            hole_heavy=float(m_hh),
            hole_light=float(m_lh)
        )