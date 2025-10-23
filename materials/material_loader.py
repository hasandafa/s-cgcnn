"""
Material Loader - Load and manage material properties from YAML files

This module provides classes and functions to dynamically load material properties
from YAML configuration files in the materials/properties directory.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass

DataSourceType = Literal["literature", "mp_api"]


@dataclass
class Material:
    """Represents a single material with all its properties"""
    name: str
    formula: str
    mp_id: Optional[str] = None
    structure_type: Optional[str] = None
    space_group: Optional[str] = None
    crystal_structure: Optional[Dict[str, Any]] = None
    literature_props: Optional[Dict[str, Any]] = None
    mp_api_props: Optional[Dict[str, Any]] = None
    tight_binding_params: Optional[Dict[str, Any]] = None
    units: Optional[Dict[str, str]] = None
    
    def get_property(self, property_name: str, source: DataSourceType = "literature") -> Any:
        """
        Get a specific property value from the material.
        
        Args:
            property_name: Name of the property (e.g., 'band_gap', 'lattice_constant')
            source: Data source ('literature' or 'mp_api')
        
        Returns:
            Property value or None if not found
        """
        props = self.literature_props if source == "literature" else self.mp_api_props
        
        if props is None:
            return None
        
        # Search in nested dictionaries (physical, electronic, optical, etc.)
        for category in ['physical', 'electronic', 'optical', 'mechanical', 'thermal', 'transport']:
            if category in props and property_name in props[category]:
                return props[category][property_name]
        
        return None
    
    def get_all_properties(self, source: DataSourceType = "literature") -> Dict[str, Any]:
        """
        Get all properties from the material as a flat dictionary.
        
        Args:
            source: Data source ('literature' or 'mp_api')
        
        Returns:
            Dictionary of all properties
        """
        props = self.literature_props if source == "literature" else self.mp_api_props
        
        if props is None:
            return {}
        
        # Flatten nested structure
        flat_props = {}
        for category in ['physical', 'electronic', 'optical', 'mechanical', 'thermal', 'transport']:
            if category in props and isinstance(props[category], dict):
                flat_props.update(props[category])
        
        return flat_props
    
    def get_tight_binding_params(self) -> Optional[Dict[str, Any]]:
        """Get tight-binding parameters if available"""
        if self.tight_binding_params and 'parameters' in self.tight_binding_params:
            return self.tight_binding_params['parameters']
        return None


@dataclass
class AlloySystem:
    """Represents an alloy system with bowing parameters"""
    name: str
    formula: str
    binary_endpoints: List[Dict[str, Any]]
    bowing_parameters: Dict[str, float]
    band_gap_transition: Optional[Dict[str, Any]] = None
    composition_rules: Optional[Dict[str, Any]] = None
    applications: Optional[Dict[str, Any]] = None
    
    def get_bowing_parameter(self, property_name: str) -> float:
        """
        Get bowing parameter for a specific property.
        
        Args:
            property_name: Name of the property
        
        Returns:
            Bowing parameter value (0.0 if not defined)
        """
        return self.bowing_parameters.get(property_name, 0.0)
    
    def get_crossover_composition(self) -> float:
        """Get the composition where band gap transitions from direct to indirect"""
        if self.band_gap_transition:
            return self.band_gap_transition.get('crossover_composition', 0.45)
        return 0.45
    
    def determine_band_gap_type(self, x: float) -> str:
        """
        Determine if band gap is direct or indirect at composition x.
        
        Args:
            x: Composition value
        
        Returns:
            'direct' or 'indirect'
        """
        crossover = self.get_crossover_composition()
        return "direct" if x < crossover else "indirect"


class MaterialLoader:
    """
    Loads and manages material properties from YAML files.
    
    This class provides methods to load material properties and alloy systems
    from YAML configuration files stored in the materials/properties directory.
    """
    
    def __init__(self, properties_dir: Optional[Path] = None):
        """
        Initialize the material loader.
        
        Args:
            properties_dir: Path to the properties directory. If None, uses default location.
        """
        if properties_dir is None:
            # Default to materials/properties relative to this file
            self.properties_dir = Path(__file__).parent / "properties"
        else:
            self.properties_dir = Path(properties_dir)
        
        if not self.properties_dir.exists():
            raise FileNotFoundError(f"Properties directory not found: {self.properties_dir}")
        
        self._cache: Dict[str, Any] = {}
    
    def load_material(self, material_name: str) -> Material:
        """
        Load a material from its YAML file.
        
        Args:
            material_name: Name of the material (e.g., 'GaAs', 'AlAs')
        
        Returns:
            Material object with all properties
        
        Raises:
            FileNotFoundError: If material file doesn't exist
        """
        # Check cache first
        cache_key = f"material_{material_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Load from file
        material_file = self.properties_dir / f"{material_name}.yaml"
        
        if not material_file.exists():
            raise FileNotFoundError(f"Material file not found: {material_file}")
        
        with open(material_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Parse material data
        material_info = data.get('material', {})
        material = Material(
            name=material_info.get('name', material_name),
            formula=material_info.get('formula', material_name),
            mp_id=material_info.get('mp_id'),
            structure_type=material_info.get('structure_type'),
            space_group=material_info.get('space_group'),
            crystal_structure=data.get('crystal_structure'),
            literature_props=data.get('literature'),
            mp_api_props=data.get('mp_api'),
            tight_binding_params=data.get('tight_binding'),
            units=data.get('units')
        )
        
        # Cache and return
        self._cache[cache_key] = material
        return material
    
    def load_alloy_system(self, alloy_name: str) -> AlloySystem:
        """
        Load an alloy system from its YAML file.
        
        Args:
            alloy_name: Name of the alloy system (e.g., 'AlGaAs')
        
        Returns:
            AlloySystem object with bowing parameters and composition rules
        
        Raises:
            FileNotFoundError: If alloy file doesn't exist
        """
        # Check cache first
        cache_key = f"alloy_{alloy_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Load from file
        alloy_file = self.properties_dir / f"{alloy_name}.yaml"
        
        if not alloy_file.exists():
            raise FileNotFoundError(f"Alloy file not found: {alloy_file}")
        
        with open(alloy_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Parse alloy data
        alloy_info = data.get('alloy_system', {})
        alloy = AlloySystem(
            name=alloy_info.get('name', alloy_name),
            formula=alloy_info.get('formula', alloy_name),
            binary_endpoints=alloy_info.get('binary_endpoints', []),
            bowing_parameters=data.get('bowing_parameters', {}),
            band_gap_transition=data.get('band_gap_transition'),
            composition_rules=data.get('composition_rules'),
            applications=data.get('applications')
        )
        
        # Cache and return
        self._cache[cache_key] = alloy
        return alloy
    
    def list_available_materials(self) -> List[str]:
        """
        List all available materials in the properties directory.
        
        Returns:
            List of material names
        """
        materials = []
        for file in self.properties_dir.glob("*.yaml"):
            # Skip alloy systems (they typically have different structure)
            with open(file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if 'material' in data:
                    materials.append(file.stem)
        return sorted(materials)
    
    def list_available_alloys(self) -> List[str]:
        """
        List all available alloy systems in the properties directory.
        
        Returns:
            List of alloy system names
        """
        alloys = []
        for file in self.properties_dir.glob("*.yaml"):
            with open(file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if 'alloy_system' in data:
                    alloys.append(file.stem)
        return sorted(alloys)
    
    def clear_cache(self):
        """Clear the internal cache"""
        self._cache.clear()


# Convenience functions
def load_material(material_name: str, properties_dir: Optional[Path] = None) -> Material:
    """
    Convenience function to load a material.
    
    Args:
        material_name: Name of the material
        properties_dir: Optional custom properties directory
    
    Returns:
        Material object
    """
    loader = MaterialLoader(properties_dir)
    return loader.load_material(material_name)


def load_alloy_system(alloy_name: str, properties_dir: Optional[Path] = None) -> AlloySystem:
    """
    Convenience function to load an alloy system.
    
    Args:
        alloy_name: Name of the alloy system
        properties_dir: Optional custom properties directory
    
    Returns:
        AlloySystem object
    """
    loader = MaterialLoader(properties_dir)
    return loader.load_alloy_system(alloy_name)