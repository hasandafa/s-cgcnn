"""
Structure Interpolation Module - Version 2.0.0 (Material-Agnostic + Enhanced)
Enhanced with charge density interpolation, structure relaxation, and advanced scipy methods.

Generates binary alloy structures with configurable property sources,
charge density interpolation, ML-based relaxation, and scipy-based interpolation.

Now fully material-agnostic - works with any binary alloy system!

Author: Abdullah Hasan Dafa && Razasyattar M. N.
"""

import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import json
from dataclasses import dataclass, asdict

from scipy.interpolate import CubicSpline, UnivariateSpline

from pymatgen.core import Structure, Lattice, Element
from pymatgen.io.cif import CifWriter

from .constants import get_material_registry, DataSourceType
from ..utils import get_logger

logger = get_logger(__name__)

# Import advanced modules
try:
    from .charge_density_interpolator import ChargeDensityInterpolator
    CHARGE_DENSITY_AVAILABLE = True
except ImportError:
    CHARGE_DENSITY_AVAILABLE = False
    logger.info("Charge density interpolation not available")

try:
    from .structure_relaxer import StructureRelaxer
    STRUCTURE_RELAXER_AVAILABLE = True
except ImportError:
    STRUCTURE_RELAXER_AVAILABLE = False
    logger.info("Structure relaxation not available")


# ============================================================================
# DATA CLASSES
# ============================================================================
@dataclass
class AlloyComposition:
    """Represents a specific alloy composition"""
    x: float  # Composition variable (0.0 to 1.0)
    formula: str  # e.g., "Al0.250Ga0.750As"
    num_element1: int  # Number of element1 atoms (high x end)
    num_element2: int  # Number of element2 atoms (low x end)
    element1_name: str  # Name of substituting element
    element2_name: str  # Name of base element
    is_discrete: bool  # True if exact discrete value, False if rounded


@dataclass
class AlloyProperties:
    """Complete property set for an alloy composition"""
    composition: AlloyComposition
    data_source: DataSourceType
    properties: Dict[str, Any]
    metadata: Dict[str, Any]
    charge_density: Optional[Any] = None
    relaxed_structure: Optional[Structure] = None
    per_atom_charge_density: Optional[np.ndarray] = None


# ============================================================================
# STRUCTURE INTERPOLATOR CLASS (Material-Agnostic)
# ============================================================================
class StructureInterpolator:
    """
    Interpolates structures and properties for binary alloys.
    
    NOW FULLY MATERIAL-AGNOSTIC!
    Works with any binary alloy system (AlGaAs, InGaAs, GaN-AlN, etc.)

    Features:
    - Dual data source support (literature/mp_api)
    - Vegard's Law with bowing parameters
    - Automatic element detection and substitution
    - Flexible property calculation
    """

    def __init__(
        self,
        structure1: Structure,  # Low x endpoint (x=0)
        structure2: Structure,  # High x endpoint (x=1)
        material1_name: str,    # e.g., "GaAs"
        material2_name: str,    # e.g., "AlAs"
        alloy_name: str,        # e.g., "AlGaAs"
        supercell_size: Tuple[int, int, int] = (2, 2, 2),
        data_source: DataSourceType = "literature",
        config: Optional[Dict] = None,
        enable_charge_density: Optional[bool] = None,
        enable_relaxation: Optional[bool] = None
    ):
        """
        Initialize the structure interpolator for any binary alloy.

        Args:
            structure1: First material structure (x=0 endpoint)
            structure2: Second material structure (x=1 endpoint)
            material1_name: Name of first material (e.g., "GaAs")
            material2_name: Name of second material (e.g., "AlAs")
            alloy_name: Name of alloy system (e.g., "AlGaAs")
            supercell_size: Size of supercell for substitution
            data_source: "literature" or "mp_api"
            config: Configuration dictionary
            enable_charge_density: Enable charge density interpolation
            enable_relaxation: Enable structure relaxation
        """
        self.structure1 = structure1
        self.structure2 = structure2
        self.material1_name = material1_name
        self.material2_name = material2_name
        self.alloy_name = alloy_name
        self.supercell_size = supercell_size
        self.data_source = data_source
        self.config = config or {}

        # Use config defaults if not explicitly set
        if enable_charge_density is None:
            enable_charge_density = config.get('features.enable_charge_density', True) if config else True
        if enable_relaxation is None:
            enable_relaxation = config.get('features.enable_relaxation', True) if config else True

        self.enable_charge_density = enable_charge_density and CHARGE_DENSITY_AVAILABLE
        self.enable_relaxation = enable_relaxation and STRUCTURE_RELAXER_AVAILABLE

        # Detect which element to substitute
        self._detect_substitution_elements()

        # Create supercells
        self.supercell1 = self._create_supercell(structure1)
        self.supercell2 = self._create_supercell(structure2)

        # Calculate total substitution sites
        self.total_sites = sum(1 for site in self.supercell1
                              if site.specie == Element(self.element_to_substitute))

        # Load properties from registry
        registry = get_material_registry()
        self.props1 = registry.get_all_properties(material1_name, data_source)
        self.props2 = registry.get_all_properties(material2_name, data_source)
        self.alloy_system = registry.get_alloy(alloy_name)

        # Initialize charge density interpolator if enabled
        self.charge_density_interpolator = None
        if self.enable_charge_density:
            try:
                from .charge_density_interpolator import ChargeDensityInterpolator
                data_dir = Path(self.config.get('paths.data_dir', 'data/'))
                
                # Use the new material-agnostic API
                self.charge_density_interpolator = ChargeDensityInterpolator.from_material_pair(
                    material1_name, material2_name, data_dir
                )
                logger.info(f"Charge density interpolator initialized for {material1_name}/{material2_name}")
            except FileNotFoundError as e:
                logger.warning(f"CHGCAR files not found: {e}")
                self.enable_charge_density = False
            except Exception as e:
                logger.warning(f"Failed to initialize charge density interpolator: {e}")
                self.enable_charge_density = False

        # Initialize structure relaxer if enabled
        self.structure_relaxer = None
        if self.enable_relaxation:
            try:
                self.structure_relaxer = StructureRelaxer()
                logger.info("Structure relaxer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize structure relaxer: {e}")

        logger.info(f"Initialized StructureInterpolator (v1.0.0 - Material-Agnostic)")
        logger.info(f"Alloy system: {alloy_name}")
        logger.info(f"Materials: {material1_name} (x=0) <-> {material2_name} (x=1)")
        logger.info(f"Substitution: {self.element_to_substitute} -> {self.substituting_element}")
        logger.info(f"Data source: {data_source}")
        logger.info(f"Supercell: {supercell_size} ({self.total_sites} substitution sites)")

    def _detect_substitution_elements(self):
        """
        Automatically detect which elements to substitute.
        Finds the differing cation between the two materials.
        """
        # Get unique elements from each structure
        elements1 = set(site.specie.symbol for site in self.structure1)
        elements2 = set(site.specie.symbol for site in self.structure2)
        
        # Find elements that differ
        diff_in_1 = elements1 - elements2
        diff_in_2 = elements2 - elements1
        
        if len(diff_in_1) != 1 or len(diff_in_2) != 1:
            raise ValueError(
                f"Cannot automatically detect substitution elements. "
                f"Structures should differ by exactly one element. "
                f"Found: {elements1} vs {elements2}"
            )
        
        # Element in structure1 is what we substitute FROM
        # Element in structure2 is what we substitute TO
        self.element_to_substitute = list(diff_in_1)[0]
        self.substituting_element = list(diff_in_2)[0]
        
        logger.info(f"Auto-detected substitution: {self.element_to_substitute} -> {self.substituting_element}")

    def _create_supercell(self, structure: Structure) -> Structure:
        """Create supercell from primitive structure"""
        supercell = structure.copy()
        supercell.make_supercell(self.supercell_size)
        return supercell

    def generate_alloy_structure(
        self,
        x: float,
        ordered: bool = False
    ) -> Tuple[Structure, AlloyComposition]:
        """
        Generate alloy structure for given composition.

        Args:
            x: Composition variable (0.0 to 1.0)
            ordered: If True, use ordered substitution; if False, random (default: random for natural disorder)

        Returns:
            Tuple of (symmetrized Structure, AlloyComposition)
        """
        # Calculate discrete number of substitutions
        num_element2 = round(x * self.total_sites)  # High x element
        num_element1 = self.total_sites - num_element2  # Low x element
        actual_x = num_element2 / self.total_sites

        is_discrete = abs(x - actual_x) < 1e-6

        if not is_discrete:
            logger.info(
                f"Composition x={x:.3f} rounded to x={actual_x:.3f} "
                f"({num_element2} {self.substituting_element}, "
                f"{num_element1} {self.element_to_substitute} atoms)"
            )

        # Create composition object
        composition = AlloyComposition(
            x=actual_x,
            formula=self._generate_formula(actual_x),
            num_element1=num_element1,
            num_element2=num_element2,
            element1_name=self.element_to_substitute,
            element2_name=self.substituting_element,
            is_discrete=is_discrete
        )

        # Start from structure1 supercell
        alloy_structure = self.supercell1.copy()

        # Find all sites to substitute
        substitution_indices = [
            i for i, site in enumerate(alloy_structure)
            if site.specie == Element(self.element_to_substitute)
        ]

        # Select sites for substitution
        if ordered:
            selected_indices = substitution_indices[:num_element2]
        else:
            rng = np.random.default_rng(seed=42)
            selected_indices = rng.choice(substitution_indices, size=num_element2, replace=False)

        # Perform substitution
        for idx in selected_indices:
            alloy_structure.replace(idx, Element(self.substituting_element))

        # Update lattice parameter (Vegard interpolation)
        lattice_param = self._interpolate_lattice_parameter(actual_x)
        supercell_factor = self.supercell_size[0]
        supercell_lattice_param = lattice_param * supercell_factor
        new_lattice = Lattice.cubic(supercell_lattice_param)
        alloy_structure.lattice = new_lattice

        # For alloys, we maintain the cubic lattice but don't force symmetrization
        # since random substitution creates disordered structures that should remain disordered
        # The cubic lattice ensures proper zinc blende geometry
        
        # Update formula with reduced formula from the cubic structure
        reduced_formula = alloy_structure.composition.reduced_formula
        composition.formula = reduced_formula

        logger.info(
            f"Generated structure: {composition.formula}, "
            f"a={lattice_param:.4f} Å (cubic, zinc blende)"
        )

        return alloy_structure, composition

    def _generate_formula(self, x: float) -> str:
        """Generate chemical formula for the alloy"""
        # Get common anion (element that's the same in both)
        elements1 = set(site.specie.symbol for site in self.structure1)
        elements2 = set(site.specie.symbol for site in self.structure2)
        common_elements = elements1 & elements2
        
        if common_elements:
            anion = list(common_elements)[0]
            return f"{self.substituting_element}{x:.3f}{self.element_to_substitute}{1-x:.3f}{anion}"
        else:
            return f"{self.substituting_element}{x:.3f}{self.element_to_substitute}{1-x:.3f}"

    def _interpolate_lattice_parameter(self, x: float, method: str = "vegard") -> float:
        """
        Interpolate lattice parameter using various methods.

        Args:
            x: Composition variable
            method: "vegard" (linear), "cubic", or "bowing"

        Returns:
            Lattice parameter in Angstrom
        """
        if self.data_source == "literature":
            a1 = self.props1.get("lattice_constant")
            a2 = self.props2.get("lattice_constant")
        else:
            a1 = self.structure1.lattice.a
            a2 = self.structure2.lattice.a

        if method == "vegard":
            # Simple Vegard's Law (linear)
            a_alloy = (1 - x) * a1 + x * a2
            
        elif method == "bowing":
            # Include bowing parameter from registry
            bowing = self.alloy_system.bowing_parameters.get("lattice_constant", 0.0)
            a_alloy = (1 - x) * a1 + x * a2 - bowing * x * (1 - x)
            
        elif method == "cubic":
            # Cubic spline interpolation through endpoints and midpoint
            x_points = np.array([0.0, 0.5, 1.0])
            # Calculate midpoint with small deviation
            a_mid = 0.5 * (a1 + a2)
            bowing = self.alloy_system.bowing_parameters.get("lattice_constant", 0.0)
            a_mid -= 0.25 * bowing  # Add bowing effect
            
            a_points = np.array([a1, a_mid, a2])
            cs = CubicSpline(x_points, a_points, bc_type='natural')
            a_alloy = float(cs(x))
            
        else:
            raise ValueError(f"Unknown interpolation method: {method}")
        
        return a_alloy
    
    def interpolate_property_with_scipy(
        self,
        property_name: str,
        x: float,
        method: str = "cubic"
    ) -> Any:
        """
        Interpolate any property using scipy methods.
        
        Args:
            property_name: Name of property to interpolate
            x: Composition variable
            method: "linear", "cubic", or "spline"
            
        Returns:
            Interpolated property value
        """
        # Get endpoint values
        val1 = self.props1.get(property_name)
        val2 = self.props2.get(property_name)
        
        if val1 is None or val2 is None:
            return None
        
        # Get bowing parameter
        bowing = self.alloy_system.bowing_parameters.get(property_name, 0.0)
        
        if method == "linear":
            return (1 - x) * val1 + x * val2 - bowing * x * (1 - x)
        
        elif method == "cubic":
            # Three-point cubic spline
            x_points = np.array([0.0, 0.5, 1.0])
            val_mid = 0.5 * (val1 + val2) - 0.25 * bowing
            y_points = np.array([val1, val_mid, val2])
            
            cs = CubicSpline(x_points, y_points, bc_type='natural')
            return float(cs(x))
        
        elif method == "spline":
            # Univariate spline with smoothing
            x_points = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
            y_points = np.array([
                val1,
                0.75 * val1 + 0.25 * val2 - 0.1875 * bowing,
                0.5 * val1 + 0.5 * val2 - 0.25 * bowing,
                0.25 * val1 + 0.75 * val2 - 0.1875 * bowing,
                val2
            ])
            
            spline = UnivariateSpline(x_points, y_points, s=0, k=3)
            return float(spline(x))
        
        else:
            raise ValueError(f"Unknown method: {method}")

    def calculate_properties(
        self,
        x: float,
        fallback_to_literature: bool = True
    ) -> Dict[str, Any]:
        """Calculate properties using the material registry"""
        registry = get_material_registry()
        
        # Get default properties
        property_list = [
            "lattice_constant", "band_gap", "band_gap_type",
            "dielectric_constant_static", "electron_mobility"
        ]
        
        properties = {}
        for prop_name in property_list:
            try:
                value = registry.calculate_alloy_property(
                    self.alloy_name, prop_name, x, self.data_source,
                    fallback_to_literature
                )
                properties[prop_name] = value
            except Exception as e:
                logger.warning(f"Error calculating '{prop_name}': {e}")
                properties[prop_name] = None
        
        return properties

    def generate_composition_range(
        self,
        x_min: float = 0.0,
        x_max: float = 1.0,
        x_step: float = 0.025,
        output_dir: Optional[Path] = None,
        save_cif: bool = True,
        save_metadata: bool = True
    ) -> List[AlloyProperties]:
        """Generate structures and properties for a range of compositions"""
        num_points = int(round((x_max - x_min) / x_step)) + 1
        x_values = np.linspace(x_min, x_max, num_points)
        x_values = np.round(x_values, 3)

        logger.info(
            f"Generating {len(x_values)} compositions for {self.alloy_name} "
            f"from x={x_min:.3f} to x={x_max:.3f} (step={x_step})"
        )

        if output_dir:
            output_dir = Path(output_dir)
            cif_dir = output_dir / "cif"
            metadata_dir = output_dir / "metadata"

            if save_cif:
                cif_dir.mkdir(parents=True, exist_ok=True)
            if save_metadata:
                metadata_dir.mkdir(parents=True, exist_ok=True)

        alloy_list = []

        for i, x in enumerate(x_values, 1):
            logger.info(f"Processing composition {i}/{len(x_values)}: x={x:.3f}")

            structure, composition = self.generate_alloy_structure(x)
            properties = self.calculate_properties(composition.x)
            metadata = self._create_metadata(composition, structure, properties)

            # Charge density interpolation
            charge_density = None
            per_atom_charge_density = None
            if self.enable_charge_density and self.charge_density_interpolator:
                try:
                    charge_density = self.charge_density_interpolator.interpolate(
                        composition.x, structure
                    )
                    # Extract per-atom charge density values for GNN features
                    per_atom_charge_density = self.charge_density_interpolator.get_per_atom_charge_density(
                        composition.x, structure
                    )
                    logger.info(f"Interpolated charge density for x={composition.x:.3f}")
                except Exception as e:
                    logger.warning(f"Charge density interpolation failed: {e}")

            # Structure relaxation
            relaxed_structure = None
            if self.enable_relaxation and self.structure_relaxer:
                try:
                    relaxed_result = self.structure_relaxer.relax(structure)
                    relaxed_structure = relaxed_result.final_structure
                    logger.info(f"Relaxed structure for x={composition.x:.3f}")
                except Exception as e:
                    logger.warning(f"Structure relaxation failed: {e}")

            alloy = AlloyProperties(
                composition=composition,
                data_source=self.data_source,
                properties=properties,
                metadata=metadata,
                charge_density=charge_density,
                relaxed_structure=relaxed_structure,
                per_atom_charge_density=per_atom_charge_density
            )

            alloy_list.append(alloy)

            # Save files
            if output_dir:
                filename_base = f"{self.alloy_name}_x{composition.x:.3f}"

                if save_cif:
                    self._save_cif(structure, cif_dir / f"{filename_base}.cif")
                    if relaxed_structure is not None:
                        self._save_cif(relaxed_structure, cif_dir / f"{filename_base}_relaxed.cif")

                if save_metadata:
                    self._save_metadata(alloy, metadata_dir / f"{filename_base}.json")

        logger.info(f"Successfully generated {len(alloy_list)} structures")
        return alloy_list

    def _create_metadata(
        self,
        composition: AlloyComposition,
        structure: Structure,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create metadata dictionary"""
        # For disordered alloys, space group analysis may detect lower symmetry due to random disorder
        # We maintain cubic lattice but acknowledge the disordered nature
        space_group_info = "P 1 (disordered cubic, zinc blende)"
        space_group_number = 1  # Triclinic, but actually disordered cubic

        metadata = {
            "version": "1.0.0",
            "alloy_system": self.alloy_name,
            "data_source": self.data_source,
            "composition": asdict(composition),
            "structure_info": {
                "formula_theoretical": composition.formula,
                "formula_reduced": structure.composition.reduced_formula,
                "num_sites": len(structure),
                "lattice_abc": structure.lattice.abc,
                "lattice_angles": structure.lattice.angles,
                "volume": structure.lattice.volume,
                "density": structure.density,
                "space_group": space_group_info,
                "space_group_number": space_group_number,
            },
            "generation_method": "random_supercell_substitution",
            "supercell_size": list(self.supercell_size),
            "interpolation_method": "vegard_law_with_bowing",
        }

        return metadata

    def _save_cif(self, structure: Structure, filepath: Path):
        """Save structure as CIF file"""
        writer = CifWriter(structure)
        writer.write_file(str(filepath))
        logger.info(f"Saved CIF: {filepath.name}")

    def _save_metadata(self, alloy: AlloyProperties, filepath: Path):
        """Save complete metadata as JSON"""
        def convert_numpy(obj):
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

        logger.info(f"Saved metadata: {filepath.name}")


# ============================================================================
# MODULE FUNCTIONS
# ============================================================================

def create_interpolator_from_config(
    config: Dict,
    structure1: Structure,
    structure2: Structure,
    material1_name: str = "GaAs",
    material2_name: str = "AlAs",
    alloy_name: str = "AlGaAs"
) -> StructureInterpolator:
    """
    Create StructureInterpolator from configuration dictionary.
    
    NOW MATERIAL-AGNOSTIC!

    Args:
        config: Configuration dictionary
        structure1: First material structure
        structure2: Second material structure
        material1_name: Name of first material (default: 'GaAs')
        material2_name: Name of second material (default: 'AlAs')
        alloy_name: Name of alloy system (default: 'AlGaAs')

    Returns:
        StructureInterpolator instance
    """
    interp_config = config.get("structure_interpolation", {})

    supercell_size = tuple(interp_config.get("supercell_size", [2, 2, 2]))
    data_source = config.get("interpolation", {}).get("mode", "literature")

    return StructureInterpolator(
        structure1=structure1,
        structure2=structure2,
        material1_name=material1_name,
        material2_name=material2_name,
        alloy_name=alloy_name,
        supercell_size=supercell_size,
        data_source=data_source,
        config=config
    )