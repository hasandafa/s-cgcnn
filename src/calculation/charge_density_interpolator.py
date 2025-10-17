"""
Charge Density Interpolator - Material-Agnostic Version
Real-space interpolation for binary alloys.

Loads from CHGCAR files and performs composition-weighted interpolation.
NOW FULLY MATERIAL-AGNOSTIC!

Author: Razasyattar M. N. && Abdullah Hasan Dafa
"""

import numpy as np
from pathlib import Path
from typing import Tuple, Optional
from dataclasses import dataclass

try:
    from pymatgen.core import Structure
    from pymatgen.io.vasp.outputs import Chgcar
    PYMATGEN_AVAILABLE = True
except ImportError:
    PYMATGEN_AVAILABLE = False
    raise ImportError("pymatgen required. Install: pip install pymatgen")

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ChargeDensityData:
    """Charge density grid data"""
    data: np.ndarray  # 3D grid (nx, ny, nz)
    structure: Structure
    grid_shape: Tuple[int, int, int]


class ChargeDensityInterpolator:
    """
    Interpolates charge density between two binary materials.
    
    NOW FULLY MATERIAL-AGNOSTIC!
    Works with any binary material pair (GaAs/AlAs, GaAs/InAs, etc.)
    
    Uses weighted linear interpolation in real space.
    """

    def __init__(self,
                 material1_chgcar_path: Optional[Path] = None,
                 material2_chgcar_path: Optional[Path] = None,
                 material1_structure: Optional[Structure] = None,
                 material2_structure: Optional[Structure] = None,
                 material1_name: str = "Material1",
                 material2_name: str = "Material2"):
        """
        Initialize interpolator for any binary material pair.

        Args:
            material1_chgcar_path: Path to material1 CHGCAR file
            material2_chgcar_path: Path to material2 CHGCAR file
            material1_structure: Material1 structure (if not loading from CHGCAR)
            material2_structure: Material2 structure (if not loading from CHGCAR)
            material1_name: Name of first material (for logging)
            material2_name: Name of second material (for logging)
        """
        self.material1_name = material1_name
        self.material2_name = material2_name
        
        # Load charge densities
        self.density1, self.structure1 = self._load_charge_density(
            material1_chgcar_path, material1_structure, material1_name
        )
        self.density2, self.structure2 = self._load_charge_density(
            material2_chgcar_path, material2_structure, material2_name
        )

        # Ensure compatible grids
        if self.density1.shape != self.density2.shape:
            logger.warning(
                f"Grid mismatch: {material1_name} {self.density1.shape} vs "
                f"{material2_name} {self.density2.shape}. Regridding {material2_name}..."
            )
            self.density2 = self._regrid(
                self.density2, self.density1.shape
            )

        self.grid_shape = self.density1.shape
        logger.info(f"Initialized charge density interpolator")
        logger.info(f"  Materials: {material1_name} ↔ {material2_name}")
        logger.info(f"  Grid shape: {self.grid_shape}")

    def _load_charge_density(self,
                            chgcar_path: Optional[Path],
                            structure: Optional[Structure],
                            label: str) -> Tuple[np.ndarray, Structure]:
        """
        Load charge density from CHGCAR file.

        Args:
            chgcar_path: Path to CHGCAR file
            structure: Fallback structure
            label: Material label for logging

        Returns:
            (density_array, structure)
        """
        if chgcar_path and chgcar_path.exists():
            logger.info(f"Loading {label} charge density from {chgcar_path}")
            try:
                chgcar = Chgcar.from_file(str(chgcar_path))
                density = chgcar.data['total']
                structure = chgcar.structure
                logger.info(f"Loaded {label}: shape={density.shape}")
                return density, structure
            except Exception as e:
                logger.error(f"Failed to load CHGCAR for {label}: {e}")
                raise

        # Fallback: no CHGCAR available
        if structure is None:
            raise ValueError(
                f"No CHGCAR file or structure provided for {label}"
            )
        
        logger.warning(
            f"No CHGCAR file for {label}, using dummy charge density"
        )
        # Create dummy density (uniform grid)
        dummy_density = np.ones((60, 60, 60))
        return dummy_density, structure

    def _regrid(self, density: np.ndarray,
               target_shape: Tuple[int, int, int]) -> np.ndarray:
        """
        Regrid density to target shape using scipy zoom.

        Args:
            density: Input density array
            target_shape: Target grid shape

        Returns:
            Regridded density array
        """
        try:
            from scipy.ndimage import zoom
            zoom_factors = np.array(target_shape) / np.array(density.shape)
            regridded = zoom(density, zoom_factors, order=1)
            logger.info(f"Regridded from {density.shape} to {regridded.shape}")
            return regridded
        except ImportError:
            logger.error("scipy required for regridding. Install: pip install scipy")
            raise

    def interpolate(self, x: float,
                   target_structure: Structure) -> ChargeDensityData:
        """
        Interpolate charge density for composition x.

        Args:
            x: Composition variable (0.0 to 1.0)
            target_structure: Target alloy structure

        Returns:
            ChargeDensityData with interpolated density
        """
        # Linear interpolation: ρ(x) = (1-x)ρ₁ + x·ρ₂
        interpolated_density = (
            (1 - x) * self.density1 + x * self.density2
        )

        logger.debug(
            f"Interpolated charge density for x={x:.3f}, "
            f"range: [{interpolated_density.min():.3f}, "
            f"{interpolated_density.max():.3f}]"
        )

        return ChargeDensityData(
            data=interpolated_density,
            structure=target_structure,
            grid_shape=self.grid_shape
        )

    @staticmethod
    def from_material_pair(material1_name: str, 
                          material2_name: str,
                          data_dir: Path) -> 'ChargeDensityInterpolator':
        """
        Create interpolator from material names using material registry.

        Args:
            material1_name: First material name (e.g., 'GaAs')
            material2_name: Second material name (e.g., 'AlAs')
            data_dir: Base data directory

        Returns:
            ChargeDensityInterpolator instance
        """
        from .constants import get_material_registry
        
        registry = get_material_registry()
        mat1 = registry.get_material(material1_name)
        mat2 = registry.get_material(material2_name)
        
        data_dir = Path(data_dir)
        
        chgcar1 = data_dir / mat1.mp_id / f"{mat1.mp_id}_CHGCAR.vasp"
        chgcar2 = data_dir / mat2.mp_id / f"{mat2.mp_id}_CHGCAR.vasp"

        if not chgcar1.exists():
            raise FileNotFoundError(f"{material1_name} CHGCAR not found: {chgcar1}")
        if not chgcar2.exists():
            raise FileNotFoundError(f"{material2_name} CHGCAR not found: {chgcar2}")

        return ChargeDensityInterpolator(
            material1_chgcar_path=chgcar1,
            material2_chgcar_path=chgcar2,
            material1_name=material1_name,
            material2_name=material2_name
        )

    @staticmethod
    def from_data_dir(data_dir: Path, 
                     material1_name: str = "GaAs",
                     material2_name: str = "AlAs") -> 'ChargeDensityInterpolator':
        """
        Create interpolator from data directory (backwards compatible).

        Args:
            data_dir: Base data directory
            material1_name: First material name (default: 'GaAs')
            material2_name: Second material name (default: 'AlAs')

        Returns:
            ChargeDensityInterpolator instance
        """
        return ChargeDensityInterpolator.from_material_pair(
            material1_name, material2_name, data_dir
        )


# ============================================================================
# EXPORT UTILITIES
# ============================================================================

def export_chgcar(charge_data: ChargeDensityData, output_path: Path):
    """
    Export charge density to VASP CHGCAR format.

    Args:
        charge_data: ChargeDensityData to export
        output_path: Output file path
    """
    # Create Chgcar object
    chgcar = Chgcar(
        structure=charge_data.structure,
        data={'total': charge_data.data}
    )
    
    chgcar.write_file(str(output_path))
    logger.info(f"Exported CHGCAR to {output_path}")


def export_cube(charge_data: ChargeDensityData, output_path: Path):
    """
    Export charge density to Gaussian Cube format.

    Args:
        charge_data: ChargeDensityData to export
        output_path: Output file path
    """
    structure = charge_data.structure
    density = charge_data.data
    nx, ny, nz = density.shape

    with open(output_path, 'w') as f:
        # Header
        f.write("Charge density interpolation\n")
        f.write("Generated by charge_density_interpolator.py\n")
        
        # Number of atoms and origin
        f.write(f"{len(structure)} 0.0 0.0 0.0\n")
        
        # Voxel vectors (in Bohr)
        ANGSTROM_TO_BOHR = 1.88972612
        lattice = structure.lattice.matrix
        voxel_x = lattice[0] / nx * ANGSTROM_TO_BOHR
        voxel_y = lattice[1] / ny * ANGSTROM_TO_BOHR
        voxel_z = lattice[2] / nz * ANGSTROM_TO_BOHR
        
        f.write(f"{nx} {voxel_x[0]:.6f} {voxel_x[1]:.6f} {voxel_x[2]:.6f}\n")
        f.write(f"{ny} {voxel_y[0]:.6f} {voxel_y[1]:.6f} {voxel_y[2]:.6f}\n")
        f.write(f"{nz} {voxel_z[0]:.6f} {voxel_z[1]:.6f} {voxel_z[2]:.6f}\n")
        
        # Atoms
        for site in structure:
            atomic_num = site.specie.Z
            pos = site.coords * ANGSTROM_TO_BOHR
            f.write(f"{atomic_num} 0.0 {pos[0]:.6f} {pos[1]:.6f} {pos[2]:.6f}\n")
        
        # Density data
        for ix in range(nx):
            for iy in range(ny):
                for iz in range(nz):
                    f.write(f"{density[ix, iy, iz]:.5e}\n")
                    if (iz + 1) % 6 == 0:
                        f.write("\n")

    logger.info(f"Exported Cube file to {output_path}")


# ============================================================================
# VISUALIZATION (Optional - requires matplotlib)
# ============================================================================

def visualize_slice(charge_data: ChargeDensityData,
                   plane: str = 'xy',
                   slice_index: Optional[int] = None,
                   output_path: Optional[Path] = None,
                   show: bool = False):
    """
    Visualize 2D slice of charge density.

    Args:
        charge_data: ChargeDensityData to visualize
        plane: 'xy', 'xz', or 'yz'
        slice_index: Index of slice (default: middle)
        output_path: Save path (optional)
        show: Show plot interactively
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.error("matplotlib required for visualization")
        return

    data = charge_data.data
    nx, ny, nz = data.shape

    # Get slice
    if plane == 'xy':
        idx = slice_index if slice_index else nz // 2
        slice_data = data[:, :, idx]
        xlabel, ylabel = 'X', 'Y'
    elif plane == 'xz':
        idx = slice_index if slice_index else ny // 2
        slice_data = data[:, idx, :]
        xlabel, ylabel = 'X', 'Z'
    elif plane == 'yz':
        idx = slice_index if slice_index else nx // 2
        slice_data = data[idx, :, :]
        xlabel, ylabel = 'Y', 'Z'
    else:
        raise ValueError(f"Invalid plane: {plane}")

    # Plot
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(slice_data.T, origin='lower', cmap='viridis',
                   interpolation='bilinear')
    plt.colorbar(im, label='Charge Density (e/Ų)', ax=ax)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(f'Charge Density Slice ({plane} plane, index={idx})')

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved visualization to {output_path}")
    
    if show:
        plt.show()
    else:
        plt.close()


# ============================================================================
# HIGH-LEVEL API
# ============================================================================

def interpolate_and_export(
    x: float,
    structure: Structure,
    output_dir: Path,
    alloy_name: str = "AlGaAs",
    material1_name: str = "GaAs",
    material2_name: str = "AlAs",
    data_dir: Path = Path("data"),
    formats: list = ['chgcar']
):
    """
    Convenience function: interpolate and export charge density.
    
    NOW MATERIAL-AGNOSTIC!

    Args:
        x: Composition variable
        structure: Target structure
        output_dir: Output directory
        alloy_name: Name of alloy system (e.g., 'AlGaAs', 'InGaAs')
        material1_name: First material name (default: 'GaAs')
        material2_name: Second material name (default: 'AlAs')
        data_dir: Base data directory with CHGCAR files
        formats: Export formats ['chgcar', 'cube', 'png']
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create interpolator using material names
    interpolator = ChargeDensityInterpolator.from_material_pair(
        material1_name, material2_name, data_dir
    )

    # Interpolate
    charge_data = interpolator.interpolate(x, structure)

    # Export with material-agnostic naming
    base_name = f"{alloy_name}_x{x:.3f}_chgcar"

    if 'chgcar' in formats:
        export_chgcar(charge_data, output_dir / f"{base_name}.vasp")

    if 'cube' in formats:
        export_cube(charge_data, output_dir / f"{base_name}.cube")

    if 'png' in formats:
        for plane in ['xy', 'xz', 'yz']:
            visualize_slice(
                charge_data,
                plane=plane,
                output_path=output_dir / f"{base_name}_slice_{plane}.png"
            )

    logger.info(f"Exported charge density for {alloy_name} x={x:.3f}")
    return charge_data


# ============================================================================
# BACKWARDS COMPATIBILITY
# ============================================================================

# Keep old parameter names for backwards compatibility
def from_data_dir_legacy(data_dir: Path) -> ChargeDensityInterpolator:
    """
    Legacy function for backwards compatibility with hardcoded GaAs/AlAs.
    
    Use from_material_pair() for new code.
    """
    return ChargeDensityInterpolator.from_data_dir(data_dir, "GaAs", "AlAs")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    from ..utils.logger import setup_logging
    
    # Setup logging
    setup_logging(verbose=True)

    print("Example 1: AlGaAs (backwards compatible)")
    interpolator = ChargeDensityInterpolator.from_material_pair(
        "GaAs", "AlAs", Path("data")
    )
    
    # Example structure
    from pymatgen.core import Lattice
    lattice = Lattice.cubic(5.65)
    structure = Structure(
        lattice,
        ["Al", "Ga", "As", "As"],
        [[0, 0, 0], [0.5, 0.5, 0.5], [0.25, 0.25, 0.25], [0.75, 0.75, 0.75]]
    )

    # Interpolate for x=0.5
    charge_data = interpolator.interpolate(0.5, structure)
    print(f"Interpolated charge density for Al₀.₅Ga₀.₅As")
    print(f"Grid shape: {charge_data.grid_shape}")
    
    # Export
    output_dir = Path("data/outputs/charge_density")
    interpolate_and_export(
        x=0.5,
        structure=structure,
        output_dir=output_dir,
        alloy_name="AlGaAs",
        material1_name="GaAs",
        material2_name="AlAs",
        formats=['chgcar']
    )

    print("\nExample 2: InGaAs (if you add InAs material)")
    print("interpolator = ChargeDensityInterpolator.from_material_pair(")
    print("    'GaAs', 'InAs', Path('data')")
    print(")")

    logger.info("Charge density interpolation examples completed")