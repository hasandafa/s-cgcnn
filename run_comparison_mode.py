"""
s-CGCNN v0.1.1 - Comparison Mode Script

Generates side-by-side comparison of Literature vs MP-API data sources.

Usage:
    python run_comparison_mode.py [--config path/to/config.yaml]

Author: Abdullah Hasan Dafa
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import yaml
import json
import pandas as pd

from src.data_acquisition import MPFetcher, StructureInterpolator
from src.data_acquisition import create_fetcher_from_config
from src.utils import setup_logger, constants


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def setup_directories(config: dict):
    """Create necessary output directories"""
    comparison_dir = Path(
        config.get("comparison", {}).get("comparison_output_dir", "results/comparison_v0.1.1")
    )
    comparison_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (comparison_dir / "literature").mkdir(exist_ok=True)
    (comparison_dir / "mp_api").mkdir(exist_ok=True)
    (comparison_dir / "analysis").mkdir(exist_ok=True)


def print_header():
    """Print comparison mode header"""
    print("=" * 80)
    print("  s-CGCNN v0.1.1 - COMPARISON MODE")
    print("  Side-by-side: Literature vs MP-API")
    print("=" * 80)
    print(f"  Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()


def run_comparison(config: dict, logger):
    """Execute comparison pipeline"""
    
    comparison_config = config.get("comparison", {})
    comparison_dir = Path(comparison_config.get("comparison_output_dir", "results/comparison_v0.1.1"))
    
    # ========================================================================
    # STEP 1: Fetch structures
    # ========================================================================
    logger.info("STEP 1: Fetching structures from Materials Project API")
    print("STEP 1: Fetching structures...")
    
    fetcher = create_fetcher_from_config(config, logger)
    gaas_structure = fetcher.fetch_gaas_structure()
    alas_structure = fetcher.fetch_alas_structure()
    
    print(f"  [OK] Structures fetched")
    
    # ========================================================================
    # STEP 2: Fetch MP-API properties
    # ========================================================================
    logger.info("STEP 2: Fetching MP-API properties")
    print("\nSTEP 2: Fetching MP-API properties...")
    
    mp_props = fetcher.fetch_and_update_constants(update_constants_module=True)
    
    # Save MP properties
    fetcher.save_properties_to_json(
        mp_props["GaAs"],
        comparison_dir / "analysis" / "mp_api_gaas_raw.json"
    )
    fetcher.save_properties_to_json(
        mp_props["AlAs"],
        comparison_dir / "analysis" / "mp_api_alas_raw.json"
    )
    
    print(f"  [OK] MP-API properties fetched")
    
    # ========================================================================
    # STEP 3: Generate Literature-based dataset
    # ========================================================================
    logger.info("STEP 3: Generating LITERATURE-based dataset")
    print("\nSTEP 3: Generating LITERATURE-based dataset...")
    
    # Override config for literature mode
    config_lit = config.copy()
    config_lit["interpolation"] = {"mode": "literature"}
    
    interpolator_lit = StructureInterpolator(
        gaas_structure=gaas_structure,
        alas_structure=alas_structure,
        supercell_size=tuple(config.get("structure_interpolation", {}).get("supercell_size", [2, 2, 2])),
        data_source="literature",
        config=config_lit,
        logger=logger
    )
    
    composition_config = config.get("structure_interpolation", {}).get("composition", {})
    
    alloys_lit = interpolator_lit.generate_composition_range(
        x_min=composition_config.get("x_min", 0.0),
        x_max=composition_config.get("x_max", 1.0),
        x_step=composition_config.get("x_step", 0.025),
        output_dir=comparison_dir / "literature",
        save_cif=True,
        save_metadata=True
    )
    
    print(f"  [OK] Literature dataset: {len(alloys_lit)} compositions")
    
    # ========================================================================
    # STEP 4: Generate MP-API-based dataset
    # ========================================================================
    logger.info("STEP 4: Generating MP-API-based dataset")
    print("\nSTEP 4: Generating MP-API-based dataset...")
    
    # Override config for mp_api mode
    config_mp = config.copy()
    config_mp["interpolation"] = {
        "mode": "mp_api",
        "mp_api_fallback_to_literature": True,
        "mp_bandgap_correction": config.get("interpolation", {}).get("mp_bandgap_correction", {})
    }
    
    interpolator_mp = StructureInterpolator(
        gaas_structure=gaas_structure,
        alas_structure=alas_structure,
        supercell_size=tuple(config.get("structure_interpolation", {}).get("supercell_size", [2, 2, 2])),
        data_source="mp_api",
        config=config_mp,
        logger=logger
    )
    
    alloys_mp = interpolator_mp.generate_composition_range(
        x_min=composition_config.get("x_min", 0.0),
        x_max=composition_config.get("x_max", 1.0),
        x_step=composition_config.get("x_step", 0.025),
        output_dir=comparison_dir / "mp_api",
        save_cif=True,
        save_metadata=True
    )
    
    print(f"  [OK] MP-API dataset: {len(alloys_mp)} compositions")
    
    # ========================================================================
    # STEP 5: Create comparison analysis
    # ========================================================================
    logger.info("STEP 5: Creating comparison analysis")
    print("\nSTEP 5: Creating comparison analysis...")
    
    # Properties to compare
    comparison_metrics = comparison_config.get("comparison_metrics", [
        "band_gap",
        "lattice_constant",
        "bulk_modulus",
        "dielectric_constant_static"
    ])
    
    # Build comparison dataframe
    comparison_data = []
    
    for alloy_lit, alloy_mp in zip(alloys_lit, alloys_mp):
        x = alloy_lit.composition.x
        
        row = {
            "composition": alloy_lit.composition.formula,
            "x": x,
        }
        
        for metric in comparison_metrics:
            lit_val = alloy_lit.properties.get(metric)
            mp_val = alloy_mp.properties.get(metric)
            
            row[f"{metric}_literature"] = lit_val
            row[f"{metric}_mp_api"] = mp_val
            
            if lit_val is not None and mp_val is not None:
                if isinstance(lit_val, (int, float)) and isinstance(mp_val, (int, float)):
                    diff = mp_val - lit_val
                    rel_diff = (diff / lit_val * 100) if lit_val != 0 else None
                    
                    row[f"{metric}_difference"] = diff
                    row[f"{metric}_rel_diff_percent"] = rel_diff
        
        comparison_data.append(row)
    
    df_comparison = pd.DataFrame(comparison_data)
    
    # Save comparison CSV
    csv_file = comparison_dir / "analysis" / "comparison_table.csv"
    df_comparison.to_csv(csv_file, index=False)
    
    print(f"  [OK] Comparison table saved: {csv_file.name}")
    
    # ========================================================================
    # STEP 6: Create summary statistics
    # ========================================================================
    logger.info("STEP 6: Creating summary statistics")
    print("\nSTEP 6: Creating summary statistics...")
    
    summary = {
        "version": "0.1.1",
        "timestamp": datetime.now().isoformat(),
        "num_compositions": len(alloys_lit),
        "comparison_metrics": comparison_metrics,
        "statistics": {}
    }
    
    for metric in comparison_metrics:
        lit_col = f"{metric}_literature"
        mp_col = f"{metric}_mp_api"
        diff_col = f"{metric}_difference"
        rel_diff_col = f"{metric}_rel_diff_percent"
        
        if lit_col in df_comparison.columns and mp_col in df_comparison.columns:
            lit_vals = df_comparison[lit_col].dropna()
            mp_vals = df_comparison[mp_col].dropna()
            
            if len(lit_vals) > 0 and len(mp_vals) > 0:
                summary["statistics"][metric] = {
                    "literature": {
                        "mean": float(lit_vals.mean()),
                        "std": float(lit_vals.std()),
                        "min": float(lit_vals.min()),
                        "max": float(lit_vals.max()),
                    },
                    "mp_api": {
                        "mean": float(mp_vals.mean()),
                        "std": float(mp_vals.std()),
                        "min": float(mp_vals.min()),
                        "max": float(mp_vals.max()),
                    }
                }
                
                if diff_col in df_comparison.columns:
                    diffs = df_comparison[diff_col].dropna()
                    if len(diffs) > 0:
                        summary["statistics"][metric]["difference"] = {
                            "mean": float(diffs.mean()),
                            "std": float(diffs.std()),
                            "rmse": float((diffs ** 2).mean() ** 0.5),
                        }
                
                if rel_diff_col in df_comparison.columns:
                    rel_diffs = df_comparison[rel_diff_col].dropna()
                    if len(rel_diffs) > 0:
                        summary["statistics"][metric]["relative_difference_percent"] = {
                            "mean": float(rel_diffs.mean()),
                            "std": float(rel_diffs.std()),
                        }
    
    # Save summary JSON
    summary_file = comparison_dir / "analysis" / "comparison_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"  [OK] Summary statistics saved: {summary_file.name}")
    
    # ========================================================================
    # STEP 7: Print key findings
    # ========================================================================
    print("\n" + "=" * 80)
    print("  KEY FINDINGS:")
    print("=" * 80)
    
    for metric in comparison_metrics:
        if metric in summary["statistics"]:
            stats = summary["statistics"][metric]
            
            lit_mean = stats["literature"]["mean"]
            mp_mean = stats["mp_api"]["mean"]
            
            print(f"\n  {metric.upper()}:")
            print(f"    Literature mean: {lit_mean:.4f}")
            print(f"    MP-API mean:     {mp_mean:.4f}")
            
            if "relative_difference_percent" in stats:
                rel_diff_mean = stats["relative_difference_percent"]["mean"]
                print(f"    Avg. difference: {rel_diff_mean:.2f}%")
    
    print("\n" + "=" * 80)
    
    # ========================================================================
    # DONE
    # ========================================================================
    logger.info("Comparison completed successfully!")
    print()
    print("=" * 80)
    print("  [SUCCESS] COMPARISON COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print(f"  End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"  Output directory: {comparison_dir}")
    print(f"    - Literature data: literature/")
    print(f"    - MP-API data: mp_api/")
    print(f"    - Analysis: analysis/")
    print("=" * 80)
    print()


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description="s-CGCNN v0.1.1 - Comparison Mode (Literature vs MP-API)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/config_v0.1.1.yaml"),
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    if not args.config.exists():
        print(f"ERROR: Configuration file not found: {args.config}")
        sys.exit(1)
    
    config = load_config(args.config)
    
    # Enable comparison mode in config
    config.setdefault("comparison", {})["enabled"] = True
    
    # Setup directories
    setup_directories(config)
    
    # Setup logger
    comparison_dir = Path(
        config.get("comparison", {}).get("comparison_output_dir", "results/comparison_v0.1.1")
    )
    log_file = comparison_dir / "comparison.log"
    logger = setup_logger("Comparison", log_file=log_file, level="INFO")
    
    # Print header
    print_header()
    
    # Run comparison
    try:
        run_comparison(config, logger)
    except KeyboardInterrupt:
        print("\n\n⚠ Comparison interrupted by user")
        logger.warning("Comparison interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Comparison failed with error: {e}")
        logger.error(f"Comparison failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()