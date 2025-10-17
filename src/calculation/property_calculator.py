"""
Property Calculator Module - Material-Agnostic Version

This module provides functions to calculate alloy properties using Vegard's Law
with bowing parameters, supporting both literature and MP-API data sources.
Includes electronic structure calculations using tight-binding method.

NOW FULLY MATERIAL-AGNOSTIC!

Author: Abdullah Hasan Dafa && Razasyattar M. N.
"""

from typing import Dict, List, Any, Optional, Literal
from .constants import get_material_registry
from ..utils import get_logger

logger = get_logger(__name__)

# Import electronic structure calculator
try:
    from .electronic_structure import TightBindingAlloy
    ELECTRONIC_STRUCTURE_AVAILABLE = True
except ImportError:
    ELECTRONIC_STRUCTURE_AVAILABLE = False
    logger.warning("Electronic structure calculator not available")

DataSourceType = Literal["literature", "mp_api"]


class PropertyCalculator:
    """
    Calculates alloy properties using Vegard's Law with bowing corrections.
    
    NOW FULLY MATERIAL-AGNOSTIC!
    Works with any alloy system defined in the materials registry.

    Supports both literature (experimental) and MP-API (DFT) data sources.
    Enhanced with tight-binding electronic structure calculations.
    """

    def __init__(self, 
                 alloy_name: str = "AlGaAs",
                 data_source: DataSourceType = "literature",
                 use_tb_electronic_structure: bool = True):
        """
        Initialize property calculator for any alloy system.

        Args:
            alloy_name: Name of alloy system (e.g., 'AlGaAs', 'InGaAs')
            data_source: "literature" for experimental values, "mp_api" for DFT
            use_tb_electronic_structure: Use tight-binding for electronic properties
        """
        self.alloy_name = alloy_name
        self.data_source = data_source
        self.use_tb_electronic_structure = use_tb_electronic_structure and ELECTRONIC_STRUCTURE_AVAILABLE
        
        # Load alloy system from registry
        self.registry = get_material_registry()
        self.alloy = self.registry.get_alloy(alloy_name)
        
        # Get binary endpoint materials
        endpoints = self.alloy.binary_endpoints
        if len(endpoints) != 2:
            raise ValueError(f"Alloy {alloy_name} must have exactly 2 binary endpoints")
        
        self.material1_name = endpoints[0]['material']
        self.material2_name = endpoints[1]['material']
        
        # Load endpoint properties
        self.props1 = self.registry.get_all_properties(self.material1_name, data_source)
        self.props2 = self.registry.get_all_properties(self.material2_name, data_source)

        if self.use_tb_electronic_structure:
            logger.info(f"Electronic structure calculator enabled for {alloy_name} (Tight-Binding)")
        
        logger.info(f"PropertyCalculator initialized for {alloy_name}")
        logger.info(f"  Materials: {self.material1_name} (x=0) ↔ {self.material2_name} (x=1)")

    def calculate_property(
        self,
        property_name: str,
        x: float,
        fallback_to_literature: bool = True
    ) -> Any:
        """
        Calculate a single property for composition x.

        Args:
            property_name: Name of the property to calculate
            x: Composition variable (0.0 to 1.0)
            fallback_to_literature: Use literature values if MP-API data unavailable

        Returns:
            Calculated property value
        """
        # Use the material registry for calculation
        return self.registry.calculate_alloy_property(
            self.alloy_name, 
            property_name, 
            x, 
            self.data_source,
            fallback_to_literature
        )

    def _calculate_tb_property(self, property_name: str, x: float) -> Any:
        """
        Calculate electronic properties using tight-binding method.

        Args:
            property_name: Electronic property name
            x: Composition variable

        Returns:
            Calculated property value
        """
        if not self.use_tb_electronic_structure:
            raise RuntimeError("Tight-binding calculator not available")

        # Use the generic tight-binding alloy class
        tb = TightBindingAlloy(self.alloy_name, x, self.registry)

        if property_name == "band_gap":
            bs = tb.calculate_band_structure()
            return bs.band_gap
        elif property_name.startswith("effective_mass_"):
            masses = tb.calculate_effective_masses()
            mass_type = property_name.replace("effective_mass_", "").replace("_", "_")
            return getattr(masses, mass_type)
        else:
            raise ValueError(f"Unknown TB property: {property_name}")

    def calculate_multiple_properties(
        self,
        property_names: List[str],
        x: float,
        fallback_to_literature: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate multiple properties for a single composition.

        Args:
            property_names: List of property names to calculate
            x: Composition variable (0.0 to 1.0)
            fallback_to_literature: Use literature values if MP-API data unavailable

        Returns:
            Dictionary mapping property names to calculated values
        """
        results = {}
        for prop_name in property_names:
            try:
                value = self.calculate_property(prop_name, x, fallback_to_literature)
                results[prop_name] = value
            except Exception as e:
                logger.error(f"Error calculating '{prop_name}' for {self.alloy_name}: {e}")
                results[prop_name] = None

        return results

    def calculate_property_range(
        self,
        property_name: str,
        x_values: List[float],
        fallback_to_literature: bool = True
    ) -> Dict[float, Any]:
        """
        Calculate a property for multiple compositions.

        Args:
            property_name: Name of the property to calculate
            x_values: List of compositions (0.0 to 1.0)
            fallback_to_literature: Use literature values if MP-API data unavailable

        Returns:
            Dictionary mapping x values to calculated property values
        """
        results = {}
        for x in x_values:
            try:
                value = self.calculate_property(property_name, x, fallback_to_literature)
                results[x] = value
            except Exception as e:
                logger.error(f"Error calculating '{property_name}' for {self.alloy_name} x={x}: {e}")
                results[x] = None

        return results


# ============================================================================
# CONVENIENCE FUNCTIONS (Backwards Compatible)
# ============================================================================

def calculate_band_gap(x: float, 
                       data_source: DataSourceType = "literature",
                       alloy_name: str = "AlGaAs") -> float:
    """
    Calculate band gap for any alloy composition.

    Args:
        x: Composition variable (0.0 to 1.0)
        data_source: "literature" or "mp_api"
        alloy_name: Name of alloy system (default: 'AlGaAs' for compatibility)

    Returns:
        Band gap in eV
    """
    calc = PropertyCalculator(alloy_name, data_source)
    return calc.calculate_property("band_gap", x)


def calculate_lattice_constant(x: float, 
                               data_source: DataSourceType = "literature",
                               alloy_name: str = "AlGaAs") -> float:
    """
    Calculate lattice constant for any alloy composition.

    Args:
        x: Composition variable (0.0 to 1.0)
        data_source: "literature" or "mp_api"
        alloy_name: Name of alloy system (default: 'AlGaAs' for compatibility)

    Returns:
        Lattice constant in Angstrom
    """
    calc = PropertyCalculator(alloy_name, data_source)
    return calc.calculate_property("lattice_constant", x)


def calculate_electron_mobility(x: float, 
                                data_source: DataSourceType = "literature",
                                alloy_name: str = "AlGaAs") -> float:
    """
    Calculate electron mobility for any alloy composition.

    Args:
        x: Composition variable (0.0 to 1.0)
        data_source: "literature" or "mp_api"
        alloy_name: Name of alloy system (default: 'AlGaAs' for compatibility)

    Returns:
        Electron mobility in cm²/(V·s)
    """
    calc = PropertyCalculator(alloy_name, data_source)
    return calc.calculate_property("electron_mobility", x)


def get_band_gap_type(x: float, alloy_name: str = "AlGaAs") -> str:
    """
    Get band gap type (direct/indirect) for any alloy composition.

    Args:
        x: Composition variable (0.0 to 1.0)
        alloy_name: Name of alloy system (default: 'AlGaAs' for compatibility)

    Returns:
        "direct" or "indirect"
    """
    registry = get_material_registry()
    alloy = registry.get_alloy(alloy_name)
    return alloy.determine_band_gap_type(x)


# ============================================================================
# BATCH CALCULATION FUNCTIONS
# ============================================================================

def calculate_all_properties(
    x: float,
    data_source: DataSourceType = "literature",
    property_list: Optional[List[str]] = None,
    use_tb_electronic_structure: bool = True,
    alloy_name: str = "AlGaAs"
) -> Dict[str, Any]:
    """
    Calculate all available properties for a composition.

    Args:
        x: Composition variable (0.0 to 1.0)
        data_source: "literature" or "mp_api"
        property_list: List of properties to calculate (None = all available)
        use_tb_electronic_structure: Use tight-binding for electronic properties
        alloy_name: Name of alloy system (default: 'AlGaAs')

    Returns:
        Dictionary of all calculated properties
    """
    if property_list is None:
        # Default important properties
        property_list = [
            "lattice_constant", "band_gap", "band_gap_type",
            "effective_mass_electron", "effective_mass_hole_heavy",
            "dielectric_constant_static", "electron_mobility",
            "thermal_conductivity", "bulk_modulus"
        ]

    calc = PropertyCalculator(alloy_name, data_source, use_tb_electronic_structure)
    return calc.calculate_multiple_properties(property_list, x)


def calculate_composition_series(
    x_values: List[float],
    properties: List[str],
    data_source: DataSourceType = "literature",
    alloy_name: str = "AlGaAs"
) -> Dict[str, Dict[float, Any]]:
    """
    Calculate properties for a series of compositions.

    Args:
        x_values: List of compositions (0.0 to 1.0)
        properties: List of property names to calculate
        data_source: "literature" or "mp_api"
        alloy_name: Name of alloy system (default: 'AlGaAs' for compatibility)

    Returns:
        Dictionary mapping property names to {x: value} dictionaries
    """
    calc = PropertyCalculator(alloy_name, data_source)
    results = {}

    for prop in properties:
        results[prop] = calc.calculate_property_range(prop, x_values)

    return results


# ============================================================================
# MODULE METADATA
# ============================================================================

__version__ = "1.0.0"
__author__ = "Abdullah Hasan Dafa"