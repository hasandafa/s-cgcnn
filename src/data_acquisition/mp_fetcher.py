"""
Materials Project Data Fetcher for AlGaAs System
UPDATED for MP API v0.41+ (new structure)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from mp_api.client import MPRester
from pymatgen.core import Structure

from src.utils.logger_config import setup_logger


class MPDataFetcher:
    """
    Fetches crystal structure and electronic properties from Materials Project.
    Updated for new MP API structure.
    """
    
    def __init__(self, api_key: str, output_dir: str = "data/raw"):
        """
        Initialize MP fetcher.
        
        Args:
            api_key: Materials Project API key
            output_dir: Directory to save fetched data
        """
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = setup_logger(__name__, log_file="logs/v0.1_mp_fetcher.log")
        self.logger.info("MPDataFetcher initialized")
        
        # Materials to fetch
        self.materials = {
            "GaAs": "mp-2534",
            "AlAs": "mp-2172"
        }
    
    def fetch_material_data(self, mp_id: str, material_name: str) -> Dict:
        """
        Fetch comprehensive material data from Materials Project.
        Updated for new API structure.
        
        Args:
            mp_id: Materials Project ID
            material_name: Name of material (for logging)
        
        Returns:
            Dictionary containing all fetched data
        """
        self.logger.info(f"Fetching data for {material_name} ({mp_id})...")
        
        data = {
            "mp_id": mp_id,
            "material_name": material_name,
            "structure": None,
            "properties": {},
            "band_structure": None,
            "dos": None
        }
        
        try:
            with MPRester(self.api_key) as mpr:
                # Fetch summary data (structure + basic properties)
                self.logger.info(f"  → Fetching summary data...")
                
                summary = mpr.materials.summary.search(
                    material_ids=[mp_id],
                    fields=[
                        "material_id",
                        "formula_pretty", 
                        "structure",
                        "symmetry",
                        "density",
                        "formation_energy_per_atom",
                        "energy_per_atom",
                        "is_stable",
                        "is_metal",
                        "ordering",
                        "theoretical"
                    ]
                )
                
                if not summary:
                    raise ValueError(f"No data found for {mp_id}")
                
                mat = summary[0]
                
                # Extract structure
                data["structure"] = mat.structure
                self.logger.info(f"  ✓ Structure: {mat.structure.composition}")
                
                # Extract basic properties
                data["properties"]["formula"] = mat.formula_pretty
                data["properties"]["density"] = mat.density
                data["properties"]["formation_energy_per_atom"] = mat.formation_energy_per_atom
                data["properties"]["energy_per_atom"] = mat.energy_per_atom
                data["properties"]["is_stable"] = mat.is_stable
                data["properties"]["is_metal"] = mat.is_metal if hasattr(mat, 'is_metal') else False
                data["properties"]["symmetry"] = str(mat.symmetry)
                
                # Fetch electronic structure data separately
                self.logger.info(f"  → Fetching electronic structure...")
                try:
                    electronic = mpr.materials.electronic_structure.search(
                        material_ids=[mp_id],
                        fields=[
                            "material_id",
                            "band_gap",
                            "cbm",
                            "vbm", 
                            "efermi",
                            "is_gap_direct",
                            "is_metal"
                        ]
                    )
                    
                    if electronic:
                        elec = electronic[0]
                        data["properties"]["band_gap"] = elec.band_gap if hasattr(elec, 'band_gap') else 0.0
                        data["properties"]["is_gap_direct"] = elec.is_gap_direct if hasattr(elec, 'is_gap_direct') else False
                        data["properties"]["efermi"] = elec.efermi if hasattr(elec, 'efermi') else 0.0
                        data["properties"]["vbm"] = elec.vbm.energy if hasattr(elec, 'vbm') else 0.0
                        data["properties"]["cbm"] = elec.cbm.energy if hasattr(elec, 'cbm') else 0.0
                        self.logger.info(f"  ✓ Band gap: {data['properties']['band_gap']:.3f} eV")
                    else:
                        self.logger.warning(f"  ⚠ No electronic structure data available")
                        # Set default values
                        data["properties"]["band_gap"] = 1.42 if material_name == "GaAs" else 2.17
                        data["properties"]["is_gap_direct"] = True if material_name == "GaAs" else False
                        data["properties"]["efermi"] = 0.0
                        data["properties"]["vbm"] = 0.0
                        data["properties"]["cbm"] = 0.0
                        
                except Exception as e:
                    self.logger.warning(f"  ⚠ Electronic structure error: {e}")
                    # Use literature values as fallback
                    if material_name == "GaAs":
                        data["properties"]["band_gap"] = 1.424
                        data["properties"]["is_gap_direct"] = True
                    else:  # AlAs
                        data["properties"]["band_gap"] = 2.168
                        data["properties"]["is_gap_direct"] = False
                    data["properties"]["efermi"] = 0.0
                    data["properties"]["vbm"] = 0.0
                    data["properties"]["cbm"] = 0.0
                
                # Fetch elastic properties
                try:
                    self.logger.info(f"  → Fetching elastic properties...")
                    elasticity = mpr.materials.elasticity.search(
                        material_ids=[mp_id],
                        fields=[
                            "material_id",
                            "elastic_tensor",
                            "bulk_modulus",
                            "shear_modulus",
                            "universal_anisotropy",
                            "homogeneous_poisson"
                        ]
                    )
                    
                    if elasticity:
                        elas = elasticity[0]
                        if hasattr(elas, 'bulk_modulus') and elas.bulk_modulus:
                            data["properties"]["elastic_tensor"] = {
                                "bulk_modulus_vrh": elas.bulk_modulus.vrh,
                                "shear_modulus_vrh": elas.shear_modulus.vrh if hasattr(elas, 'shear_modulus') else None,
                            }
                            self.logger.info(f"  ✓ Elastic: K={elas.bulk_modulus.vrh:.1f} GPa")
                except Exception as e:
                    self.logger.warning(f"  ⚠ Elastic tensor not available: {e}")
                
                # Fetch dielectric properties
                try:
                    self.logger.info(f"  → Fetching dielectric properties...")
                    dielectric = mpr.materials.dielectric.search(
                        material_ids=[mp_id],
                        fields=[
                            "material_id",
                            "e_total",
                            "e_ionic", 
                            "e_electronic",
                            "n"
                        ]
                    )
                    
                    if dielectric:
                        diel = dielectric[0]
                        data["properties"]["dielectric"] = {
                            "total": diel.e_total if hasattr(diel, 'e_total') else None,
                            "ionic": diel.e_ionic if hasattr(diel, 'e_ionic') else None,
                            "electronic": diel.e_electronic if hasattr(diel, 'e_electronic') else None,
                            "refractive_index": diel.n if hasattr(diel, 'n') else None
                        }
                        self.logger.info(f"  ✓ Dielectric properties fetched")
                except Exception as e:
                    self.logger.warning(f"  ⚠ Dielectric data not available: {e}")
                
                self.logger.info(f"✓ Successfully fetched data for {material_name}")
                
        except Exception as e:
            self.logger.error(f"✗ Error fetching {material_name}: {e}")
            raise
        
        return data
    
    def save_data(self, data: Dict, filename: str):
        """
        Save fetched data to JSON file.
        
        Args:
            data: Data dictionary
            filename: Output filename
        """
        output_file = self.output_dir / filename
        
        # Convert pymatgen objects to dict for JSON serialization
        save_data = data.copy()
        
        if data["structure"] is not None:
            save_data["structure"] = data["structure"].as_dict()
        
        with open(output_file, 'w') as f:
            json.dump(save_data, f, indent=2, default=str)
        
        self.logger.info(f"✓ Saved data to {output_file}")
    
    def fetch_all_materials(self) -> Dict[str, Dict]:
        """
        Fetch data for all materials in the system.
        
        Returns:
            Dictionary with material names as keys and data as values
        """
        self.logger.info("="*60)
        self.logger.info("Starting data fetch for AlGaAs system")
        self.logger.info("="*60)
        
        all_data = {}
        
        for material_name, mp_id in self.materials.items():
            try:
                data = self.fetch_material_data(mp_id, material_name)
                all_data[material_name] = data
                
                # Save individual material data
                filename = f"mp_{mp_id.replace('mp-', '')}_{material_name}.json"
                self.save_data(data, filename)
                
            except Exception as e:
                self.logger.error(f"Failed to fetch {material_name}: {e}")
                continue
        
        self.logger.info("="*60)
        self.logger.info(f"Data fetch complete. {len(all_data)}/{len(self.materials)} materials fetched")
        self.logger.info("="*60)
        
        return all_data
    
    def load_saved_data(self, material_name: str) -> Optional[Dict]:
        """
        Load previously saved material data.
        
        Args:
            material_name: Name of material
        
        Returns:
            Data dictionary or None if not found
        """
        mp_id = self.materials.get(material_name)
        if not mp_id:
            self.logger.error(f"Unknown material: {material_name}")
            return None
        
        filename = f"mp_{mp_id.replace('mp-', '')}_{material_name}.json"
        filepath = self.output_dir / filename
        
        if not filepath.exists():
            self.logger.warning(f"Saved data not found: {filepath}")
            return None
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Convert structure dict back to Structure object
        if data.get("structure"):
            data["structure"] = Structure.from_dict(data["structure"])
        
        self.logger.info(f"Loaded data for {material_name} from {filepath}")
        return data


def main():
    """
    Main execution function for standalone use.
    """
    import sys
    
    # Read API key
    api_key_file = Path("config/mp_api_key.txt")
    
    if not api_key_file.exists():
        print("ERROR: API key file not found!")
        print("Please create config/mp_api_key.txt with your Materials Project API key")
        print("Get your API key from: https://next-gen.materialsproject.org/api")
        sys.exit(1)
    
    with open(api_key_file, 'r') as f:
        api_key = f.read().strip()
    
    # Fetch data
    fetcher = MPDataFetcher(api_key)
    data = fetcher.fetch_all_materials()
    
    # Summary
    print("\n" + "="*60)
    print("FETCH SUMMARY")
    print("="*60)
    for material_name, mat_data in data.items():
        print(f"\n{material_name} ({mat_data['mp_id']}):")
        print(f"  Formula: {mat_data['structure'].composition}")
        print(f"  Band gap: {mat_data['properties']['band_gap']:.3f} eV "
              f"({'direct' if mat_data['properties']['is_gap_direct'] else 'indirect'})")
        print(f"  Density: {mat_data['properties']['density']:.3f} g/cm³")
        if "elastic_tensor" in mat_data["properties"]:
            print(f"  Bulk modulus: {mat_data['properties']['elastic_tensor']['bulk_modulus_vrh']:.1f} GPa")


if __name__ == "__main__":
    main()