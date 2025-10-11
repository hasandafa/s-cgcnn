"""
s-CGCNN v0.1.1 - Main Pipeline Execution Script

Enhanced with dual data source support:
- Mode 1: Literature-based (experimental values from ioffe.ru)
- Mode 2: MP-API-based (DFT-calculated values from Materials Project)

Usage:
    python run_version_0.1.1.py [--mode literature|mp_api] [--config path/to/config.yaml]

Author: Abdullah Hasan Dafa
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import yaml
import json

from src.data_acquisition import MPFetcher, StructureInterpolator
from src.data_acquisition import create_fetcher_from_config, create_interpolator_from_config
from src.utils import setup_logger, constants


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def setup_directories(config: dict):
    """Create necessary output directories"""
    output = config.get("output", {})
    
    dirs_to_create = [
        output.get("structures_dir", "data/structures"),
        output.get("cif_dir", "data/structures/cif"),
        output.get("metadata_dir", "data/structures/metadata"),
        output.get("results_dir", "results"),
        output.get("logs_dir", "logs"),
    ]
    
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def print_header():
    """Print pipeline header"""
    print("=" * 80)
    print("  s-CGCNN v0.1.1 - AlGaAs Structure Generation & Property Calculation")
    print("=" * 80)
    print(f"  Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()


def print_config_summary(config: dict):
    """Print configuration summary"""
    mode = config.get("interpolation", {}).get("mode", "literature")
    x_min = config.get("structure_interpolation", {}).get("composition", {}).get("x_min", 0.0)
    x_max = config.get("structure_interpolation", {}).get("composition", {}).get("x_max", 1.0)
    x_step = config.get("structure_interpolation", {}).get("composition", {}).get("x_step", 0.025)
    
    num_compositions = int((x_max - x_min) / x_step) + 1
    
    print("CONFIGURATION:")
    print(f"  Data Source Mode: {mode.upper()}")
    print(f"  Composition Range: x={x_min:.3f} to x={x_max:.3f} (step={x_step})")
    print(f"  Expected Structures: {num_compositions}")
    
    if mode == "mp_api":
        correction_config = config.get("interpolation", {}).get("mp_bandgap_correction", {})
        if correction_config.get("enabled", True):
            factor = correction_config.get("correction_factor", 1.5)
            print(f"  Band Gap Correction: ENABLED (factor={factor})")
        else:
            print(f"  Band Gap Correction: DISABLED")
        
        fallback = config.get("interpolation", {}).get("mp_api_fallback_to_literature", True)
        print(f"  Fallback to Literature: {'YES' if fallback else 'NO'}")
    
    print()


def run_pipeline(config: dict, logger):
    """Execute the main pipeline"""
    
    # ========================================================================
    # STEP 1: Fetch structures from Materials Project
    # ========================================================================
    logger.info("STEP 1: Fetching structures from Materials Project API")
    print("STEP 1: Fetching structures from Materials Project API...")
    
    try:
        fetcher = create_fetcher_from_config(config, logger)
        
        gaas_structure = fetcher.fetch_gaas_structure()
        alas_structure = fetcher.fetch_alas_structure()
        
        logger.info(f"  [OK] GaAs: {gaas_structure.composition.reduced_formula}")
        logger.info(f"  [OK] AlAs: {alas_structure.composition.reduced_formula}")
        print(f"  [OK] Successfully fetched GaAs and AlAs structures")
        
    except Exception as e:
        logger.error(f"Failed to fetch structures: {e}")
        print(f"  [ERROR] ERROR: {e}")
        sys.exit(1)
    
    # ========================================================================
    # STEP 2: (Optional) Fetch MP-API properties
    # ========================================================================
    mode = config.get("interpolation", {}).get("mode", "literature")
    
    if mode == "mp_api":
        logger.info("STEP 2: Fetching properties from Materials Project API")
        print("\nSTEP 2: Fetching properties from Materials Project API...")
        
        try:
            mp_props = fetcher.fetch_and_update_constants(update_constants_module=True)
            
            gaas_props_count = len([v for v in mp_props["GaAs"].values() if v is not None])
            alas_props_count = len([v for v in mp_props["AlAs"].values() if v is not None])
            
            logger.info(f"  [OK] GaAs: {gaas_props_count} properties fetched")
            logger.info(f"  [OK] AlAs: {alas_props_count} properties fetched")
            print(f"  [OK] GaAs: {gaas_props_count} properties")
            print(f"  [OK] AlAs: {alas_props_count} properties")
            
            # Save fetched properties
            results_dir = Path(config.get("output", {}).get("results_dir", "results"))
            fetcher.save_properties_to_json(
                mp_props["GaAs"], 
                results_dir / "mp_api_gaas_properties.json"
            )
            fetcher.save_properties_to_json(
                mp_props["AlAs"], 
                results_dir / "mp_api_alas_properties.json"
            )
            
        except Exception as e:
            logger.warning(f"Could not fetch all MP-API properties: {e}")
            print(f"  ⚠ WARNING: Some properties could not be fetched")
            
            fallback = config.get("interpolation", {}).get("mp_api_fallback_to_literature", True)
            if fallback:
                logger.info("  → Fallback to literature values enabled")
                print(f"  → Will use literature values for missing properties")
    
    else:
        logger.info("STEP 2: Using literature-based properties (skipping MP-API fetch)")
        print("\nSTEP 2: Using literature-based properties (no MP-API fetch needed)")
    
    # ========================================================================
    # STEP 3: Initialize structure interpolator
    # ========================================================================
    logger.info("STEP 3: Initializing structure interpolator")
    print("\nSTEP 3: Initializing structure interpolator...")
    
    try:
        interpolator = create_interpolator_from_config(
            config,
            gaas_structure,
            alas_structure,
            logger
        )
        
        logger.info(f"  [OK] Mode: {interpolator.data_source}")
        logger.info(f"  [OK] Supercell: {interpolator.supercell_size}")
        logger.info(f"  [OK] Total Ga sites: {interpolator.total_ga_sites}")
        print(f"  [OK] Interpolator ready (mode={interpolator.data_source})")
        
    except Exception as e:
        logger.error(f"Failed to initialize interpolator: {e}")
        print(f"  [ERROR] ERROR: {e}")
        sys.exit(1)
    
    # ========================================================================
    # STEP 4: Generate alloy structures and calculate properties
    # ========================================================================
    logger.info("STEP 4: Generating alloy structures and calculating properties")
    print("\nSTEP 4: Generating structures and calculating properties...")
    
    composition_config = config.get("structure_interpolation", {}).get("composition", {})
    x_min = composition_config.get("x_min", 0.0)
    x_max = composition_config.get("x_max", 1.0)
    x_step = composition_config.get("x_step", 0.025)
    
    output_dir = Path(config.get("output", {}).get("structures_dir", "data/structures"))
    
    try:
        alloy_list = interpolator.generate_composition_range(
            x_min=x_min,
            x_max=x_max,
            x_step=x_step,
            output_dir=output_dir,
            save_cif=True,
            save_metadata=True
        )
        
        logger.info(f"  [OK] Generated {len(alloy_list)} compositions")
        print(f"  [OK] Successfully generated {len(alloy_list)} structures")
        
    except Exception as e:
        logger.error(f"Failed to generate structures: {e}")
        print(f"  [ERROR] ERROR: {e}")
        sys.exit(1)
    
    # ========================================================================
    # STEP 5: Create summary report
    # ========================================================================
    logger.info("STEP 5: Creating summary report")
    print("\nSTEP 5: Creating summary report...")
    
    try:
        results_dir = Path(config.get("output", {}).get("results_dir", "results"))
        
        summary = {
            "version": "0.1.1",
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "data_source": mode,
                "composition_range": {
                    "x_min": x_min,
                    "x_max": x_max,
                    "x_step": x_step,
                },
                "num_structures": len(alloy_list),
            },
            "structures": [
                {
                    "composition": alloy.composition.formula,
                    "x": alloy.composition.x,
                    "num_al": alloy.composition.num_al,
                    "num_ga": alloy.composition.num_ga,
                    "band_gap": alloy.properties.get("band_gap"),
                    "band_gap_type": alloy.properties.get("band_gap_type"),
                    "lattice_constant": alloy.properties.get("lattice_constant"),
                }
                for alloy in alloy_list
            ]
        }
        
        summary_file = results_dir / f"summary_v0.1.1_{mode}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"  [OK] Summary saved: {summary_file}")
        print(f"  [OK] Summary saved: {summary_file.name}")
        
    except Exception as e:
        logger.warning(f"Could not create summary: {e}")
        print(f"  ⚠ WARNING: Could not create summary")
    
    # ========================================================================
    # DONE
    # ========================================================================
    logger.info("Pipeline completed successfully!")
    print()
    print("=" * 80)
    print("  [OK] PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print(f"  End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"  Output directories:")
    print(f"    - CIF files: {output_dir / 'cif'}")
    print(f"    - Metadata: {output_dir / 'metadata'}")
    print(f"    - Results: {results_dir}")
    print("=" * 80)
    print()


def main():
    """Main entry point"""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="s-CGCNN v0.1.1 - AlGaAs Structure Generation Pipeline"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/config_v0.1.1.yaml"),
        help="Path to configuration file (default: config/config_v0.1.1.yaml)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["literature", "mp_api"],
        help="Override data source mode (overrides config file)"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    if not args.config.exists():
        print(f"ERROR: Configuration file not found: {args.config}")
        sys.exit(1)
    
    config = load_config(args.config)
    
    # Override mode if specified
    if args.mode:
        config.setdefault("interpolation", {})["mode"] = args.mode
    
    # Setup directories
    setup_directories(config)
    
    # Setup logger
    log_level = config.get("output", {}).get("log_level", "INFO")
    log_prefix = config.get("output", {}).get("log_file_prefix", "v0.1.1")
    logs_dir = Path(config.get("output", {}).get("logs_dir", "logs"))
    
    log_file = logs_dir / f"{log_prefix}_pipeline.log"
    logger = setup_logger("Pipeline", log_file=log_file, level=log_level)
    
    # Print header
    print_header()
    print_config_summary(config)
    
    # Run pipeline
    try:
        run_pipeline(config, logger)
    except KeyboardInterrupt:
        print("\n\n⚠ Pipeline interrupted by user")
        logger.warning("Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Pipeline failed with error: {e}")
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()