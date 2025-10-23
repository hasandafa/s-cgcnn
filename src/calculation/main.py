"""
Material-Agnostic Structure and Property Calculator

This module provides functionality for:
- Generating alloy structures through supercell interpolation (any binary alloy)
- Calculating material properties using Vegard's Law with bowing corrections
- Electronic structure calculations using tight-binding method
- Charge density interpolation in real space
- ML-based structure relaxation

The system supports any material or alloy system defined in materials/properties/

Usage:
    from src.calculation.main import run_full_pipeline

    results = run_full_pipeline(
        alloy_system="AlGaAs",
        material1="GaAs",
        material2="AlAs"
    )
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from pymatgen.core import Structure

from ..utils import get_config, get_logger
from .structure_interpolator import StructureInterpolator
from .property_calculator import PropertyCalculator

logger = get_logger(__name__)


def load_binary_structures(
    material1: str,
    material2: str,
    mp_id1: Optional[str] = None,
    mp_id2: Optional[str] = None
) -> tuple[Structure, Structure]:
    """
    Load and standardize to cubic primitive cells.

    This function is material-agnostic and can load any materials
    defined in the materials registry.

    Args:
        material1: First material name
        material2: Second material name
        mp_id1: Materials Project ID for material1 (auto-detected if None)
        mp_id2: Materials Project ID for material2 (auto-detected if None)

    Returns:
        Tuple of (material1_structure, material2_structure)
    """
    from .constants import get_material_registry
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

    config = get_config()
    data_dir = Path(config.get('paths.data_dir', 'data/'))

    # Get MP IDs from materials registry if not provided
    registry = get_material_registry()
    if mp_id1 is None:
        mat1 = registry.get_material(material1)
        mp_id1 = mat1.mp_id
    if mp_id2 is None:
        mat2 = registry.get_material(material2)
        mp_id2 = mat2.mp_id

    # Load first material structure
    mat1_file = data_dir / mp_id1 / "material_data.json"
    if not mat1_file.exists():
        raise FileNotFoundError(f"Material data not found: {mat1_file}")

    with open(mat1_file, 'r') as f:
        mat1_data = json.load(f)
    structure1 = Structure.from_dict(mat1_data['structure'])

    # Load second material structure
    mat2_file = data_dir / mp_id2 / "material_data.json"
    if not mat2_file.exists():
        raise FileNotFoundError(f"Material data not found: {mat2_file}")

    with open(mat2_file, 'r') as f:
        mat2_data = json.load(f)
    structure2 = Structure.from_dict(mat2_data['structure'])

    # Convert to primitive cubic cells
    sga1 = SpacegroupAnalyzer(structure1)
    structure1 = sga1.get_primitive_standard_structure()

    sga2 = SpacegroupAnalyzer(structure2)
    structure2 = sga2.get_primitive_standard_structure()

    # Verify they're cubic
    def is_cubic(lattice):
        return (abs(lattice.a - lattice.b) < 1e-6 and
                abs(lattice.b - lattice.c) < 1e-6 and
                all(abs(angle - 90.0) < 1e-6 for angle in lattice.angles))

    if not (is_cubic(structure1.lattice) and is_cubic(structure2.lattice)):
        logger.warning("Structures are not cubic! This may cause issues.")

    logger.info(f"Loaded and standardized structures for {material1} ({mp_id1}) and {material2} ({mp_id2})")

    return structure1, structure2


def generate_structures(
    alloy_system: str,
    material1: str,
    material2: str,
    output_dir: str = "data/outputs/calculations/structures",
    x_values: Optional[List[float]] = None,
    supercell_size: tuple[int, int, int] = (2, 2, 2),
    data_source: str = "literature",
    enable_charge_density: Optional[bool] = None,
    enable_relaxation: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    Generate alloy structures through supercell interpolation.
    Enhanced with charge density interpolation and structure relaxation.

    Supports any alloy system defined in materials/properties/.

    Args:
        alloy_system: Name of alloy system
        material1: First binary material
        material2: Second binary material
        output_dir: Directory to save interpolated structures
        x_values: List of compositions (default: config values)
        supercell_size: Size of supercell for substitution
        data_source: "literature" or "mp_api"
        enable_charge_density: Enable charge density interpolation
        enable_relaxation: Enable ML-based structure relaxation

    Returns:
        List of generated alloy data
    """
    logger.info(f"Generating {alloy_system} alloy structures with advanced features...")

    # Load config
    config = get_config()
    if x_values is None:
        x_values = config.get('system.compositions.x_values', [0.0, 0.25, 0.5, 0.75, 1.0])

    # Use config defaults if not explicitly set
    if enable_charge_density is None:
        enable_charge_density = config.get('features.enable_charge_density', True)
    if enable_relaxation is None:
        enable_relaxation = config.get('features.enable_relaxation', True)

    # Load binary structures
    logger.info(f"Loading binary structures for {material1} and {material2}...")
    structure1, structure2 = load_binary_structures(material1, material2)

    # Create interpolator with advanced features (material-agnostic)
    interpolator = StructureInterpolator(
        structure1=structure1,
        structure2=structure2,
        material1_name=material1,
        material2_name=material2,
        alloy_name=alloy_system,
        supercell_size=supercell_size,
        data_source=data_source,
        enable_charge_density=enable_charge_density,
        enable_relaxation=enable_relaxation
    )

    # Generate structures
    output_path = Path(output_dir)
    alloys = interpolator.generate_composition_range(
        x_min=min(x_values),
        x_max=max(x_values),
        x_step=x_values[1] - x_values[0] if len(x_values) > 1 else 0.1,
        output_dir=output_path,
        save_cif=True,
        save_metadata=True
    )

    logger.info(f"Generated {len(alloys)} alloy structures in {output_dir}")
    if enable_charge_density:
        logger.info("Charge density interpolation enabled")
    if enable_relaxation:
        logger.info("Structure relaxation enabled")

    return [alloy.__dict__ for alloy in alloys]


def calculate_properties(
    alloy_system: str,
    x_values: Optional[List[float]] = None,
    data_source: str = "literature",
    properties: Optional[List[str]] = None,
    output_file: str = "data/outputs/calculations/properties.json",
    use_tb_electronic_structure: bool = True
) -> Dict[str, Any]:
    """
    Calculate alloy properties using Vegard's Law with bowing corrections.
    Enhanced with tight-binding electronic structure calculations.

    Supports any alloy system defined in materials/properties/.

    Args:
        alloy_system: Name of alloy system
        x_values: List of compositions (default: config values)
        data_source: "literature" or "mp_api"
        properties: List of properties to calculate (default: all important ones)
        output_file: File to save calculated properties
        use_tb_electronic_structure: Use tight-binding for electronic properties

    Returns:
        Dictionary of calculated properties for all compositions
    """
    logger.info(f"Calculating {alloy_system} properties with advanced electronic structure...")

    # Load config
    config = get_config()
    if x_values is None:
        x_values = config.get('system.compositions.x_values', [0.0, 0.25, 0.5, 0.75, 1.0])

    if properties is None:
        # Complete list of all available properties from YAML files
        properties = [
            # Core electronic properties
            "lattice_constant",
            "band_gap",
            "band_gap_type",
            "electron_affinity",
            "effective_mass_electron",
            "effective_mass_hole_heavy",
            "effective_mass_hole_light",
            
            # Optical properties
            "dielectric_constant_static",
            "dielectric_constant_high_freq",
            "refractive_index",
            
            # Mechanical properties
            "bulk_modulus",
            "shear_modulus",
            "youngs_modulus",
            "poissons_ratio",
            "elastic_constant_c11",
            "elastic_constant_c12",
            "elastic_constant_c44",
            
            # Thermal properties
            "thermal_conductivity",
            
            # Transport properties
            "electron_mobility",
            "hole_mobility"
        ]

    # Calculate properties for all compositions (material-agnostic)
    calculator = PropertyCalculator(alloy_system, data_source, use_tb_electronic_structure)
    results = {
        "metadata": {
            "alloy_system": alloy_system,
            "data_source": data_source,
            "properties_calculated": properties,
            "compositions": x_values,
            "electronic_structure_method": "tight_binding" if use_tb_electronic_structure else "vegard_only"
        },
        "compositions": {}
    }

    logger.info(f"Calculating {len(properties)} properties for {len(x_values)} compositions...")

    for x in x_values:
        logger.info(f"  Calculating properties for x = {x:.3f}")
        props = calculator.calculate_multiple_properties(properties, x)
        results["compositions"][f"x_{x:.3f}"] = {
            "x": x,
            "properties": props
        }

    # Save results
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Saved property calculations to {output_file}")
    if use_tb_electronic_structure:
        logger.info("Tight-binding electronic structure calculations included")

    return results


def run_calculation_pipeline(
    alloy_system: str,
    material1: str,
    material2: str,
    structure_output_dir: str = "data/outputs/calculations/structures",
    properties_output_file: str = "data/outputs/calculations/properties.json",
    x_values: Optional[List[float]] = None,
    data_source: str = "literature",
    enable_charge_density: Optional[bool] = None,
    enable_relaxation: Optional[bool] = None,
    use_tb_electronic_structure: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Run the complete calculation pipeline: structure generation and property calculation.
    Enhanced with charge density interpolation, structure relaxation, and tight-binding electronic structure.

    Supports any alloy system defined in materials/properties/.

    Args:
        alloy_system: Name of alloy system
        material1: First binary material
        material2: Second binary material
        structure_output_dir: Directory for interpolated structures
        properties_output_file: File for calculated properties
        x_values: List of compositions
        data_source: "literature" or "mp_api"
        enable_charge_density: Enable charge density interpolation
        enable_relaxation: Enable ML-based structure relaxation
        use_tb_electronic_structure: Use tight-binding for electronic properties

    Returns:
        Combined results from structure generation and property calculation
    """
    logger.info(f"Starting Enhanced {alloy_system} Calculation Pipeline...")

    # Load config for defaults
    config = get_config()
    if enable_charge_density is None:
        enable_charge_density = config.get('features.enable_charge_density', True)
    if enable_relaxation is None:
        enable_relaxation = config.get('features.enable_relaxation', True)
    if use_tb_electronic_structure is None:
        use_tb_electronic_structure = config.get('features.enable_tight_binding', True)

    # Generate structures with advanced features
    structures = generate_structures(
        alloy_system=alloy_system,
        material1=material1,
        material2=material2,
        output_dir=structure_output_dir,
        x_values=x_values,
        data_source=data_source,
        enable_charge_density=enable_charge_density,
        enable_relaxation=enable_relaxation
    )

    # Calculate properties with tight-binding
    properties = calculate_properties(
        alloy_system=alloy_system,
        x_values=x_values,
        data_source=data_source,
        output_file=properties_output_file,
        use_tb_electronic_structure=use_tb_electronic_structure
    )

    logger.info("Enhanced Pipeline Completed Successfully!")
    logger.info("Features enabled:")
    logger.info(f"  • Charge density interpolation: {'OK' if enable_charge_density else 'No'}")
    logger.info(f"  • Structure relaxation: {'OK' if enable_relaxation else 'No'}")
    logger.info(f"  • Tight-binding electronic structure: {'OK' if use_tb_electronic_structure else 'No'}")

    return {
        "structures": structures,
        "properties": properties,
        "summary": {
            "alloy_system": alloy_system,
            "materials": [material1, material2],
            "num_structures": len(structures),
            "num_compositions": len(properties["compositions"]),
            "data_source": data_source,
            "features": {
                "charge_density": enable_charge_density,
                "relaxation": enable_relaxation,
                "tb_electronic_structure": use_tb_electronic_structure
            }
        }
    }


def run_full_pipeline(
    alloy_system: str,
    material1: str,
    material2: str,
    x_values: Optional[List[float]] = None,
    enable_all_features: bool = True
) -> Dict[str, Any]:
    """
    Run the complete enhanced pipeline with all advanced features enabled.

    This is the main entry point for using the system. It supports
    any alloy system defined in materials/properties/.

    Args:
        alloy_system: Name of alloy system
        material1: First binary material
        material2: Second binary material
        x_values: List of compositions (default: config values)
        enable_all_features: Enable charge density, relaxation, and TB electronic structure

    Returns:
        Complete pipeline results

    Examples:
        results = run_full_pipeline(
            alloy_system="AlGaAs",
            material1="GaAs",
            material2="AlAs"
        )
    """
    return run_calculation_pipeline(
        alloy_system=alloy_system,
        material1=material1,
        material2=material2,
        x_values=x_values,
        enable_charge_density=enable_all_features,
        enable_relaxation=enable_all_features,
        use_tb_electronic_structure=enable_all_features
    )


if __name__ == "__main__":
    # Example usage with all features enabled
    logger.info("Material-Agnostic Research Pipeline")
    logger.info("=" * 60)

    # Example: AlGaAs system
    logger.info("\nExample: AlGaAs System")
    results = run_full_pipeline(
        alloy_system="AlGaAs",
        material1="GaAs",
        material2="AlAs",
        enable_all_features=True
    )

    logger.info("Results Summary:")
    logger.info(f"  • Alloy system: {results['summary']['alloy_system']}")
    logger.info(f"  • Materials: {' / '.join(results['summary']['materials'])}")
    logger.info(f"  • Generated {results['summary']['num_structures']} alloy structures")
    logger.info(f"  • Calculated properties for {results['summary']['num_compositions']} compositions")
    logger.info(f"  • Data source: {results['summary']['data_source']}")

    features = results['summary']['features']
    logger.info(f"  • Charge density interpolation: {'✓' if features['charge_density'] else '✗'}")
    logger.info(f"  • Structure relaxation: {'✓' if features['relaxation'] else '✗'}")
    logger.info(f"  • Tight-binding electronic structure: {'✓' if features['tb_electronic_structure'] else '✗'}")

    logger.info("\nPipeline execution completed successfully!")
    logger.info("Check data/outputs/calculations/ for results")

    # Show how to use with other alloy systems
    logger.info("\n" + "=" * 60)
    logger.info("To use with other alloy systems:")
    logger.info("  1. Add material YAML files to materials/properties/")
    logger.info("  2. Add alloy system YAML to materials/properties/")
    logger.info("  3. Run: run_full_pipeline(alloy_system='YourAlloy', material1='Mat1', material2='Mat2')")