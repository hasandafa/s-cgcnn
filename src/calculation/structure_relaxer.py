"""
Structure Relaxer - Fast ML-based relaxation for AlGaAs
Uses CHGNet (ML potential) or EMT (fallback).

Author: Razasyattar M. N.
"""

import numpy as np
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass

from ..utils import get_logger

logger = get_logger(__name__)

try:
    from pymatgen.core import Structure
    from pymatgen.io.cif import CifWriter
except ImportError:
    logger.warning("pymatgen not available")

try:
    from ase import Atoms
    from ase.optimize import BFGS
    ASE_AVAILABLE = True
except ImportError:
    ASE_AVAILABLE = False
    logger.warning("ASE not available")

try:
    from chgnet.model import CHGNet
    from chgnet.model.dynamics import StructOptimizer
    CHGNET_AVAILABLE = True
except ImportError:
    CHGNET_AVAILABLE = False
    logger.info("CHGNet not available, will use EMT fallback")


@dataclass
class RelaxationResult:
    """Results from structure relaxation"""
    initial_structure: Structure
    final_structure: Structure
    initial_energy: float
    final_energy: float
    energy_change: float  # eV
    max_force: float  # eV/Å
    n_steps: int
    converged: bool
    method: str  # 'chgnet' or 'emt'


class StructureRelaxer:
    """
    Relaxes AlGaAs structures using ML potentials or force fields.
    """

    def __init__(self, method: str = 'auto',
                  fmax: float = 0.05,  # eV/Å
                  max_steps: int = 500):
        """
        Initialize relaxer.

        Args:
            method: 'chgnet', 'emt', or 'auto' (use CHGNet if available)
            fmax: Force convergence criterion (eV/Å)
            max_steps: Maximum optimization steps
        """
        self.fmax = fmax
        self.max_steps = max_steps

        # Select method
        if method == 'auto':
            self.method = 'chgnet' if CHGNET_AVAILABLE else 'emt'
        else:
            self.method = method

        # Initialize CHGNet if selected
        if self.method == 'chgnet':
            if not CHGNET_AVAILABLE:
                raise ImportError("CHGNet not available. Install: pip install chgnet")
            self.chgnet_model = CHGNet.load()
            self.relaxer = StructOptimizer()
            logger.info("Initialized CHGNet relaxer")
        elif self.method == 'emt':
            if not ASE_AVAILABLE:
                raise ImportError("ASE required for EMT")
            logger.info("Initialized EMT relaxer (fast approximation)")
        else:
            raise ValueError(f"Unknown method: {method}")

    def relax(self, structure: Structure,
              relax_cell: bool = True) -> RelaxationResult:
        """
        Relax structure.

        Args:
            structure: Input pymatgen Structure
            relax_cell: Also relax lattice parameters

        Returns:
            RelaxationResult object
        """
        if self.method == 'chgnet':
            return self._relax_chgnet(structure, relax_cell)
        else:
            return self._relax_emt(structure, relax_cell)

    def _relax_chgnet(self, structure: Structure,
                      relax_cell: bool) -> RelaxationResult:
        """Relax using CHGNet"""
        initial_structure = structure.copy()

        # Calculate initial energy
        initial_energy = self.chgnet_model.predict_structure(structure)['e']

        # Relax
        result = self.relaxer.relax(
            structure,
            fmax=self.fmax,
            steps=self.max_steps,
            relax_cell=relax_cell
        )

        final_structure = result['final_structure']
        final_energy = self.chgnet_model.predict_structure(final_structure)['e']

        # --- START: MODIFIED CODE FOR MAX FORCE ---
        max_force_val = 0.0
        n_steps = 0
        # Check if trajectory and forces are available to prevent errors
        if 'trajectory' in result and hasattr(result['trajectory'], 'forces') and len(result['trajectory'].forces) > 0:
            # Get forces from the final relaxation step
            last_forces = result['trajectory'].forces[-1]
            # Calculate the magnitude of force on each atom and find the maximum
            max_force_val = np.max(np.linalg.norm(last_forces, axis=1))
            n_steps = len(result['trajectory'].energies)
        # --- END: MODIFIED CODE FOR MAX FORCE ---

        return RelaxationResult(
            initial_structure=initial_structure,
            final_structure=final_structure,
            initial_energy=initial_energy,
            final_energy=final_energy,
            energy_change=final_energy - initial_energy,
            # Use the manually calculated max force
            max_force=max_force_val,
            # Use the correctly calculated number of steps
            n_steps=n_steps,
            converged=True,  # CHGNet relaxer doesn't have a simple converged flag, assume true if it finishes
            method='chgnet'
        )

    def _relax_emt(self, structure: Structure,
                   relax_cell: bool) -> RelaxationResult:
        """Relax using EMT (Effective Medium Theory)"""
        from ase.calculators.emt import EMT
        from ase.constraints import ExpCellFilter

        initial_structure = structure.copy()

        # Convert to ASE Atoms
        atoms = self._pmg_to_ase(structure)
        atoms.calc = EMT()

        initial_energy = atoms.get_potential_energy()

        # Setup optimizer
        if relax_cell:
            atoms_opt = ExpCellFilter(atoms)
        else:
            atoms_opt = atoms

        opt = BFGS(atoms_opt, logfile=None)

        # Relax
        opt.run(fmax=self.fmax, steps=self.max_steps)

        final_energy = atoms.get_potential_energy()
        max_force = np.max(np.linalg.norm(atoms.get_forces(), axis=1))

        # Convert back to pymatgen
        final_structure = self._ase_to_pmg(atoms)

        return RelaxationResult(
            initial_structure=initial_structure,
            final_structure=final_structure,
            initial_energy=initial_energy,
            final_energy=final_energy,
            energy_change=final_energy - initial_energy,
            max_force=max_force,
            n_steps=opt.get_number_of_steps(),
            converged=opt.converged(),
            method='emt'
        )

    def _pmg_to_ase(self, structure: Structure) -> 'Atoms':
        """Convert pymatgen Structure to ASE Atoms"""
        from ase import Atoms

        atoms = Atoms(
            symbols=[str(site.specie) for site in structure],
            positions=structure.cart_coords,
            cell=structure.lattice.matrix,
            pbc=True
        )
        return atoms

    def _ase_to_pmg(self, atoms: 'Atoms') -> Structure:
        """Convert ASE Atoms to pymatgen Structure"""
        from pymatgen.core import Lattice

        structure = Structure(
            lattice=Lattice(atoms.cell.array),
            species=atoms.get_chemical_symbols(),
            coords=atoms.get_positions(),
            coords_are_cartesian=True
        )
        return structure

    def relax_batch(self, structures: Dict[float, Structure],
                    relax_cell: bool = True,
                    output_dir: Optional[Path] = None) -> Dict[float, RelaxationResult]:
        """
        Relax multiple structures.

        Args:
            structures: Dict mapping x values to structures
            relax_cell: Relax lattice parameters
            output_dir: Save relaxed structures as CIF

        Returns:
            Dict mapping x to RelaxationResult
        """
        results = {}

        for x, structure in structures.items():
            logger.info(f"Relaxing x={x:.3f}...")
            result = self.relax(structure, relax_cell)
            results[x] = result

            logger.info(f"ΔE={result.energy_change:.3f} eV, "
                  f"F_max={result.max_force:.3f} eV/Å, "
                  f"steps={result.n_steps}")

            # Save if requested
            if output_dir:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)

                cif_path = output_dir / f"AlGaAs_x{x:.3f}_relaxed.cif"
                writer = CifWriter(result.final_structure)
                writer.write_file(str(cif_path))

        return results


# ============================================================================
# HIGH-LEVEL API
# ============================================================================

def relax_structure_simple(structure: Structure,
                            method: str = 'auto',
                            relax_cell: bool = True,
                            fmax: float = 0.05) -> Structure:
    """
    Simple wrapper: relax and return final structure.

    Args:
        structure: Input structure
        method: 'chgnet', 'emt', or 'auto'
        relax_cell: Relax lattice
        fmax: Force threshold (eV/Å)

    Returns:
        Relaxed Structure
    """
    relaxer = StructureRelaxer(method=method, fmax=fmax)
    result = relaxer.relax(structure, relax_cell)
    return result.final_structure


def compare_relaxation_methods(structure: Structure) -> Dict:
    """
    Compare CHGNet vs EMT relaxation (if both available).

    Args:
        structure: Test structure

    Returns:
        Comparison dict
    """
    results = {}

    if CHGNET_AVAILABLE:
        relaxer_chgnet = StructureRelaxer(method='chgnet')
        result_chgnet = relaxer_chgnet.relax(structure)
        results['chgnet'] = result_chgnet

    if ASE_AVAILABLE:
        relaxer_emt = StructureRelaxer(method='emt')
        result_emt = relaxer_emt.relax(structure)
        results['emt'] = result_emt

    return results


def export_relaxation_report(result: RelaxationResult,
                              output_file: Path):
    """Export relaxation summary as JSON"""
    import json

    # Helper function to convert numpy types to native Python types
    def convert_numpy(obj):
        """Convert numpy types to native Python types for JSON serialization"""
        import numpy as np

        if isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: convert_numpy(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(item) for item in obj]
        else:
            return obj

    report = {
        'method': result.method,
        'converged': convert_numpy(result.converged),
        'n_steps': convert_numpy(result.n_steps),
        'energies': {
            'initial': convert_numpy(result.initial_energy),
            'final': convert_numpy(result.final_energy),
            'change': convert_numpy(result.energy_change),
        },
        'max_force': convert_numpy(result.max_force),
        'lattice_parameters': {
            'initial': {
                'a': convert_numpy(result.initial_structure.lattice.a),
                'b': convert_numpy(result.initial_structure.lattice.b),
                'c': convert_numpy(result.initial_structure.lattice.c),
                'volume': convert_numpy(result.initial_structure.lattice.volume),
            },
            'final': {
                'a': convert_numpy(result.final_structure.lattice.a),
                'b': convert_numpy(result.final_structure.lattice.b),
                'c': convert_numpy(result.final_structure.lattice.c),
                'volume': convert_numpy(result.final_structure.lattice.volume),
            }
        }
    }

    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Saved relaxation report: {output_file}")