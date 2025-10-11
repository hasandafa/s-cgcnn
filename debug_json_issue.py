"""
Debug script to find JSON serialization issues
"""

import sys
import json
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_acquisition import StructureInterpolator
from src.utils import setup_logger
from pymatgen.core import Structure, Lattice
import yaml

def find_non_serializable(obj, path="root"):
    """Recursively find non-JSON-serializable objects"""
    import numpy as np
    
    issues = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            issues.extend(find_non_serializable(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            issues.extend(find_non_serializable(item, f"{path}[{i}]"))
    else:
        # Try to serialize
        try:
            json.dumps(obj)
        except TypeError as e:
            issues.append({
                "path": path,
                "type": type(obj).__name__,
                "module": type(obj).__module__,
                "value": str(obj)[:100],
                "error": str(e)
            })
    
    return issues

def test_single_composition():
    """Test generating a single composition to find the issue"""
    
    print("=" * 80)
    print("DEBUG: JSON Serialization Issue")
    print("=" * 80)
    print()
    
    # Load config
    with open("config/config_v0.1.1.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    # Create mock structures
    lattice_gaas = Lattice.cubic(5.6533)
    gaas_structure = Structure(
        lattice_gaas,
        ["Ga", "As"],
        [[0, 0, 0], [0.25, 0.25, 0.25]]
    )
    
    lattice_alas = Lattice.cubic(5.6611)
    alas_structure = Structure(
        lattice_alas,
        ["Al", "As"],
        [[0, 0, 0], [0.25, 0.25, 0.25]]
    )
    
    # Create interpolator
    logger = setup_logger("Debug")
    interpolator = StructureInterpolator(
        gaas_structure=gaas_structure,
        alas_structure=alas_structure,
        data_source="literature",
        config=config,
        logger=logger
    )
    
    # Generate single structure
    print("Generating structure for x=0.0...")
    structure, composition = interpolator.generate_alloy_structure(x=0.0)
    print(f"✓ Structure generated: {composition.formula}")
    print()
    
    # Calculate properties
    print("Calculating properties...")
    properties = interpolator.calculate_properties(x=0.0)
    print(f"✓ Properties calculated: {len(properties)} properties")
    print()
    
    # Create metadata
    print("Creating metadata...")
    from dataclasses import asdict
    
    metadata = {
        "version": "0.1.1",
        "data_source": "literature",
        "composition": asdict(composition),
        "structure_info": {
            "formula": structure.composition.reduced_formula,
            "num_sites": len(structure),
            "lattice_abc": structure.lattice.abc,
            "lattice_angles": structure.lattice.angles,
            "volume": structure.lattice.volume,
            "density": structure.density,
        },
    }
    
    # Combine all data
    all_data = {
        "composition": asdict(composition),
        "data_source": "literature",
        "properties": properties,
        "metadata": metadata,
    }
    
    print("Checking for non-serializable objects...")
    print()
    
    # Find issues
    issues = find_non_serializable(all_data)
    
    if issues:
        print("=" * 80)
        print(f"FOUND {len(issues)} NON-SERIALIZABLE OBJECTS:")
        print("=" * 80)
        print()
        
        for i, issue in enumerate(issues, 1):
            print(f"{i}. PATH: {issue['path']}")
            print(f"   TYPE: {issue['type']} (from {issue['module']})")
            print(f"   VALUE: {issue['value']}")
            print(f"   ERROR: {issue['error']}")
            print()
        
        # Show the problematic objects
        print("=" * 80)
        print("DETAILED INSPECTION:")
        print("=" * 80)
        print()
        
        for issue in issues[:3]:  # Show first 3 issues
            print(f"Path: {issue['path']}")
            
            # Try to get the actual object
            parts = issue['path'].replace('root.', '').split('.')
            obj = all_data
            for part in parts:
                if '[' in part:
                    key = part.split('[')[0]
                    idx = int(part.split('[')[1].rstrip(']'))
                    obj = obj[key][idx]
                else:
                    obj = obj[part]
            
            print(f"Type: {type(obj)}")
            print(f"Value: {obj}")
            print(f"Is numpy bool? {type(obj).__name__ == 'bool_'}")
            
            # Check module
            import numpy as np
            print(f"isinstance np.bool_? {isinstance(obj, np.bool_)}")
            print(f"isinstance np.integer? {isinstance(obj, np.integer)}")
            print()
        
        return False
    else:
        print("✓ All objects are JSON-serializable!")
        
        # Try actual JSON dump
        try:
            json.dumps(all_data, indent=2)
            print("✓ JSON serialization successful!")
            return True
        except Exception as e:
            print(f"✗ JSON serialization failed: {e}")
            return False

if __name__ == "__main__":
    success = test_single_composition()
    sys.exit(0 if success else 1)