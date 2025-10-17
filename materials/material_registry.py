"""
Material Registry - Central registry for managing materials and alloy systems

Provides a convenient interface for accessing material properties and 
managing multiple materials in a project.
"""

from typing import Dict, Optional, List, Any, Literal
from pathlib import Path
from .material_loader import MaterialLoader, Material, AlloySystem

DataSourceType = Literal["literature", "mp_api"]


class MaterialRegistry:
    """
    Central registry for managing materials and alloy systems.
    
    This class provides a high-level interface for working with materials,
    including caching, property lookup, and alloy calculations.
    """
    
    def __init__(self, properties_dir: Optional[Path] = None):
        """
        Initialize the material registry.
        
        Args:
            properties_dir: Path to properties directory (None = default location)
        """
        self.loader = MaterialLoader(properties_dir)
        self._materials: Dict[str, Material] = {}
        self._alloys: Dict[str, AlloySystem] = {}
    
    def register_material(self, material_name: str) -> Material:
        """
        Register and cache a material.
        
        Args:
            material_name: Name of the material to register
        
        Returns:
            Material object
        """
        if material_name not in self._materials:
            self._materials[material_name] = self.loader.load_material(material_name)
        return self._materials[material_name]
    
    def register_alloy(self, alloy_name: str) -> AlloySystem:
        """
        Register and cache an alloy system.
        
        Args:
            alloy_name: Name of the alloy system to register
        
        Returns:
            AlloySystem object
        """
        if alloy_name not in self._alloys:
            self._alloys[alloy_name] = self.loader.load_alloy_system(alloy_name)
        return self._alloys[alloy_name]
    
    def get_material(self, material_name: str) -> Material:
        """
        Get a material (registers if not already cached).
        
        Args:
            material_name: Name of the material
        
        Returns:
            Material object
        """
        return self.register_material(material_name)
    
    def get_alloy(self, alloy_name: str) -> AlloySystem:
        """
        Get an alloy system (registers if not already cached).
        
        Args:
            alloy_name: Name of the alloy system
        
        Returns:
            AlloySystem object
        """
        return self.register_alloy(alloy_name)
    
    def get_property(self, material_name: str, property_name: str, 
                     source: DataSourceType = "literature") -> Any:
        """
        Get a property value for a material.
        
        Args:
            material_name: Name of the material
            property_name: Name of the property
            source: Data source ('literature' or 'mp_api')
        
        Returns:
            Property value
        """
        material = self.get_material(material_name)
        return material.get_property(property_name, source)
    
    def get_all_properties(self, material_name: str, 
                          source: DataSourceType = "literature") -> Dict[str, Any]:
        """
        Get all properties for a material.
        
        Args:
            material_name: Name of the material
            source: Data source ('literature' or 'mp_api')
        
        Returns:
            Dictionary of all properties
        """
        material = self.get_material(material_name)
        return material.get_all_properties(source)
    
    def get_tight_binding_params(self, material_name: str) -> Optional[Dict[str, Any]]:
        """
        Get tight-binding parameters for a material.
        
        Args:
            material_name: Name of the material
        
        Returns:
            Dictionary of tight-binding parameters or None
        """
        material = self.get_material(material_name)
        return material.get_tight_binding_params()
    
    def calculate_alloy_property(self, alloy_name: str, property_name: str, 
                                 x: float, source: DataSourceType = "literature",
                                 fallback_to_literature: bool = True) -> Any:
        """
        Calculate an alloy property using Vegard's Law with bowing.
        
        Args:
            alloy_name: Name of the alloy system
            property_name: Name of the property to calculate
            x: Composition variable (typically Al content)
            source: Data source for endpoint properties
            fallback_to_literature: Fallback to literature if MP data unavailable
        
        Returns:
            Calculated property value
        """
        alloy = self.get_alloy(alloy_name)
        
        # Get endpoint materials
        endpoints = alloy.binary_endpoints
        if len(endpoints) != 2:
            raise ValueError(f"Alloy {alloy_name} must have exactly 2 binary endpoints")
        
        material1_name = endpoints[0]['material']
        material2_name = endpoints[1]['material']
        
        # Special handling for band gap type
        if property_name == "band_gap_type":
            return alloy.determine_band_gap_type(x)
        
        # Get endpoint property values
        material1 = self.get_material(material1_name)
        material2 = self.get_material(material2_name)
        
        p1 = material1.get_property(property_name, source)
        p2 = material2.get_property(property_name, source)
        
        # Fallback to literature if needed
        if (p1 is None or p2 is None) and fallback_to_literature and source == "mp_api":
            p1 = material1.get_property(property_name, "literature")
            p2 = material2.get_property(property_name, "literature")
        
        if p1 is None or p2 is None:
            raise ValueError(f"Property '{property_name}' not available for {alloy_name}")
        
        # Handle string properties (no interpolation)
        if isinstance(p1, str) or isinstance(p2, str):
            return p1 if x < 0.5 else p2
        
        # Get bowing parameter
        bowing = alloy.get_bowing_parameter(property_name)
        
        # Vegard's Law with bowing: P(x) = (1-x)P₁ + xP₂ - bx(1-x)
        value = (1 - x) * p1 + x * p2 - bowing * x * (1 - x)
        
        return value
    
    def calculate_alloy_properties(self, alloy_name: str, x: float,
                                   property_list: Optional[List[str]] = None,
                                   source: DataSourceType = "literature") -> Dict[str, Any]:
        """
        Calculate multiple properties for an alloy composition.
        
        Args:
            alloy_name: Name of the alloy system
            x: Composition variable
            property_list: List of properties to calculate (None = common properties)
            source: Data source for endpoint properties
        
        Returns:
            Dictionary of calculated properties
        """
        if property_list is None:
            # Default important properties
            property_list = [
                "lattice_constant", "band_gap", "band_gap_type",
                "effective_mass_electron", "effective_mass_hole_heavy",
                "dielectric_constant_static", "electron_mobility",
                "thermal_conductivity", "bulk_modulus"
            ]
        
        results = {}
        for prop in property_list:
            try:
                value = self.calculate_alloy_property(alloy_name, prop, x, source)
                results[prop] = value
            except Exception as e:
                results[prop] = None
        
        return results
    
    def list_materials(self) -> List[str]:
        """List all available materials"""
        return self.loader.list_available_materials()
    
    def list_alloys(self) -> List[str]:
        """List all available alloy systems"""
        return self.loader.list_available_alloys()
    
    def clear_cache(self):
        """Clear all cached materials and alloys"""
        self._materials.clear()
        self._alloys.clear()
        self.loader.clear_cache()


# Global registry instance
_global_registry: Optional[MaterialRegistry] = None


def get_global_registry() -> MaterialRegistry:
    """
    Get the global material registry instance.
    
    Returns:
        Global MaterialRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = MaterialRegistry()
    return _global_registry


def reset_global_registry():
    """Reset the global registry (useful for testing)"""
    global _global_registry
    _global_registry = None