"""
Structure Interpolation Module - Version 0.1.1
Enhanced with dual data source: Literature vs MP-API

Generates AlₓGa₁₋ₓAs alloy structures with configurable property sources.

Author: Abdullah Hasan Dafa
"""

import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Literal, Any
import json
from dataclasses import dataclass, asdict

from pymatgen.core import Structure, Lattice, Element
from pymatgen.io.cif import CifWriter

from ..utils import constants
from ..utils.logger_config import setup_logger

# ============================================================================
# TYPE DEFINITIONS
# ============================================================================
DataSourceType = Literal["literature", "mp_api"]


# ============================================================================
# DATA CLASSES
# ============================================================================
@dataclass
class AlloyComposition:
    """Represents a specific AlGaAs composition"""
    x: float  # Al composition (0.0 to 1.0)
    formula: str  # e.g., "Al0.250Ga0.750As"
    num_al: int  # Number of Al atoms in supercell
    num_ga: int  # Number of Ga atoms in supercell
    is_discrete: bool  # True if exact discrete value, False if rounded


@dataclass
class AlloyProperties:
    """Complete property set for an alloy composition"""
    composition: AlloyComposition
    data_source: DataSourceType
    properties: Dict[str, Any]
    metadata: Dict[str, Any]


# ============================================================================
# STRUCTURE INTERPOLATOR CLASS
# ============================================================================
class StructureInterpolator:
    """
    Interpolates structures and properties for AlₓGa₁₋ₓAs alloys.
    
    Features:
    - Dual data source support (literature/mp_api)
    - Vegard's Law with bowing parameters
    - Direct-to-indirect band gap transition
    - Flexible property calculation
    """
    
    def __init__(
        self,
        gaas_structure: Structure,
        alas_structure: Structure,
        supercell_size: Tuple[int, int, int] = (2, 2, 2),
        data_source: DataSourceType = "literature",
        config: Optional[Dict] = None,
        logger = None
    ):
        """
        Initialize the structure interpolator.
        
        Args:
            gaas_structure: GaAs primitive structure
            alas_structure: AlAs primitive structure
            supercell_size: Size of supercell for substitution
            data_source: "literature" or "mp_api"
            config: Configuration dictionary
            logger: Logger instance
        """
        self.gaas_structure = gaas_structure
        self.alas_structure = alas_structure
        self.supercell_size = supercell_size
        self.data_source = data_source
        self.config = config or {}
        self.logger = logger or setup_logger("StructureInterpolator")
        
        # Create supercells
        self.gaas_supercell = self._create_supercell(gaas_structure)
        self.alas_supercell = self._create_supercell(alas_structure)
        
        # Calculate total Ga sites available for substitution
        self.total_ga_sites = sum(1 for site in self.gaas_supercell 
                                  if site.specie == Element("Ga"))
        
        # Load properties from selected source
        self.gaas_props = constants.get_properties("GaAs", data_source)
        self.alas_props = constants.get_properties("AlAs", data_source)
        
        self.logger.info(f"Initialized StructureInterpolator (v0.1.1)")
        self.logger.info(f"Data source: {data_source}")
        self.logger.info(f"Supercell: {supercell_size} ({self.total_ga_sites} Ga sites)")
        self.logger.info(f"GaAs lattice: {self.gaas_structure.lattice.a:.4f} Å")
        self.logger.info(f"AlAs lattice: {self.alas_structure.lattice.a:.4f} Å")
    
    # ========================================================================
    # STRUCTURE GENERATION
    # ========================================================================
    
    def _create_supercell(self, structure: Structure) -> Structure:
        """Create supercell from primitive structure"""
        supercell = structure.copy()
        supercell.make_supercell(self.supercell_size)
        return supercell
    
    def generate_alloy_structure(
        self,
        x: float,
        ordered: bool = True
    ) -> Tuple[Structure, AlloyComposition]:
        """
        Generate AlₓGa₁₋ₓAs structure for given composition.
        
        Args:
            x: Al composition (0.0 to 1.0)
            ordered: If True, use ordered substitution; if False, random
        
        Returns:
            Tuple of (Structure, AlloyComposition)
        """
        # Calculate discrete number of Al atoms
        num_al = round(x * self.total_ga_sites)
        num_ga = self.total_ga_sites - num_al
        actual_x = num_al / self.total_ga_sites
        
        # Check if composition is exactly achievable
        is_discrete = abs(x - actual_x) < 1e-6
        
        if not is_discrete:
            self.logger.debug(
                f"Composition x={x:.3f} rounded to x={actual_x:.3f} "
                f"({num_al} Al, {num_ga} Ga atoms)"
            )
        
        # Create composition object
        composition = AlloyComposition(
            x=actual_x,
            formula=f"Al{actual_x:.3f}Ga{1-actual_x:.3f}As",
            num_al=num_al,
            num_ga=num_ga,
            is_discrete=is_discrete
        )
        
        # Start from GaAs supercell
        alloy_structure = self.gaas_supercell.copy()
        
        # Find all Ga sites
        ga_indices = [i for i, site in enumerate(alloy_structure)
                     if site.specie == Element("Ga")]
        
        # Select sites for Al substitution
        if ordered:
            # Ordered substitution (first N sites)
            al_indices = ga_indices[:num_al]
        else:
            # Random substitution
            rng = np.random.default_rng(seed=42)
            al_indices = rng.choice(ga_indices, size=num_al, replace=False)
        
        # Perform substitution
        for idx in al_indices:
            alloy_structure.replace(idx, Element("Al"))
        
        # Interpolate lattice parameter
        lattice_param = self._interpolate_lattice_parameter(actual_x)
        
        # Update lattice (keep cubic symmetry)
        new_lattice = Lattice.cubic(lattice_param)
        alloy_structure.lattice = new_lattice
        
        self.logger.debug(
            f"Generated structure: {composition.formula}, "
            f"a={lattice_param:.4f} Å"
        )
        
        return alloy_structure, composition
    
    def _interpolate_lattice_parameter(self, x: float) -> float:
        """
        Interpolate lattice parameter using Vegard's Law.
        
        Args:
            x: Al composition
        
        Returns:
            Lattice parameter in Angstrom
        """
        if self.data_source == "literature":
            a_gaas = self.gaas_props["lattice_constant"]
            a_alas = self.alas_props["lattice_constant"]
        else:
            # For MP-API, use structure lattice parameters
            a_gaas = self.gaas_structure.lattice.a
            a_alas = self.alas_structure.lattice.a
        
        # Linear interpolation (bowing ~ 0 for lattice constant)
        a_alloy = (1 - x) * a_gaas + x * a_alas
        
        return a_alloy
    
    # ========================================================================
    # PROPERTY CALCULATION
    # ========================================================================
    
    def calculate_properties(
        self,
        x: float,
        fallback_to_literature: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate all properties for composition x using Vegard's Law.
        
        Args:
            x: Al composition (0.0 to 1.0)
            fallback_to_literature: If True and MP data unavailable, use literature
        
        Returns:
            Dictionary of calculated properties
        """
        properties = {}
        
        # Get property lists from config or use defaults
        property_config = self.config.get("property_calculation", {})
        property_groups = property_config.get("properties", {})
        
        # Flatten all property lists
        all_properties = []
        for group in property_groups.values():
            all_properties.extend(group)
        
        # Calculate each property
        for prop_name in all_properties:
            try:
                value = self._calculate_single_property(
                    prop_name, x, fallback_to_literature
                )
                properties[prop_name] = value
            except KeyError as e:
                self.logger.warning(
                    f"Property '{prop_name}' not available in {self.data_source} source: {e}"
                )
                properties[prop_name] = None
            except Exception as e:
                self.logger.error(
                    f"Error calculating '{prop_name}': {e}"
                )
                properties[prop_name] = None
        
        return properties
    
    def _calculate_single_property(
        self,
        property_name: str,
        x: float,
        fallback_to_literature: bool
    ) -> Any:
        """
        Calculate a single property using Vegard's Law with bowing.
        
        Args:
            property_name: Name of the property
            x: Al composition
            fallback_to_literature: Use literature values if MP unavailable
        
        Returns:
            Calculated property value
        """
        # Special handling for band gap type
        if property_name == "band_gap_type":
            return constants.determine_band_gap_type(x)
        
        # Get endpoint values
        try:
            p_gaas = self.gaas_props[property_name]
            p_alas = self.alas_props[property_name]
        except KeyError:
            if fallback_to_literature and self.data_source == "mp_api":
                # Fallback to literature values
                p_gaas = constants.GAAS_PROPERTIES_LITERATURE.get(property_name)
                p_alas = constants.ALAS_PROPERTIES_LITERATURE.get(property_name)
                if p_gaas is None or p_alas is None:
                    raise KeyError(
                        f"Property '{property_name}' not available in any source"
                    )
            else:
                raise
        
        # Handle None values (MP-API placeholders)
        if p_gaas is None or p_alas is None:
            if fallback_to_literature and self.data_source == "mp_api":
                p_gaas = constants.GAAS_PROPERTIES_LITERATURE.get(property_name)
                p_alas = constants.ALAS_PROPERTIES_LITERATURE.get(property_name)
                if p_gaas is None or p_alas is None:
                    raise ValueError(
                        f"Property '{property_name}' is None in MP-API and not available in literature"
                    )
            else:
                raise ValueError(f"Property '{property_name}' value is None")
        
        # Handle string properties (no interpolation)
        if isinstance(p_gaas, str) or isinstance(p_alas, str):
            return p_gaas if x < 0.5 else p_alas
        
        # Get bowing parameter
        bowing = constants.get_bowing_parameter(property_name)
        
        # Vegard's Law with bowing: P(x) = (1-x)P₁ + xP₂ - bx(1-x)
        value = (1 - x) * p_gaas + x * p_alas - bowing * x * (1 - x)
        
        return value
    
    # ========================================================================
    # BATCH GENERATION
    # ========================================================================
    
    def generate_composition_range(
        self,
        x_min: float = 0.0,
        x_max: float = 1.0,
        x_step: float = 0.025,
        output_dir: Optional[Path] = None,
        save_cif: bool = True,
        save_metadata: bool = True
    ) -> List[AlloyProperties]:
        """
        Generate structures and properties for a range of compositions.
        
        Args:
            x_min: Minimum Al composition
            x_max: Maximum Al composition
            x_step: Composition step size
            output_dir: Directory to save files (if None, don't save)
            save_cif: Save CIF files
            save_metadata: Save JSON metadata files
        
        Returns:
            List of AlloyProperties objects
        """
        # Generate composition array
        x_values = np.arange(x_min, x_max + x_step/2, x_step)
        
        self.logger.info(
            f"Generating {len(x_values)} compositions from "
            f"x={x_min:.3f} to x={x_max:.3f} (step={x_step})"
        )
        
        # Setup output directories
        if output_dir:
            output_dir = Path(output_dir)
            cif_dir = output_dir / "cif"
            metadata_dir = output_dir / "metadata"
            
            if save_cif:
                cif_dir.mkdir(parents=True, exist_ok=True)
            if save_metadata:
                metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate all compositions
        alloy_list = []
        
        for i, x in enumerate(x_values, 1):
            self.logger.info(f"Processing composition {i}/{len(x_values)}: x={x:.3f}")
            
            # Generate structure
            structure, composition = self.generate_alloy_structure(x)
            
            # Calculate properties
            properties = self.calculate_properties(
                composition.x,
                fallback_to_literature=self.config.get(
                    "interpolation", {}
                ).get("mp_api_fallback_to_literature", True)
            )
            
            # Create metadata
            metadata = self._create_metadata(
                composition, structure, properties
            )
            
            # Create AlloyProperties object
            alloy = AlloyProperties(
                composition=composition,
                data_source=self.data_source,
                properties=properties,
                metadata=metadata
            )
            
            alloy_list.append(alloy)
            
            # Save files
            if output_dir:
                filename_base = f"AlGaAs_x{composition.x:.3f}"
                
                if save_cif:
                    self._save_cif(structure, cif_dir / f"{filename_base}.cif")
                
                if save_metadata:
                    self._save_metadata(
                        alloy, metadata_dir / f"{filename_base}.json"
                    )
        
        self.logger.info(
            f"Successfully generated {len(alloy_list)} structures and properties"
        )
        
        return alloy_list
    
    def _create_metadata(
        self,
        composition: AlloyComposition,
        structure: Structure,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create metadata dictionary for a composition"""
        metadata = {
            "version": "0.1.1",
            "data_source": self.data_source,
            "composition": asdict(composition),
            "structure_info": {
                "formula": structure.composition.reduced_formula,
                "num_sites": len(structure),
                "lattice_abc": structure.lattice.abc,
                "lattice_angles": structure.lattice.angles,
                "volume": structure.lattice.volume,
                "density": structure.density,
            },
            "generation_method": "ordered_supercell_substitution",
            "supercell_size": list(self.supercell_size),
            "interpolation_method": "vegard_law_with_bowing",
        }
        
        return metadata
    
    def _save_cif(self, structure: Structure, filepath: Path):
        """Save structure as CIF file"""
        writer = CifWriter(structure)
        writer.write_file(str(filepath))
        self.logger.debug(f"Saved CIF: {filepath.name}")
    
    def _save_metadata(self, alloy: AlloyProperties, filepath: Path):
        """Save complete metadata as JSON"""
        
        # Helper function to convert numpy types to native Python types
        def convert_numpy(obj):
            """Convert numpy types to native Python types for JSON serialization"""
            import numpy as np
            
            if isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            else:
                return obj
        
        data = {
            "composition": convert_numpy(asdict(alloy.composition)),
            "data_source": alloy.data_source,
            "properties": convert_numpy(alloy.properties),
            "metadata": convert_numpy(alloy.metadata),
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.debug(f"Saved metadata: {filepath.name}")
    
    # ========================================================================
    # COMPARISON UTILITIES
    # ========================================================================
    
    def compare_data_sources(
        self,
        x: float,
        properties_to_compare: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare literature vs MP-API values for a specific composition.
        
        Args:
            x: Al composition
            properties_to_compare: List of properties (None = all common properties)
        
        Returns:
            Dictionary with comparison results
        """
        # Calculate with literature
        original_source = self.data_source
        
        self.data_source = "literature"
        self.gaas_props = constants.get_properties("GaAs", "literature")
        self.alas_props = constants.get_properties("AlAs", "literature")
        lit_props = self.calculate_properties(x, fallback_to_literature=False)
        
        # Calculate with MP-API
        self.data_source = "mp_api"
        self.gaas_props = constants.get_properties("GaAs", "mp_api")
        self.alas_props = constants.get_properties("AlAs", "mp_api")
        mp_props = self.calculate_properties(x, fallback_to_literature=False)
        
        # Restore original source
        self.data_source = original_source
        self.gaas_props = constants.get_properties("GaAs", original_source)
        self.alas_props = constants.get_properties("AlAs", original_source)
        
        # Determine properties to compare
        if properties_to_compare is None:
            properties_to_compare = list(set(lit_props.keys()) & set(mp_props.keys()))
        
        # Build comparison
        comparison = {
            "composition": x,
            "properties": {}
        }
        
        for prop in properties_to_compare:
            if prop in lit_props and prop in mp_props:
                lit_val = lit_props[prop]
                mp_val = mp_props[prop]
                
                if lit_val is not None and mp_val is not None:
                    if isinstance(lit_val, (int, float)) and isinstance(mp_val, (int, float)):
                        diff = mp_val - lit_val
                        rel_diff = (diff / lit_val * 100) if lit_val != 0 else None
                    else:
                        diff = None
                        rel_diff = None
                    
                    comparison["properties"][prop] = {
                        "literature": lit_val,
                        "mp_api": mp_val,
                        "difference": diff,
                        "relative_difference_percent": rel_diff
                    }
        
        return comparison


# ============================================================================
# MODULE FUNCTIONS
# ============================================================================

def create_interpolator_from_config(
    config: Dict,
    gaas_structure: Structure,
    alas_structure: Structure,
    logger = None
) -> StructureInterpolator:
    """
    Create StructureInterpolator from configuration dictionary.
    
    Args:
        config: Configuration dictionary
        gaas_structure: GaAs structure
        alas_structure: AlAs structure
        logger: Logger instance
    
    Returns:
        StructureInterpolator instance
    """
    interp_config = config.get("structure_interpolation", {})
    
    supercell_size = tuple(interp_config.get("supercell_size", [2, 2, 2]))
    data_source = config.get("interpolation", {}).get("mode", "literature")
    
    return StructureInterpolator(
        gaas_structure=gaas_structure,
        alas_structure=alas_structure,
        supercell_size=supercell_size,
        data_source=data_source,
        config=config,
        logger=logger
    )


# ============================================================================
# MODULE METADATA
# ============================================================================

__version__ = "0.1.1"
__author__ = "Abdullah Hasan Dafa"