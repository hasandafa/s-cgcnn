"""
Materials Project API Fetcher - Version 0.1.1
Enhanced for dual-mode property extraction

Fetches structures and properties from Materials Project API.
Compatible with mp-api >= 0.41.2

Author: Abdullah Hasan Dafa
"""

from typing import Dict, Optional, Any, List
from pathlib import Path
import json

from mp_api.client import MPRester
from pymatgen.core import Structure
import numpy as np

from ..utils.logger_config import setup_logger
from ..utils import constants


# ============================================================================
# MATERIALS PROJECT FETCHER CLASS
# ============================================================================
class MPFetcher:
    """
    Fetches material data from Materials Project API.
    
    Features:
    - Structure retrieval
    - Electronic properties (band structure, DOS)
    - Mechanical properties (elastic tensor)
    - Thermodynamic properties (formation energy, stability)
    - Dielectric properties
    - Automatic retry on connection errors
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_key_file: Optional[Path] = None,
        config: Optional[Dict] = None,
        logger=None
    ):
        """
        Initialize MP API fetcher.
        
        Args:
            api_key: MP API key (if None, reads from file)
            api_key_file: Path to file containing API key
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config or {}
        self.logger = logger or setup_logger("MPFetcher")
        
        # Get API key
        if api_key:
            self.api_key = api_key
        elif api_key_file:
            self.api_key = self._read_api_key(api_key_file)
        else:
            # Try default location from config
            default_path = Path(
                self.config.get("materials_project", {}).get(
                    "api_key_file", "config/mp_api_key.txt"
                )
            )
            self.api_key = self._read_api_key(default_path)
        
        # Get API configuration
        mp_config = self.config.get("materials_project", {})
        self.timeout = mp_config.get("timeout", 30)
        self.max_retries = mp_config.get("max_retries", 3)
        
        # Material IDs
        self.gaas_mp_id = mp_config.get("gaas_mp_id", "mp-2534")
        self.alas_mp_id = mp_config.get("alas_mp_id", "mp-2172")
        
        self.logger.info("Initialized MPFetcher (v0.1.1)")
        self.logger.info(f"GaAs: {self.gaas_mp_id}, AlAs: {self.alas_mp_id}")
    
    def _read_api_key(self, filepath: Path) -> str:
        """Read API key from file"""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(
                f"MP API key file not found: {filepath}\n"
                "Please create the file with your API key from materialsproject.org"
            )
        
        with open(filepath, 'r') as f:
            api_key = f.read().strip()
        
        if not api_key:
            raise ValueError(f"API key file is empty: {filepath}")
        
        return api_key
    
    # ========================================================================
    # STRUCTURE FETCHING
    # ========================================================================
    
    def fetch_structure(self, mp_id: str) -> Structure:
        """
        Fetch structure from Materials Project.
        
        Args:
            mp_id: Materials Project ID (e.g., "mp-2534")
        
        Returns:
            pymatgen Structure object
        """
        self.logger.info(f"Fetching structure for {mp_id}")
        
        with MPRester(self.api_key) as mpr:
            try:
                # Get structure (conventional cell)
                structure = mpr.get_structure_by_material_id(
                    mp_id,
                    conventional_unit_cell=False  # Use primitive cell
                )
                
                self.logger.info(
                    f"Successfully fetched {mp_id}: "
                    f"{structure.composition.reduced_formula}, "
                    f"a={structure.lattice.a:.4f} Å"
                )
                
                return structure
                
            except Exception as e:
                self.logger.error(f"Failed to fetch structure {mp_id}: {e}")
                raise
    
    def fetch_gaas_structure(self) -> Structure:
        """Fetch GaAs structure"""
        return self.fetch_structure(self.gaas_mp_id)
    
    def fetch_alas_structure(self) -> Structure:
        """Fetch AlAs structure"""
        return self.fetch_structure(self.alas_mp_id)
    
    # ========================================================================
    # PROPERTY FETCHING (NEW in v0.1.1)
    # ========================================================================
    
    def fetch_all_properties(
        self,
        mp_id: str,
        apply_bandgap_correction: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch all available properties for a material.
        
        This populates the MP-API property dictionaries in constants.py
        
        Args:
            mp_id: Materials Project ID
            apply_bandgap_correction: Apply scissor shift correction to band gap
        
        Returns:
            Dictionary of all fetched properties
        """
        self.logger.info(f"Fetching all properties for {mp_id}")
        
        properties = {}
        
        with MPRester(self.api_key) as mpr:
            # ================================================================
            # 1. SUMMARY DATA (basic properties)
            # ================================================================
            try:
                summary = mpr.materials.summary.search(
                    material_ids=[mp_id],
                    fields=[
                        "material_id",
                        "formula_pretty",
                        "structure",
                        "volume",
                        "density",
                        "symmetry",
                        "is_stable",
                        "is_metal",
                        "is_magnetic",
                    ]
                )
                
                if summary:
                    s = summary[0]
                    
                    # Physical properties from structure
                    structure = s.structure
                    properties["lattice_constant"] = structure.lattice.a
                    properties["volume"] = s.volume
                    properties["density"] = s.density
                    
                    # Symmetry
                    properties["space_group"] = s.symmetry.symbol if s.symmetry else None
                    properties["crystal_system"] = s.symmetry.crystal_system if s.symmetry else None
                    properties["point_group"] = s.symmetry.point_group if s.symmetry else None
                    
                    # Boolean properties
                    properties["is_metal"] = s.is_metal
                    properties["is_magnetic"] = s.is_magnetic
                    properties["is_stable"] = s.is_stable
                    
                    self.logger.debug(f"Fetched summary data for {mp_id}")
                
            except Exception as e:
                self.logger.warning(f"Could not fetch summary data: {e}")
            
            # ================================================================
            # 2. ELECTRONIC STRUCTURE (band gap, VBM, CBM)
            # ================================================================
            try:
                electronic = mpr.materials.electronic_structure.search(
                    material_ids=[mp_id],
                    fields=[
                        "material_id",
                        "band_gap",
                        "is_gap_direct",
                        "is_metal",
                        "efermi",
                    ]
                )
                
                if electronic:
                    e = electronic[0]
                    
                    # Band gap (with optional correction)
                    raw_bandgap = e.band_gap
                    if apply_bandgap_correction and raw_bandgap > 0:
                        correction_config = self.config.get(
                            "interpolation", {}
                        ).get("mp_bandgap_correction", {})
                        
                        if correction_config.get("enabled", True):
                            factor = correction_config.get("correction_factor", 1.5)
                            corrected_bandgap = raw_bandgap * factor
                            
                            properties["band_gap_raw"] = raw_bandgap
                            properties["band_gap"] = corrected_bandgap
                            properties["band_gap_correction_factor"] = factor
                            
                            self.logger.info(
                                f"Band gap correction: {raw_bandgap:.3f} eV -> "
                                f"{corrected_bandgap:.3f} eV (factor={factor})"
                            )
                        else:
                            properties["band_gap"] = raw_bandgap
                    else:
                        properties["band_gap"] = raw_bandgap
                    
                    properties["is_gap_direct"] = e.is_gap_direct
                    properties["band_gap_type"] = "direct" if e.is_gap_direct else "indirect"
                    properties["is_metal"] = e.is_metal
                    properties["fermi_energy"] = e.efermi
                    
                    # Try to get VBM/CBM (may not always be available)
                    try:
                        # These might be in different format depending on MP version
                        properties["vbm"] = getattr(e, "vbm", None)
                        properties["cbm"] = getattr(e, "cbm", None)
                    except:
                        properties["vbm"] = None
                        properties["cbm"] = None
                    
                    self.logger.debug(
                        f"Fetched electronic structure: "
                        f"Eg={properties['band_gap']:.3f} eV "
                        f"({'direct' if e.is_gap_direct else 'indirect'})"
                    )
                
            except Exception as e:
                self.logger.warning(f"Could not fetch electronic structure: {e}")
            
            # ================================================================
            # 3. THERMODYNAMIC PROPERTIES
            # ================================================================
            try:
                thermo = mpr.materials.thermo.search(
                    material_ids=[mp_id],
                    fields=[
                        "material_id",
                        "formation_energy_per_atom",
                        "energy_above_hull",
                        "decomposes_to",
                    ]
                )
                
                if thermo:
                    t = thermo[0]
                    
                    properties["formation_energy_per_atom"] = t.formation_energy_per_atom
                    properties["energy_above_hull"] = t.energy_above_hull
                    properties["decomposes_to"] = t.decomposes_to
                    
                    self.logger.debug(
                        f"Fetched thermodynamics: "
                        f"ΔHf={t.formation_energy_per_atom:.3f} eV/atom, "
                        f"E_hull={t.energy_above_hull:.3f} eV/atom"
                    )
                
            except Exception as e:
                self.logger.warning(f"Could not fetch thermodynamics: {e}")
            
            # ================================================================
            # 4. ELASTIC PROPERTIES
            # ================================================================
            try:
                elastic = mpr.materials.elasticity.search(
                    material_ids=[mp_id],
                    fields=[
                        "material_id",
                        "elastic_tensor",
                        "bulk_modulus",
                        "shear_modulus",
                        "elastic_anisotropy",
                        "poisson_ratio",
                        "homogeneous_poisson",
                    ]
                )
                
                if elastic:
                    el = elastic[0]
                    
                    # Bulk and shear modulus - handle both dict and object formats
                    if hasattr(el, 'bulk_modulus'):
                        if hasattr(el.bulk_modulus, 'vrh'):
                            properties["bulk_modulus"] = el.bulk_modulus.vrh
                        elif isinstance(el.bulk_modulus, dict) and 'vrh' in el.bulk_modulus:
                            properties["bulk_modulus"] = el.bulk_modulus['vrh']
                        else:
                            properties["bulk_modulus"] = el.bulk_modulus
                    
                    if hasattr(el, 'shear_modulus'):
                        if hasattr(el.shear_modulus, 'vrh'):
                            properties["shear_modulus"] = el.shear_modulus.vrh
                        elif isinstance(el.shear_modulus, dict) and 'vrh' in el.shear_modulus:
                            properties["shear_modulus"] = el.shear_modulus['vrh']
                        else:
                            properties["shear_modulus"] = el.shear_modulus
                    
                    # Elastic tensor - handle different API versions
                    if hasattr(el, 'elastic_tensor') and el.elastic_tensor is not None:
                        tensor = el.elastic_tensor
                        
                        # Try different ways to get Voigt notation
                        if hasattr(tensor, 'voigt'):
                            voigt_matrix = tensor.voigt
                        elif hasattr(tensor, 'raw'):
                            voigt_matrix = tensor.raw
                        elif isinstance(tensor, np.ndarray):
                            voigt_matrix = tensor
                        else:
                            # Convert to numpy array if possible
                            try:
                                voigt_matrix = np.array(tensor)
                            except:
                                voigt_matrix = None
                        
                        if voigt_matrix is not None:
                            properties["elastic_tensor"] = voigt_matrix
                            
                            # Extract C11, C12, C44 for cubic crystals
                            try:
                                if isinstance(voigt_matrix, np.ndarray) and voigt_matrix.shape == (6, 6):
                                    properties["elastic_constant_c11"] = float(voigt_matrix[0, 0])
                                    properties["elastic_constant_c12"] = float(voigt_matrix[0, 1])
                                    properties["elastic_constant_c44"] = float(voigt_matrix[3, 3])
                            except:
                                pass
                    
                    if hasattr(el, 'elastic_anisotropy'):
                        properties["elastic_anisotropy"] = el.elastic_anisotropy
                    
                    if hasattr(el, 'homogeneous_poisson'):
                        properties["poissons_ratio"] = el.homogeneous_poisson
                    elif hasattr(el, 'poisson_ratio'):
                        properties["poissons_ratio"] = el.poisson_ratio
                    
                    # Calculate Young's modulus (approximate)
                    K = properties.get("bulk_modulus")
                    G = properties.get("shear_modulus")
                    if K and G:
                        try:
                            E = (9 * K * G) / (3 * K + G)  # GPa
                            properties["youngs_modulus"] = E
                        except:
                            pass
                    
                    self.logger.debug(
                        f"Fetched elastic properties: "
                        f"K={properties.get('bulk_modulus', 'N/A')}, "
                        f"G={properties.get('shear_modulus', 'N/A')}"
                    )
                
            except Exception as e:
                self.logger.warning(f"Could not fetch elastic properties: {e}")
            
            # ================================================================
            # 5. DIELECTRIC PROPERTIES
            # ================================================================
            try:
                dielectric = mpr.materials.dielectric.search(
                    material_ids=[mp_id],
                    fields=[
                        "material_id",
                        "total",
                        "electronic",
                        "ionic",
                        "e_total",
                        "e_electronic",
                        "e_ionic",
                        "n",
                    ]
                )
                
                if dielectric:
                    d = dielectric[0]
                    
                    # Dielectric constants (average of diagonal)
                    if hasattr(d, 'total') and d.total is not None:
                        eps_total = np.trace(d.total) / 3
                        properties["dielectric_constant_static"] = eps_total
                    
                    if hasattr(d, 'electronic') and d.electronic is not None:
                        eps_elec = np.trace(d.electronic) / 3
                        properties["dielectric_constant_electronic"] = eps_elec
                        properties["dielectric_constant_high_freq"] = eps_elec
                        
                        # Refractive index: n = sqrt(ε∞)
                        properties["refractive_index"] = np.sqrt(eps_elec)
                    
                    if hasattr(d, 'ionic') and d.ionic is not None:
                        eps_ionic = np.trace(d.ionic) / 3
                        properties["dielectric_constant_ionic"] = eps_ionic
                    
                    self.logger.debug(
                        f"Fetched dielectric properties: "
                        f"εs={properties.get('dielectric_constant_static', 'N/A'):.2f}, "
                        f"ε∞={properties.get('dielectric_constant_high_freq', 'N/A'):.2f}"
                    )
                
            except Exception as e:
                self.logger.warning(f"Could not fetch dielectric properties: {e}")
            
            # ================================================================
            # 6. MAGNETIC PROPERTIES
            # ================================================================
            try:
                magnetism = mpr.materials.magnetism.search(
                    material_ids=[mp_id],
                    fields=[
                        "material_id",
                        "total_magnetization",
                        "total_magnetization_normalized_vol",
                    ]
                )
                
                if magnetism:
                    m = magnetism[0]
                    
                    properties["total_magnetization"] = m.total_magnetization
                    properties["total_magnetization_normalized"] = m.total_magnetization_normalized_vol
                    
                    self.logger.debug(
                        f"Fetched magnetic properties: "
                        f"M={m.total_magnetization:.3f} μB"
                    )
                
            except Exception as e:
                self.logger.warning(f"Could not fetch magnetic properties: {e}")
        
        # ====================================================================
        # SUMMARY
        # ====================================================================
        num_properties = len([v for v in properties.values() if v is not None])
        self.logger.info(
            f"Successfully fetched {num_properties} properties for {mp_id}"
        )
        
        return properties
    
    def fetch_and_update_constants(
        self,
        update_constants_module: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch properties for GaAs and AlAs and optionally update constants.py
        
        Args:
            update_constants_module: If True, update constants.py dictionaries
        
        Returns:
            Dictionary with GaAs and AlAs properties
        """
        self.logger.info("Fetching properties for GaAs and AlAs from MP API")
        
        # Fetch GaAs properties
        gaas_props = self.fetch_all_properties(self.gaas_mp_id)
        
        # Fetch AlAs properties
        alas_props = self.fetch_all_properties(self.alas_mp_id)
        
        result = {
            "GaAs": gaas_props,
            "AlAs": alas_props
        }
        
        # Update constants module if requested
        if update_constants_module:
            self.logger.info("Updating constants.py with MP-API properties")
            
            # Update GAAS_PROPERTIES_MP_API
            for key, value in gaas_props.items():
                if key in constants.GAAS_PROPERTIES_MP_API:
                    constants.GAAS_PROPERTIES_MP_API[key] = value
            
            # Update ALAS_PROPERTIES_MP_API
            for key, value in alas_props.items():
                if key in constants.ALAS_PROPERTIES_MP_API:
                    constants.ALAS_PROPERTIES_MP_API[key] = value
            
            self.logger.info("Constants module updated successfully")
        
        return result
    
    # ========================================================================
    # EXPORT UTILITIES
    # ========================================================================
    
    def save_properties_to_json(
        self,
        properties: Dict[str, Any],
        filepath: Path,
        pretty: bool = True
    ):
        """Save properties dictionary to JSON file"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert numpy arrays and pymatgen objects to lists for JSON serialization
        def convert_types(obj):
            """Convert non-serializable types to JSON-compatible types"""
            import numpy as np
            from enum import Enum
            
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, Enum):
                # Convert pymatgen enums (CrystalSystem, etc.) to string
                return str(obj.value) if hasattr(obj, 'value') else str(obj)
            elif hasattr(obj, '__dict__'):
                # Convert objects with __dict__ to dict (pymatgen objects)
                return str(obj)
            return obj
        
        # Process all values
        props_serializable = {
            k: convert_types(v) for k, v in properties.items()
        }
        
        with open(filepath, 'w') as f:
            if pretty:
                json.dump(props_serializable, f, indent=2)
            else:
                json.dump(props_serializable, f)
        
        self.logger.info(f"Saved properties to {filepath}")


# ============================================================================
# MODULE FUNCTIONS
# ============================================================================

def create_fetcher_from_config(
    config: Dict,
    logger=None
) -> MPFetcher:
    """
    Create MPFetcher from configuration dictionary.
    
    Args:
        config: Configuration dictionary
        logger: Logger instance
    
    Returns:
        MPFetcher instance
    """
    return MPFetcher(config=config, logger=logger)


# ============================================================================
# MODULE METADATA
# ============================================================================

__version__ = "0.1.1"
__author__ = "Abdullah Hasan Dafa"