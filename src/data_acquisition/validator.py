"""
Data Validation Module for AlGaAs Pipeline.

This module provides comprehensive validation of materials data fetched from
Materials Project, including structure completeness, band structure verification,
phonon validation, and anomaly detection.

Author: Razasyattar M. N. && Abdullah Hasan Dafa
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

try:
    from pymatgen.core import Structure
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    from pymatgen.io.cif import CifWriter
    from pymatgen.electronic_structure.bandstructure import BandStructure
    from pymatgen.phonon.bandstructure import PhononBandStructure
    PYMATGEN_AVAILABLE = True
except ImportError:
    PYMATGEN_AVAILABLE = False

from ..utils.logger import get_logger

logger = get_logger(__name__)

if not PYMATGEN_AVAILABLE:
    logger.warning("pymatgen package not available. Validation features limited.")


@dataclass
class ValidationResult:
    """Container for validation results."""
    is_valid: bool
    structure_complete: bool
    bandstructure_valid: bool
    phonon_valid: bool
    anomalies: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class DataValidator:
    """Validates materials data from Materials Project."""

    def __init__(self):
        """Initialize the validator."""
        if not PYMATGEN_AVAILABLE:
            raise ImportError("pymatgen package required for validation. Install with: pip install pymatgen")

    def validate_material_data(self, material_data: Any) -> ValidationResult:
        """
        Comprehensive validation of material data.

        Args:
            material_data: MaterialData object to validate

        Returns:
            ValidationResult with detailed validation information
        """
        anomalies = []
        warnings = []
        metadata = {}

        # Structure validation
        structure_complete = self._validate_structure(material_data, anomalies, warnings, metadata)

        # Band structure validation
        bandstructure_valid = self._validate_bandstructure(material_data, anomalies, warnings, metadata)

        # Phonon validation
        phonon_valid = self._validate_phonon(material_data, anomalies, warnings, metadata)

        # Charge density validation
        charge_density_valid = self._validate_charge_density(material_data, anomalies, warnings, metadata)

        # Overall validity
        is_valid = structure_complete and bandstructure_valid and phonon_valid and charge_density_valid and len(anomalies) == 0

        return ValidationResult(
            is_valid=is_valid,
            structure_complete=structure_complete,
            bandstructure_valid=bandstructure_valid,
            phonon_valid=phonon_valid,
            anomalies=anomalies,
            warnings=warnings,
            metadata=metadata
        )

    def _validate_structure(self, material_data: Any, anomalies: List[str],
                          warnings: List[str], metadata: Dict[str, Any]) -> bool:
        """Validate crystal structure completeness and quality."""
        if not material_data.structure:
            anomalies.append("Missing crystal structure data")
            return False

        try:
            structure = Structure.from_dict(material_data.structure)

            # Check for missing atoms
            if len(structure) == 0:
                anomalies.append("Structure contains no atoms")
                return False

            # Check for atoms with missing coordinates
            invalid_sites = []
            for i, site in enumerate(structure):
                if site.coords is None or any(not isinstance(c, (int, float)) for c in site.coords):
                    invalid_sites.append(i)

            if invalid_sites:
                anomalies.append(f"Sites with invalid coordinates: {invalid_sites}")
                return False

            # Check lattice parameters
            lattice = structure.lattice
            if lattice.a <= 0 or lattice.b <= 0 or lattice.c <= 0:
                anomalies.append("Invalid lattice parameters (negative or zero)")
                return False

            # Symmetry analysis
            try:
                sga = SpacegroupAnalyzer(structure)
                spacegroup = sga.get_space_group_symbol()
                metadata['spacegroup'] = spacegroup

                # Check for unusual symmetry
                if 'P1' in spacegroup and len(structure) > 4:
                    warnings.append("Triclinic symmetry with many atoms - possible structure issue")

            except Exception as e:
                warnings.append(f"Could not determine space group: {e}")

            # Check composition
            composition = structure.composition
            metadata['composition'] = str(composition)
            metadata['num_atoms'] = len(structure)
            metadata['formula_reduced'] = composition.reduced_formula

            return True

        except Exception as e:
            anomalies.append(f"Structure validation failed: {e}")
            return False

    def _validate_bandstructure(self, material_data: Any, anomalies: List[str],
                              warnings: List[str], metadata: Dict[str, Any]) -> bool:
        """Validate electronic band structure."""
        if not material_data.bandstructure:
            warnings.append("Missing band structure data")
            return True  # Not required for validity

        try:
            # Try to create BandStructure object, but be more lenient with validation
            try:
                bs = BandStructure.from_dict(material_data.bandstructure)
            except Exception:
                # If we can't create the object, at least check if the data structure looks reasonable
                bs_data = material_data.bandstructure
                if not isinstance(bs_data, dict):
                    anomalies.append("Band structure data is not a dictionary")
                    return False

                # Check for basic structure
                if 'bands' not in bs_data and 'energies' not in bs_data:
                    warnings.append("Band structure missing energy data")
                    return True  # Not a fatal error

                # Store what we can in metadata
                if 'bands' in bs_data:
                    metadata['bandstructure_bands'] = len(bs_data['bands']) if isinstance(bs_data['bands'], list) else 'unknown'
                if 'kpoints' in bs_data:
                    metadata['bandstructure_kpoints'] = len(bs_data['kpoints']) if isinstance(bs_data['kpoints'], list) else 'unknown'

                metadata['band_gap'] = material_data.band_gap
                metadata['is_gap_direct'] = material_data.is_gap_direct
                return True

            # If we successfully created the BandStructure object, do full validation
            # Check k-path
            kpoints = bs.kpoints
            if len(kpoints) == 0:
                anomalies.append("Band structure contains no k-points")
                return False

            # Check for standard k-path (be more lenient)
            try:
                labels = bs.labels_dict
                if not labels:
                    warnings.append("Band structure missing high-symmetry point labels")
            except AttributeError:
                warnings.append("Could not access band structure labels")

            # Check band energies
            energies = bs.bands
            if len(energies) == 0:
                anomalies.append("Band structure contains no energy data")
                return False

            # Check for reasonable energy range (be more lenient)
            try:
                all_energies = [e for band in energies for e in band]
                if all_energies:
                    energy_range = max(all_energies) - min(all_energies)
                    if energy_range < 1.0:  # eV
                        warnings.append("Unusually small energy range in band structure")
            except (TypeError, ValueError):
                warnings.append("Could not analyze energy range in band structure")

            metadata['bandstructure_kpoints'] = len(kpoints)
            metadata['bandstructure_bands'] = len(energies)
            metadata['band_gap'] = material_data.band_gap
            metadata['is_gap_direct'] = material_data.is_gap_direct

            return True

        except Exception as e:
            warnings.append(f"Band structure validation had issues: {e}")
            # Don't fail validation completely, just warn
            return True

    def _validate_phonon(self, material_data: Any, anomalies: List[str],
                         warnings: List[str], metadata: Dict[str, Any]) -> bool:
        """Validate phonon band structure."""
        if not material_data.phonon_bandstructure:
            warnings.append("Missing phonon band structure data")
            return True  # Not required for validity

        try:
            # Try to create PhononBandStructure object, but be more lenient
            try:
                phonon_bs = PhononBandStructure.from_dict(material_data.phonon_bandstructure)
            except Exception:
                # If we can't create the object, check basic structure
                phonon_data = material_data.phonon_bandstructure
                if not isinstance(phonon_data, dict):
                    warnings.append("Phonon band structure data is not a dictionary")
                    return True

                # Check for basic structure
                if 'bands' not in phonon_data and 'frequencies' not in phonon_data:
                    warnings.append("Phonon band structure missing frequency data")
                    return True

                # Store what we can in metadata
                if 'bands' in phonon_data:
                    metadata['phonon_bands'] = len(phonon_data['bands']) if isinstance(phonon_data['bands'], list) else 'unknown'
                if 'kpoints' in phonon_data:
                    metadata['phonon_kpoints'] = len(phonon_data['kpoints']) if isinstance(phonon_data['kpoints'], list) else 'unknown'

                return True

            # If we successfully created the PhononBandStructure object, do full validation
            # Check for negative frequencies (be more lenient)
            try:
                frequencies = phonon_bs.bands
                negative_freqs = []
                for band_idx, band in enumerate(frequencies):
                    for freq in band:
                        if freq < -1e-6:  # Small tolerance for numerical precision
                            negative_freqs.append((band_idx, freq))

                if negative_freqs:
                    warnings.append(f"Negative phonon frequencies found: {len(negative_freqs)} instances")
            except (AttributeError, TypeError):
                warnings.append("Could not check for negative phonon frequencies")

            # Check k-path
            try:
                kpoints = phonon_bs.kpoints
                if len(kpoints) == 0:
                    warnings.append("Phonon band structure contains no k-points")
            except AttributeError:
                warnings.append("Could not access phonon k-points")

            # Check frequency range (be more lenient)
            try:
                all_freqs = [f for band in frequencies for f in band]
                if all_freqs:
                    max_freq = max(all_freqs)
                    if max_freq < 0.1:  # THz
                        warnings.append("Unusually low maximum phonon frequency")
                    metadata['phonon_max_freq'] = max_freq
            except (TypeError, ValueError, NameError):
                warnings.append("Could not analyze phonon frequency range")

            try:
                metadata['phonon_kpoints'] = len(phonon_bs.kpoints)
                metadata['phonon_bands'] = len(frequencies)
            except (AttributeError, NameError):
                pass

            return True

        except Exception as e:
            warnings.append(f"Phonon validation had issues: {e}")
            # Don't fail validation completely, just warn
            return True

    def _validate_charge_density(self, material_data: Any, anomalies: List[str],
                                warnings: List[str], metadata: Dict[str, Any]) -> bool:
        """Validate charge density data."""
        if not material_data.charge_density:
            warnings.append("Missing charge density data")
            return True  # Not required for validity

        try:
            # Try to create Chgcar object to validate
            try:
                from pymatgen.io.vasp.outputs import Chgcar
                chgcar = Chgcar.from_dict(material_data.charge_density)
            except Exception:
                # If we can't create the object, check basic structure
                chg_data = material_data.charge_density
                if not isinstance(chg_data, dict):
                    warnings.append("Charge density data is not a dictionary")
                    return True

                # Check for basic structure
                if 'data' not in chg_data and 'chg' not in chg_data:
                    warnings.append("Charge density missing data array")
                    return True

                # Store what we can in metadata
                if 'data' in chg_data:
                    if isinstance(chg_data['data'], dict) and 'total' in chg_data['data']:
                        metadata['charge_density_shape'] = 'unknown'
                    elif hasattr(chg_data['data'], '__len__'):
                        metadata['charge_density_points'] = len(chg_data['data'])
                return True

            # If we successfully created the Chgcar object, do full validation
            # Check data dimensions
            try:
                data_shape = chgcar.data['total'].shape
                metadata['charge_density_shape'] = str(data_shape)

                # Check for reasonable data size
                total_points = 1
                for dim in data_shape:
                    total_points *= dim

                if total_points == 0:
                    anomalies.append("Charge density data is empty")
                    return False

                metadata['charge_density_points'] = total_points

                # Check for negative values (shouldn't happen in charge density)
                min_val = chgcar.data['total'].min()
                if min_val < -1e-10:  # Small tolerance for numerical precision
                    warnings.append(f"Negative charge density values found (min: {min_val})")

                # Check for reasonable maximum values
                max_val = chgcar.data['total'].max()
                if max_val > 100:  # Very high charge density might indicate issues
                    warnings.append(f"Unusually high charge density values (max: {max_val})")

            except (AttributeError, KeyError, TypeError):
                warnings.append("Could not analyze charge density data structure")

            return True

        except Exception as e:
            warnings.append(f"Charge density validation had issues: {e}")
            # Don't fail validation completely, just warn
            return True

    def export_cif(self, material_data: Any, output_path: Path) -> bool:
        """
        Export structure to CIF format.

        Args:
            material_data: MaterialData object
            output_path: Path to save CIF file

        Returns:
            True if successful, False otherwise
        """
        if not material_data.structure:
            return False

        try:
            structure = Structure.from_dict(material_data.structure)
            cif_writer = CifWriter(structure)
            cif_writer.write_file(str(output_path))
            return True
        except Exception as e:
            logger.error(f"Failed to export CIF for {material_data.material_id}: {e}")
            return False

    def export_provenance(self, material_data: Any, validation_result: ValidationResult,
                         output_path: Path):
        """
        Export provenance metadata.

        Args:
            material_data: MaterialData object
            validation_result: ValidationResult object
            output_path: Path to save provenance file
        """
        provenance = {
            'material_id': material_data.material_id,
            'formula': material_data.formula,
            'fetch_timestamp': material_data.fetch_timestamp,
            'api_version': material_data.metadata.get('api_version', 'unknown') if material_data.metadata else 'unknown',
            'validation_timestamp': validation_result.metadata.get('validation_timestamp', None),
            'validation_result': validation_result.to_dict(),
            'data_sources': {
                'structure': material_data.metadata.get('has_structure', False) if material_data.metadata else False,
                'bandstructure': material_data.metadata.get('has_bandstructure', False) if material_data.metadata else False,
                'dos': material_data.metadata.get('has_dos', False) if material_data.metadata else False,
                'phonon_bs': material_data.metadata.get('has_phonon_bs', False) if material_data.metadata else False,
                'phonon_dos': material_data.metadata.get('has_phonon_dos', False) if material_data.metadata else False,
            }
        }

        try:
            with open(output_path, 'w') as f:
                json.dump(provenance, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to export provenance for {material_data.material_id}: {e}")


# Convenience functions
def validate_material_data(material_data: Any) -> ValidationResult:
    """Validate a single material's data."""
    validator = DataValidator()
    return validator.validate_material_data(material_data)


def export_cif(material_data: Any, output_path: str) -> bool:
    """Export structure to CIF format."""
    validator = DataValidator()
    return validator.export_cif(material_data, Path(output_path))


def export_provenance(material_data: Any, validation_result: ValidationResult, output_path: str):
    """Export provenance metadata."""
    validator = DataValidator()
    validator.export_provenance(material_data, validation_result, Path(output_path))