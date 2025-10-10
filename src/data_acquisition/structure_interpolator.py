"""
Structure Interpolator for AlₓGa₁₋ₓAs System
Generates ordered supercells by systematic Ga→Al substitution
"""

import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import json
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from pymatgen.core import Structure, Lattice, Element
from pymatgen.io.cif import CifWriter
from pymatgen.analysis.structure_matcher import StructureMatcher

from src.utils.logger_config import setup_logger
from src.utils.constants import (
    calculate_property_vegard, 
    get_band_gap_algaas,
    get_lattice_constant,
    GaAs_PROPERTIES,
    AlAs_PROPERTIES,
    BOWING_PARAMETERS
)


class StructureInterpolator:
    """
    Generates AlₓGa₁₋ₓAs structures via ordered supercell substitution.
    """
    
    def __init__(self, 
                 gaas_structure: Structure,
                 alas_structure: Structure,
                 supercell_size: List[int] = [2, 2, 2],
                 output_dir: str = "data/structures"):
        """
        Initialize structure interpolator.
        
        Args:
            gaas_structure: GaAs primitive structure from MP
            alas_structure: AlAs primitive structure from MP
            supercell_size: Supercell dimensions [a, b, c]
            output_dir: Output directory for structures
        """
        self.gaas_structure = gaas_structure
        self.alas_structure = alas_structure
        self.supercell_size = supercell_size
        
        self.output_dir = Path(output_dir)
        self.cif_dir = self.output_dir / "cif"
        self.metadata_dir = self.output_dir / "metadata"
        
        self.cif_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = setup_logger(__name__, log_file="logs/v0.1_interpolation.log")
        self.logger.info("StructureInterpolator initialized")
        self.logger.info(f"Supercell size: {supercell_size}")
        
        # Create base supercell from GaAs
        self.base_supercell = self._create_base_supercell()
        self.n_ga_sites = self._count_ga_sites()
        
        self.logger.info(f"Base supercell: {self.base_supercell.composition}")
        self.logger.info(f"Total Ga sites available for substitution: {self.n_ga_sites}")
    
    def _create_base_supercell(self) -> Structure:
        """Create supercell from GaAs primitive cell."""
        supercell = self.gaas_structure.copy()
        supercell.make_supercell(self.supercell_size)
        return supercell
    
    def _count_ga_sites(self) -> int:
        """Count number of Ga sites in supercell."""
        return sum(1 for site in self.base_supercell if site.specie.symbol == "Ga")
    
    def generate_structure(self, x: float) -> Structure:
        """
        Generate AlₓGa₁₋ₓAs structure by ordered Ga→Al substitution.
        
        Args:
            x: Al fraction (0 to 1)
        
        Returns:
            AlₓGa₁₋ₓAs structure
        """
        if not 0 <= x <= 1:
            raise ValueError(f"x must be between 0 and 1, got {x}")
        
        # Calculate number of Al atoms needed
        n_al = int(round(x * self.n_ga_sites))
        n_ga = self.n_ga_sites - n_al
        
        self.logger.debug(f"x={x:.3f}: Substituting {n_al}/{self.n_ga_sites} Ga→Al sites")
        
        # Start with base GaAs supercell
        structure = self.base_supercell.copy()
        
        # Find all Ga site indices
        ga_indices = [i for i, site in enumerate(structure) 
                     if site.specie.symbol == "Ga"]
        
        # Perform ordered substitution (first n_al sites)
        # This creates a periodic, ordered structure
        for i in range(n_al):
            structure.replace(ga_indices[i], Element("Al"))
        
        # Adjust lattice constant using Vegard's law
        new_lattice_param = get_lattice_constant(x)
        scale_factor = new_lattice_param / self.gaas_structure.lattice.a
        structure.apply_strain([scale_factor - 1] * 3)
        
        # Validate composition
        composition = structure.composition
        actual_x = composition.get("Al", 0) / (composition.get("Al", 0) + composition.get("Ga", 0))
        
        if abs(actual_x - x) > 0.01:
            self.logger.warning(f"Composition mismatch: target x={x:.3f}, actual x={actual_x:.3f}")
        
        return structure
    
    def calculate_properties(self, x: float) -> Dict:
        """
        Calculate interpolated properties using bowing parameters.
        
        Args:
            x: Al fraction
        
        Returns:
            Dictionary of interpolated properties
        """
        properties = {}
        
        # Structural
        properties["lattice_constant"] = get_lattice_constant(x)
        properties["density"] = calculate_property_vegard(
            GaAs_PROPERTIES["density"],
            AlAs_PROPERTIES["density"],
            x, 0.0
        )
        
        # Electronic - band gap with crossover
        band_gap_data = get_band_gap_algaas(x)
        properties["band_gap"] = band_gap_data["value"]
        properties["band_gap_type"] = band_gap_data["type"]
        properties["band_gap_direct"] = band_gap_data["Eg_direct"]
        properties["band_gap_indirect_X"] = band_gap_data["Eg_indirect_X"]
        
        properties["electron_affinity"] = calculate_property_vegard(
            GaAs_PROPERTIES["electron_affinity"],
            AlAs_PROPERTIES["electron_affinity"],
            x, BOWING_PARAMETERS["electron_affinity"]
        )
        
        # Effective masses
        properties["electron_effective_mass"] = calculate_property_vegard(
            GaAs_PROPERTIES["electron_effective_mass_gamma"],
            AlAs_PROPERTIES["electron_effective_mass_gamma"],
            x, 0.0
        )
        
        properties["hole_effective_mass_heavy"] = calculate_property_vegard(
            GaAs_PROPERTIES["hole_effective_mass_heavy"],
            AlAs_PROPERTIES["hole_effective_mass_heavy"],
            x, 0.0
        )
        
        # Dielectric
        properties["static_dielectric"] = calculate_property_vegard(
            GaAs_PROPERTIES["static_dielectric_constant"],
            AlAs_PROPERTIES["static_dielectric_constant"],
            x, BOWING_PARAMETERS["static_dielectric"]
        )
        
        properties["optical_dielectric"] = calculate_property_vegard(
            GaAs_PROPERTIES["optical_dielectric_constant"],
            AlAs_PROPERTIES["optical_dielectric_constant"],
            x, BOWING_PARAMETERS["optical_dielectric"]
        )
        
        properties["refractive_index"] = calculate_property_vegard(
            GaAs_PROPERTIES["refractive_index"],
            AlAs_PROPERTIES["refractive_index"],
            x, BOWING_PARAMETERS["refractive_index"]
        )
        
        # Elastic constants
        properties["elastic_c11"] = calculate_property_vegard(
            GaAs_PROPERTIES["elastic_c11"],
            AlAs_PROPERTIES["elastic_c11"],
            x, BOWING_PARAMETERS["elastic_c11"]
        )
        
        properties["elastic_c12"] = calculate_property_vegard(
            GaAs_PROPERTIES["elastic_c12"],
            AlAs_PROPERTIES["elastic_c12"],
            x, BOWING_PARAMETERS["elastic_c12"]
        )
        
        properties["elastic_c44"] = calculate_property_vegard(
            GaAs_PROPERTIES["elastic_c44"],
            AlAs_PROPERTIES["elastic_c44"],
            x, BOWING_PARAMETERS["elastic_c44"]
        )
        
        # Bulk and shear modulus
        properties["bulk_modulus"] = calculate_property_vegard(
            GaAs_PROPERTIES["bulk_modulus"],
            AlAs_PROPERTIES["bulk_modulus"],
            x, 0.0
        )
        
        properties["shear_modulus"] = calculate_property_vegard(
            GaAs_PROPERTIES["shear_modulus"],
            AlAs_PROPERTIES["shear_modulus"],
            x, 0.0
        )
        
        # Thermal
        properties["thermal_conductivity"] = calculate_property_vegard(
            GaAs_PROPERTIES["thermal_conductivity"],
            AlAs_PROPERTIES["thermal_conductivity"],
            x, BOWING_PARAMETERS["thermal_conductivity"]
        )
        
        properties["thermal_expansion"] = calculate_property_vegard(
            GaAs_PROPERTIES["thermal_expansion"],
            AlAs_PROPERTIES["thermal_expansion"],
            x, BOWING_PARAMETERS["thermal_expansion"]
        )
        
        properties["specific_heat"] = calculate_property_vegard(
            GaAs_PROPERTIES["specific_heat"],
            AlAs_PROPERTIES["specific_heat"],
            x, 0.0
        )
        
        properties["debye_temperature"] = calculate_property_vegard(
            GaAs_PROPERTIES["debye_temperature"],
            AlAs_PROPERTIES["debye_temperature"],
            x, 0.0
        )
        
        # Transport (rough estimates)
        if x < 0.45:  # Direct gap regime
            properties["electron_mobility"] = calculate_property_vegard(
                GaAs_PROPERTIES["electron_mobility"],
                AlAs_PROPERTIES["electron_mobility"],
                x, -8000  # Strong bowing for mobility
            )
        else:  # Indirect gap regime - lower mobility
            properties["electron_mobility"] = AlAs_PROPERTIES["electron_mobility"] * (1 - 0.5*x)
        
        properties["hole_mobility"] = calculate_property_vegard(
            GaAs_PROPERTIES["hole_mobility"],
            AlAs_PROPERTIES["hole_mobility"],
            x, 0.0
        )
        
        return properties
    
    def save_structure(self, structure: Structure, x: float, properties: Dict):
        """
        Save structure as CIF and metadata as JSON.
        
        Args:
            structure: AlGaAs structure
            x: Al fraction
            properties: Calculated properties
        """
        # Generate filenames
        x_str = f"{x:.3f}".replace(".", "_")
        cif_filename = self.cif_dir / f"AlGaAs_x_{x_str}.cif"
        metadata_filename = self.metadata_dir / f"AlGaAs_x_{x_str}.json"
        
        # Save CIF
        cif_writer = CifWriter(structure)
        cif_writer.write_file(str(cif_filename))
        
        # Prepare metadata
        metadata = {
            "composition": str(structure.composition),
            "x_value": x,
            "formula": f"Al{x:.3f}Ga{1-x:.3f}As",
            "lattice_parameters": {
                "a": structure.lattice.a,
                "b": structure.lattice.b,
                "c": structure.lattice.c,
                "alpha": structure.lattice.alpha,
                "beta": structure.lattice.beta,
                "gamma": structure.lattice.gamma,
                "volume": structure.lattice.volume
            },
            "num_sites": len(structure),
            "space_group": structure.get_space_group_info()[0],
            "properties": properties,
            "cif_file": str(cif_filename.name)
        }
        
        # Save metadata
        with open(metadata_filename, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"✓ Saved x={x:.3f}: {cif_filename.name}")
    
    def generate_all_structures(self, 
                               x_start: float = 0.0,
                               x_end: float = 1.0,
                               x_step: float = 0.025) -> List[Tuple[float, Structure, Dict]]:
        """
        Generate all AlₓGa₁₋ₓAs structures.
        
        Args:
            x_start: Starting Al fraction
            x_end: Ending Al fraction
            x_step: Step size
        
        Returns:
            List of (x, structure, properties) tuples
        """
        x_values = np.arange(x_start, x_end + x_step/2, x_step)
        
        self.logger.info("="*60)
        self.logger.info(f"Generating {len(x_values)} AlGaAs structures")
        self.logger.info(f"x range: {x_start:.3f} to {x_end:.3f} (step {x_step:.3f})")
        self.logger.info("="*60)
        
        results = []
        
        for x in x_values:
            try:
                structure = self.generate_structure(x)
                properties = self.calculate_properties(x)
                self.save_structure(structure, x, properties)
                
                results.append((x, structure, properties))
                
            except Exception as e:
                self.logger.error(f"✗ Error generating x={x:.3f}: {e}")
                continue
        
        self.logger.info("="*60)
        self.logger.info(f"✓ Generated {len(results)}/{len(x_values)} structures")
        self.logger.info("="*60)
        
        # Save summary
        self._save_summary(results)
        
        return results
    
    def _save_summary(self, results: List[Tuple[float, Structure, Dict]]):
        """Save summary of all generated structures."""
        summary = {
            "total_structures": len(results),
            "x_values": [x for x, _, _ in results],
            "compositions": [str(s.composition) for _, s, _ in results],
            "properties_summary": {}
        }
        
        # Calculate property ranges
        for prop_name in results[0][2].keys():
            values = [props[prop_name] for _, _, props in results 
                     if isinstance(props[prop_name], (int, float))]
            if values:
                summary["properties_summary"][prop_name] = {
                    "min": float(min(values)),
                    "max": float(max(values)),
                    "mean": float(np.mean(values))
                }
        
        summary_file = self.metadata_dir / "generation_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"✓ Summary saved to {summary_file}")


def main():
    """
    Main execution for standalone use.
    """
    from src.data_acquisition.mp_fetcher import MPDataFetcher
    
    # Load structures from MP data
    fetcher = MPDataFetcher("")  # Empty API key for loading only
    gaas_data = fetcher.load_saved_data("GaAs")
    alas_data = fetcher.load_saved_data("AlAs")
    
    if gaas_data is None or alas_data is None:
        print("ERROR: MP data not found. Please run mp_fetcher.py first!")
        sys.exit(1)
    
    # Initialize interpolator
    interpolator = StructureInterpolator(
        gaas_structure=gaas_data["structure"],
        alas_structure=alas_data["structure"],
        supercell_size=[2, 2, 2]
    )
    
    # Generate all structures
    results = interpolator.generate_all_structures()
    
    # Print summary
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)
    print(f"Total structures generated: {len(results)}")
    print(f"Composition range: Al₀Ga₁As to Al₁Ga₀As")
    print(f"Output directory: {interpolator.output_dir}")
    print("="*60)


if __name__ == "__main__":
    main()