"""
CIF Processor for Crystal Structure Analysis.

This module provides tools to extract crystal structure information from CIF files
and update material YAML files with this metadata for material-agnostic tight-binding.

Author: Razasyattar M. N. && Abdullah Hasan Dafa
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

try:
    from pymatgen.core import Structure
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    from pymatgen.symmetry.bandstructure import HighSymmKpath
    from pymatgen.io.cif import CifParser
    PYMATGEN_AVAILABLE = True
except ImportError:
    PYMATGEN_AVAILABLE = False

import yaml
from ..utils import get_logger

logger = get_logger(__name__)

if not PYMATGEN_AVAILABLE:
    logger.warning("pymatgen package not available. CIF processing features limited.")


@dataclass
class CrystalStructureMetadata:
    """Container for crystal structure metadata."""
    lattice_parameters: Dict[str, float]
    lattice_angles: Dict[str, float]
    space_group: str
    crystal_system: str
    kpath_type: str
    kpath_points: List[Dict[str, Any]]
    basis_atoms: List[Dict[str, Any]]
    cif_file_path: str


class CIFProcessor:
    """Processes CIF files to extract crystal structure information."""

    def __init__(self):
        """Initialize the CIF processor."""
        if not PYMATGEN_AVAILABLE:
            raise ImportError("pymatgen package required for CIF processing. Install with: pip install pymatgen")

    def extract_structure_from_cif(self, cif_path: Path) -> Optional[Structure]:
        """
        Extract structure from CIF file.
        
        Args:
            cif_path: Path to CIF file
            
        Returns:
            pymatgen Structure object or None if failed
        """
        try:
            parser = CifParser(str(cif_path))
            structures = parser.get_structures()
            if structures:
                return structures[0]  # Return first structure
            else:
                logger.warning(f"No structures found in {cif_path}")
                return None
        except Exception as e:
            logger.error(f"Failed to parse CIF file {cif_path}: {e}")
            return None

    def analyze_crystal_structure(self, structure: Structure) -> CrystalStructureMetadata:
        """
        Analyze crystal structure and extract metadata.
        
        Args:
            structure: pymatgen Structure object
            
        Returns:
            CrystalStructureMetadata with extracted information
        """
        # Get lattice parameters
        lattice = structure.lattice
        lattice_parameters = {
            'a': float(lattice.a),
            'b': float(lattice.b),
            'c': float(lattice.c)
        }
        
        lattice_angles = {
            'alpha': float(lattice.alpha),
            'beta': float(lattice.beta),
            'gamma': float(lattice.gamma)
        }
        
        # Get space group information
        sga = SpacegroupAnalyzer(structure)
        space_group = sga.get_space_group_symbol()
        crystal_system = sga.get_crystal_system()
        
        # Determine k-path type based on crystal system
        kpath_type = self._determine_kpath_type(crystal_system)
        
        # Get high-symmetry k-points
        kpath_points = self._get_kpath_points(structure)
        
        # Get basis atoms
        basis_atoms = []
        for site in structure:
            basis_atoms.append({
                'element': str(site.specie),
                'position': [float(coord) for coord in site.coords],
                'fractional_position': [float(coord) for coord in site.frac_coords]
            })
        
        return CrystalStructureMetadata(
            lattice_parameters=lattice_parameters,
            lattice_angles=lattice_angles,
            space_group=space_group,
            crystal_system=crystal_system,
            kpath_type=kpath_type,
            kpath_points=kpath_points,
            basis_atoms=basis_atoms,
            cif_file_path=""
        )

    def _determine_kpath_type(self, crystal_system: str) -> str:
        """Determine k-path type based on crystal system."""
        kpath_mapping = {
            'cubic': 'cubic',
            'hexagonal': 'hexagonal',
            'tetragonal': 'tetragonal',
            'orthorhombic': 'orthorhombic',
            'monoclinic': 'monoclinic',
            'triclinic': 'triclinic',
            'rhombohedral': 'rhombohedral'
        }
        return kpath_mapping.get(crystal_system.lower(), 'automatic')

    def _get_kpath_points(self, structure: Structure) -> List[Dict[str, Any]]:
        """Get high-symmetry k-points for the structure."""
        try:
            kpath = HighSymmKpath(structure)
            kpath_dict = kpath.kpath
            
            # Extract k-path points information
            points = []
            if 'kpoints' in kpath_dict:
                for label, coords in kpath_dict['kpoints'].items():
                    points.append({
                        'label': label,
                        'coordinates': [float(c) for c in coords]
                    })
            return points
        except Exception as e:
            logger.warning(f"Could not determine k-path points: {e}")
            return []

    def process_cif_file(self, cif_path: Path) -> Optional[CrystalStructureMetadata]:
        """
        Process a CIF file and extract crystal structure metadata.
        
        Args:
            cif_path: Path to CIF file
            
        Returns:
            CrystalStructureMetadata or None if failed
        """
        logger.info(f"Processing CIF file: {cif_path}")
        
        # Extract structure
        structure = self.extract_structure_from_cif(cif_path)
        if not structure:
            return None
            
        # Analyze structure
        metadata = self.analyze_crystal_structure(structure)
        metadata.cif_file_path = str(cif_path)
        
        logger.info(f"Successfully processed {cif_path}: {metadata.crystal_system} system, space group {metadata.space_group}")
        return metadata

    def update_material_yaml(self, material_yaml_path: Path,
                           crystal_metadata: CrystalStructureMetadata) -> bool:
        """
        Update material YAML file with crystal structure metadata.
        
        Args:
            material_yaml_path: Path to material YAML file
            crystal_metadata: CrystalStructureMetadata to add to YAML
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read existing YAML with proper encoding
            with open(material_yaml_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
            
            # Add crystal structure section
            yaml_data['crystal_structure'] = {
                'lattice_parameters': crystal_metadata.lattice_parameters,
                'lattice_angles': crystal_metadata.lattice_angles,
                'space_group': crystal_metadata.space_group,
                'crystal_system': crystal_metadata.crystal_system,
                'kpath_type': crystal_metadata.kpath_type,
                'kpath_points': crystal_metadata.kpath_points,
                'basis_atoms': crystal_metadata.basis_atoms,
                'cif_file_path': crystal_metadata.cif_file_path
            }
            
            # Write updated YAML with proper encoding
            with open(material_yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, default_flow_style=False, indent=2, allow_unicode=True)
            
            logger.info(f"Updated {material_yaml_path} with crystal structure metadata")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update {material_yaml_path}: {e}")
            return False

    def process_material_directory(self, material_dir: Path, 
                                 material_yaml_path: Path) -> bool:
        """
        Process all CIF files in a material directory and update YAML.
        
        Args:
            material_dir: Directory containing CIF files
            material_yaml_path: Path to material YAML file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find CIF files
            cif_files = list(material_dir.glob("*.cif"))
            if not cif_files:
                logger.warning(f"No CIF files found in {material_dir}")
                return False
                
            # Process first CIF file (assuming there's only one per material)
            cif_file = cif_files[0]
            metadata = self.process_cif_file(cif_file)
            
            if metadata:
                return self.update_material_yaml(material_yaml_path, metadata)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to process material directory {material_dir}: {e}")
            return False


def process_all_materials(data_dir: Path = Path("data"),
                         properties_dir: Path = Path("materials/properties")) -> bool:
    """
    Process all materials and update their YAML files with crystal structure metadata.
    
    Args:
        data_dir: Directory containing material data subdirectories
        properties_dir: Directory containing material YAML files
        
    Returns:
        True if successful, False otherwise
    """
    try:
        processor = CIFProcessor()
        success_count = 0
        total_count = 0
        
        # Process each material directory
        for material_dir in data_dir.iterdir():
            if material_dir.is_dir():
                total_count += 1
                material_id = material_dir.name
                
                # Find corresponding YAML file
                yaml_files = list(properties_dir.glob(f"*.yaml"))
                yaml_file = None
                for yf in yaml_files:
                    # Try to match by material name in YAML
                    try:
                        with open(yf, 'r', encoding='utf-8') as f:
                            yaml_data = yaml.safe_load(f)
                            if 'material' in yaml_data and yaml_data['material'].get('mp_id') == material_id:
                                yaml_file = yf
                                break
                    except Exception as e:
                        logger.warning(f"Could not read {yf}: {e}")
                        continue
                
                if yaml_file and material_dir.exists():
                    logger.info(f"Processing {material_id}")
                    if processor.process_material_directory(material_dir, yaml_file):
                        success_count += 1
                else:
                    logger.warning(f"No matching YAML file found for {material_id}")
        
        logger.info(f"Processed {success_count}/{total_count} materials successfully")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Failed to process all materials: {e}")
        return False


# Convenience functions
def process_single_material(material_id: str, data_dir: str = "data", 
                          properties_dir: str = "materials/properties") -> bool:
    """Process a single material."""
    processor = CIFProcessor()
    material_dir = Path(data_dir) / material_id
    properties_path = Path(properties_dir)
    
    # Find corresponding YAML file
    yaml_files = list(properties_path.glob(f"*.yaml"))
    yaml_file = None
    for yf in yaml_files:
        with open(yf, 'r') as f:
            yaml_data = yaml.safe_load(f)
            if 'material' in yaml_data and yaml_data['material'].get('mp_id') == material_id:
                yaml_file = yf
                break
    
    if yaml_file and material_dir.exists():
        return processor.process_material_directory(material_dir, yaml_file)
    else:
        logger.error(f"Material directory or YAML file not found for {material_id}")
        return False


if __name__ == "__main__":
    # Example usage
    try:
        success = process_all_materials()
        if success:
            logger.info("Successfully processed all materials")
        else:
            logger.error("Failed to process materials")
    except Exception as e:
        logger.error(f"Processing failed: {e}")