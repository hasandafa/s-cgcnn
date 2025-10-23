"""
Property Calculator Module - Material-Agnostic Version

This module provides functions to calculate alloy properties using Vegard's Law
with bowing parameters, supporting both literature and MP-API data sources.
Includes electronic structure calculations using tight-binding method.

NOW FULLY MATERIAL-AGNOSTIC!

Author: Abdullah Hasan Dafa && Razasyattar M. N.
"""

from typing import Dict, List, Any, Literal
from .constants import get_material_registry
from ..utils import get_logger

logger = get_logger(__name__)

# Import electronic structure calculator
try:
    from .electronic_structure import AlloyTightBinding
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
        logger.info(f"  Materials: {self.material1_name} (x=0) <-> {self.material2_name} (x=1)")

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
        tb_properties = [
            "band_gap", "effective_mass_electron", 
            "effective_mass_hole_heavy", "effective_mass_hole_light"
        ]

        if self.use_tb_electronic_structure and property_name in tb_properties:
            try:
                # If it's an electronic property, use the advanced TB calculator
                return self._calculate_tb_property(property_name, x)
            except Exception as e:
                logger.warning(f"TB calculation failed for {property_name} at x={x}: {e}")
                # Fallback to simple interpolation if TB fails
        
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
        tb = AlloyTightBinding(self.alloy_name, x, self.registry)

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


# Main calculator class is sufficient - removed redundant convenience functions


# Batch calculation functions removed - use PropertyCalculator class directly


# ============================================================================
# MODULE METADATA
# ============================================================================

__version__ = "1.0.0"
__author__ = "Abdullah Hasan Dafa"