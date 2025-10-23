"""
Data Acquisition Module for AlGaAs Pipeline.

This module handles fetching materials data from Materials Project API,
including structures, band structures, and phonon data.
Supports parallel fetching and smart caching.

Author: Abdullah Hasan Dafa && Razasyattar M. N.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    from mp_api.client import MPRester
    MP_API_AVAILABLE = True
except ImportError:
    MP_API_AVAILABLE = False

from ..utils import get_config, get_cache_manager, validate_mp_api, get_logger
from .validator import DataValidator, ValidationResult

logger = get_logger(__name__)

if not MP_API_AVAILABLE:
    logger.warning("mp-api package not available. Install with: pip install mp-api")


@dataclass
class MaterialData:
    """Container for material data from Materials Project."""
    material_id: str
    formula: str
    structure: Optional[Dict[str, Any]] = None
    band_gap: Optional[float] = None
    is_gap_direct: Optional[bool] = None
    bandstructure: Optional[Dict[str, Any]] = None
    dos: Optional[Dict[str, Any]] = None
    phonon_bandstructure: Optional[Dict[str, Any]] = None
    phonon_dos: Optional[Dict[str, Any]] = None
    charge_density: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    fetch_timestamp: Optional[str] = None
    validation_result: Optional[ValidationResult] = None


class MaterialsProjectScraper:
    """Scraper for Materials Project data using official MPRester client."""

    def __init__(self, api_key: Optional[str] = None, cache_days: int = 7):
        """
        Initialize the scraper.

        Args:
            api_key: Materials Project API key (optional, loaded from key.env if not provided)
            cache_days: Number of days to consider cached data valid
        """
        if not MP_API_AVAILABLE:
            raise ImportError("mp-api package required. Install with: pip install mp-api")

        self.config = get_config()
        self.cache_manager = get_cache_manager()
        self.cache_days = cache_days

        # Load API key
        if api_key is None:
            key_file = Path("key.env")
            if key_file.exists():
                with open(key_file, 'r') as f:
                    content = f.read().strip()
                    if '=' in content:
                        _, api_key = content.split('=', 1)
                        api_key = api_key.strip()

        self.api_key = api_key
        self.mpr = None

        # Rate limiting
        self.request_delay = 0.2  # 200ms between requests to be safe
        self.last_request_time = 0

    def _rate_limit(self):
        """Implement rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()

    def __enter__(self):
        """Context manager entry."""
        self.mpr = MPRester(self.api_key).__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.mpr:
            self.mpr.__exit__(exc_type, exc_val, exc_tb)
        self.mpr = None

    def fetch_material_data(self, material_id: str,
                            fetch_structure: bool = True,
                            fetch_bandstructure: bool = True,
                            fetch_dos: bool = True,
                            fetch_phonon: bool = True,
                            fetch_charge_density: bool = True) -> MaterialData:
        """
        Fetch all requested data for a single material.

        Args:
            material_id: Materials Project ID
            fetch_structure: Whether to fetch crystal structure
            fetch_bandstructure: Whether to fetch electronic band structure
            fetch_dos: Whether to fetch electronic density of states
            fetch_phonon: Whether to fetch phonon data
            fetch_charge_density: Whether to fetch charge density

        Returns:
            MaterialData object with fetched data
        """
        cache_key = f"material_{material_id}"
        cached = self._check_cache(cache_key)
        if cached:
            logger.info(f"Using cached data for {material_id}")
            material_data = MaterialData(**cached)
            
            # Validate cached data if not already validated
            if not material_data.validation_result:
                try:
                    validator = DataValidator()
                    validation_result = validator.validate_material_data(material_data)
                    material_data.validation_result = validation_result
                    
                    if validation_result.anomalies:
                        logger.warning(f"Anomalies found for {material_id}: {validation_result.anomalies}")
                    if validation_result.warnings:
                        logger.warning(f"Warnings for {material_id}: {validation_result.warnings}")
                    if validation_result.is_valid:
                        logger.info(f"Data validation passed for {material_id}")
                except Exception as e:
                    logger.warning(f"Could not validate cached data for {material_id}: {e}")
            
            return material_data

        self._rate_limit()
        
        material_data = MaterialData(
            material_id=material_id,
            formula="Unknown",
            fetch_timestamp=datetime.now().isoformat()
        )

        try:
            # Fetch summary data (basic info + structure)
            summary = self.mpr.materials.summary.search(
                material_ids=[material_id],
                fields=["material_id", "formula_pretty", "structure", 
                        "band_gap", "is_gap_direct"]
            )
            
            if not summary or len(summary) == 0:
                logger.error(f"No data found for {material_id}")
                return material_data
            
            doc = summary[0]
            material_data.formula = doc.formula_pretty
            material_data.band_gap = doc.band_gap
            material_data.is_gap_direct = doc.is_gap_direct
            
            if fetch_structure and doc.structure:
                material_data.structure = doc.structure.as_dict()

            # Fetch electronic structure (band structure + DOS)
            # Use the convenience methods from MPRester
            if fetch_bandstructure:
                try:
                    bs = self.mpr.get_bandstructure_by_material_id(material_id)
                    if bs is not None:
                        material_data.bandstructure = bs.as_dict()
                        logger.info(f"Got band structure")
                except Exception as e:
                    logger.warning(f"Could not fetch band structure for {material_id}: {e}")
            
            if fetch_dos:
                try:
                    dos = self.mpr.get_dos_by_material_id(material_id)
                    if dos is not None:
                        material_data.dos = dos.as_dict()
                        logger.info(f"Got DOS")
                except Exception as e:
                    logger.warning(f"Could not fetch DOS for {material_id}: {e}")

            # Fetch phonon data
            if fetch_phonon:
                try:
                    phonon_docs = self.mpr.materials.phonon.search(
                        material_ids=[material_id]
                    )

                    if phonon_docs and len(phonon_docs) > 0:
                        phonon_doc = phonon_docs[0]

                        # Use correct attribute names: ph_bs and ph_dos
                        if hasattr(phonon_doc, 'ph_bs') and phonon_doc.ph_bs:
                            material_data.phonon_bandstructure = phonon_doc.ph_bs.as_dict()
                            logger.info(f"Got phonon band structure")

                        if hasattr(phonon_doc, 'ph_dos') and phonon_doc.ph_dos:
                            material_data.phonon_dos = phonon_doc.ph_dos.as_dict()
                            logger.info(f"Got phonon DOS")

                except Exception as e:
                    logger.warning(f"Could not fetch phonon data for {material_id}: {e}")

            # Fetch charge density data
            if fetch_charge_density:
                try:
                    chgcar = self.mpr.get_charge_density_from_material_id(material_id)
                    if chgcar is not None:
                        material_data.charge_density = chgcar.as_dict()
                        logger.info(f"Got charge density")
                except Exception as e:
                    logger.warning(f"Could not fetch charge density for {material_id}: {e}")

            # Add metadata
            material_data.metadata = {
                'api_version': 'mp-api',
                'has_structure': material_data.structure is not None,
                'has_bandstructure': material_data.bandstructure is not None,
                'has_dos': material_data.dos is not None,
                'has_phonon_bs': material_data.phonon_bandstructure is not None,
                'has_phonon_dos': material_data.phonon_dos is not None,
                'has_charge_density': material_data.charge_density is not None,
            }

            # Validate the data
            try:
                validator = DataValidator()
                validation_result = validator.validate_material_data(material_data)
                material_data.validation_result = validation_result

                # Log validation results
                if validation_result.anomalies:
                    logger.warning(f"Anomalies found for {material_id}: {validation_result.anomalies}")
                if validation_result.warnings:
                    logger.warning(f"Warnings for {material_id}: {validation_result.warnings}")
                if validation_result.is_valid:
                    logger.info(f"Data validation passed for {material_id}")
                else:
                    logger.error(f"Data validation failed for {material_id}")

            except Exception as e:
                logger.warning(f"Could not validate data for {material_id}: {e}")

            # Cache the result
            self._cache_data(cache_key, asdict(material_data))
            logger.info(f"Fetched data for {material_id} ({material_data.formula})")

        except Exception as e:
            logger.error(f"Failed to fetch data for {material_id}: {e}")

        return material_data

    def fetch_multiple_materials(self, material_ids: List[str],
                                  fetch_structure: bool = True,
                                  fetch_bandstructure: bool = True,
                                  fetch_dos: bool = True,
                                  fetch_phonon: bool = True,
                                  fetch_charge_density: bool = True,
                                  max_workers: int = 3) -> Dict[str, MaterialData]:
        """
        Fetch data for multiple materials in parallel.

        Args:
            material_ids: List of material IDs
            fetch_structure: Whether to fetch crystal structure
            fetch_bandstructure: Whether to fetch band structure
            fetch_dos: Whether to fetch DOS
            fetch_phonon: Whether to fetch phonon data
            fetch_charge_density: Whether to fetch charge density
            max_workers: Maximum number of parallel threads

        Returns:
            Dictionary mapping material_id to MaterialData
        """
        results = {}

        # Detect if we're running in Jupyter (IPython kernel)
        try:
            get_ipython()  # type: ignore
            is_jupyter = True
            logger.info("Jupyter environment detected - using sequential fetching")
        except NameError:
            is_jupyter = False

        # Use sequential execution in Jupyter to avoid ContextVar issues
        if is_jupyter:
            for mat_id in material_ids:
                try:
                    material_data = self.fetch_material_data(
                        mat_id,
                        fetch_structure,
                        fetch_bandstructure,
                        fetch_dos,
                        fetch_phonon,
                        fetch_charge_density
                    )
                    results[mat_id] = material_data
                except Exception as e:
                    logger.error(f"Failed to fetch data for {mat_id}: {e}")
        else:
            # Use parallel execution in normal Python environments
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_id = {
                    executor.submit(
                        self.fetch_material_data,
                        mat_id,
                        fetch_structure,
                        fetch_bandstructure,
                        fetch_dos,
                        fetch_phonon,
                        fetch_charge_density
                    ): mat_id
                    for mat_id in material_ids
                }

                for future in as_completed(future_to_id):
                    material_id = future_to_id[future]
                    try:
                        material_data = future.result()
                        results[material_id] = material_data
                    except Exception as e:
                        logger.error(f"Failed to fetch data for {material_id}: {e}")

        return results

    def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check if data is cached and still valid."""
        if self.cache_manager.is_cached(cache_key, self.cache_days):
            entry = self.cache_manager.get_entry(cache_key)
            if entry and entry.file_path and Path(entry.file_path).exists():
                try:
                    with open(entry.file_path, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load cache for {cache_key}: {e}")
        return None

    def _cache_data(self, cache_key: str, data: Any):
        """Cache data to disk."""
        cache_dir = Path(self.config.get('paths.cache_dir', 'cache/'))
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{cache_key}.json"

        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            self.cache_manager.add_entry(
                key=cache_key,
                file_path=str(cache_file),
                metadata={'timestamp': datetime.now().isoformat()}
            )
        except Exception as e:
            logger.warning(f"Failed to cache data for {cache_key}: {e}")

    def save_material_data(self, material_data: MaterialData, output_dir: str = "data/",
                           export_cif: bool = True, export_provenance: bool = True,
                           export_charge_density: bool = True):
        """
        Save material data to multiple formats.

        Args:
            material_data: MaterialData object to save
            output_dir: Output directory
            export_cif: Whether to export structure as CIF
            export_provenance: Whether to export provenance metadata
            export_charge_density: Whether to export charge density as CHGCAR
        """
        output_path = Path(output_dir) / material_data.material_id
        output_path.mkdir(parents=True, exist_ok=True)

        # Save complete data as single JSON
        data_path = output_path / "material_data.json"
        with open(data_path, 'w') as f:
            json.dump(asdict(material_data), f, indent=2, default=str)

        # Export CIF if requested and structure exists
        if export_cif and material_data.structure:
            try:
                validator = DataValidator()
                cif_path = output_path / f"{material_data.material_id}.cif"
                if validator.export_cif(material_data, cif_path):
                    logger.info(f"Exported CIF for {material_data.material_id}")
                else:
                    logger.warning(f"Failed to export CIF for {material_data.material_id}")
            except Exception as e:
                logger.warning(f"CIF export failed for {material_data.material_id}: {e}")

        # Export charge density if requested and available
        if export_charge_density and material_data.charge_density:
            try:
                from pymatgen.io.vasp.outputs import Chgcar
                chgcar = Chgcar.from_dict(material_data.charge_density)
                chgcar_path = output_path / f"{material_data.material_id}_CHGCAR.vasp"
                chgcar.write_file(str(chgcar_path))
                logger.info(f"Exported charge density for {material_data.material_id}")
            except Exception as e:
                logger.warning(f"Charge density export failed for {material_data.material_id}: {e}")

        # Export provenance metadata if requested
        if export_provenance and material_data.validation_result:
            try:
                validator = DataValidator()
                provenance_path = output_path / "provenance.json"
                validator.export_provenance(material_data, material_data.validation_result, provenance_path)
                logger.info(f"Exported provenance for {material_data.material_id}")
            except Exception as e:
                logger.warning(f"Provenance export failed for {material_data.material_id}: {e}")

        logger.info(f"Saved data for {material_data.material_id} to {output_path}")


def scrape_binary_compounds(config_file: str = "config.yaml") -> Dict[str, MaterialData]:
    """
    Scrape data for binary compounds defined in config.

    Args:
        config_file: Path to configuration file

    Returns:
        Dictionary of material data
    """
    # Validate API first
    valid, msg = validate_mp_api()
    if not valid:
        raise RuntimeError(f"API validation failed: {msg}")

    config = get_config()
    system_config = config.get('system', {})

    # Get binary compounds from config
    binary_compounds = system_config.get('binary_compounds', [])
    if not binary_compounds:
        raise ValueError("No binary compounds defined in configuration")

    material_ids = [compound['mp_id'] for compound in binary_compounds]

    # Initialize scraper with context manager
    with MaterialsProjectScraper() as scraper:
        logger.info(f"Fetching data for {len(material_ids)} binary compounds...")
        material_data = scraper.fetch_multiple_materials(
            material_ids,
            fetch_structure=True,
            fetch_bandstructure=True,
            fetch_dos=True,
            fetch_phonon=True,
            fetch_charge_density=True
        )

        # Save data
        data_dir = config.get('paths.data_dir', 'data/')
        for material_datum in material_data.values():
            scraper.save_material_data(material_datum, data_dir)

    return material_data


if __name__ == "__main__":
    # Example usage
    try:
        results = scrape_binary_compounds()
        logger.info(f"\nSuccessfully scraped data for {len(results)} materials")

        for material_id, data in results.items():
            logger.info(f"- {material_id}: {data.formula} (Eg={data.band_gap} eV)")

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        exit(1)