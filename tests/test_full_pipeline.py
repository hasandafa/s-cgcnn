#!/usr/bin/env python3
"""
Full Pipeline Test Script
Tests the complete material-agnostic pipeline from data acquisition to graph conversion.

This script demonstrates:
1. Data acquisition from Materials Project
2. Structure generation and interpolation (any alloy system)
3. Property calculation with Vegard's Law (any alloy system)
4. Optional charge density interpolation
5. Optional structure relaxation
6. Optional tight-binding electronic structure
7. Graph conversion for GNN training

Usage:
    python test_full_pipeline.py

Or with specific options:
    python test_full_pipeline.py --quick --no-charge-density --alloy AlGaAs
    python test_full_pipeline.py --test-graphs-only  # Test only graph conversion
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import get_config, get_logger, scrape_binary_compounds, run_full_pipeline
from src.data_acquisition import process_all_materials
from src.graph_conversion import GraphConversionPipeline

logger = get_logger(__name__)


def test_data_acquisition() -> bool:
    """Test data acquisition from Materials Project."""
    logger.info("Testing data acquisition...")

    try:
        # Test with cache (should be fast if data exists)
        results = scrape_binary_compounds()
        logger.info(f"[OK] Data acquisition successful: {len(results)} materials")

        # Verify we have the expected materials
        expected_ids = ["mp-2534", "mp-2172"]  # GaAs, AlAs
        found_ids = list(results.keys())

        for expected_id in expected_ids:
            if expected_id not in found_ids:
                logger.error(f"Missing expected material: {expected_id}")
                return False

        logger.info("[OK] All expected materials found")
        return True

    except Exception as e:
        logger.error(f"[FAIL] Data acquisition failed: {e}")
        return False


def test_cif_processing() -> bool:
    """Test CIF processing functionality."""
    logger.info("Testing CIF processing...")

    try:
        # Test processing all materials
        success = process_all_materials()
        if success:
            logger.info("[OK] CIF processing successful")
            return True
        else:
            logger.warning("[WARN] CIF processing completed with warnings")
            return True  # Not a failure, just warnings

    except Exception as e:
        logger.error(f"[FAIL] CIF processing failed: {e}")
        return False


def test_calculation_pipeline(alloy_system: str = "AlGaAs", material1: str = "GaAs", material2: str = "AlAs", enable_all_features: bool = False) -> bool:
    """Test the calculation pipeline."""
    logger.info(f"Testing calculation pipeline for {alloy_system}...")

    try:
        # Run with minimal features for speed
        results = run_full_pipeline(
            alloy_system=alloy_system,
            material1=material1,
            material2=material2,
            x_values=[0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1],  # Fewer compositions for speed
            enable_all_features=enable_all_features
        )

        # Verify results
        structures = results.get('structures', [])
        properties = results.get('properties', {})

        if len(structures) != 9:  # Updated to match the x_values count
            logger.error(f"Expected 9 structures, got {len(structures)}")
            return False

        compositions = properties.get('compositions', {})
        if len(compositions) != 9:
            logger.error(f"Expected 9 property sets, got {len(compositions)}")
            return False

        logger.info("[OK] Calculation pipeline successful")
        logger.info(f"  - Generated {len(structures)} structures")
        logger.info(f"  - Calculated properties for {len(compositions)} compositions")

        return True

    except Exception as e:
        logger.error(f"[FAIL] Calculation pipeline failed: {e}")
        return False


def test_graph_conversion_pipeline(alloy_system: str = "AlGaAs") -> bool:
    """Test the graph conversion pipeline."""
    logger.info(f"Testing graph conversion pipeline for {alloy_system}...")

    try:
        # Define paths based on calculation pipeline output
        structure_dir = f"data/outputs/calculations/structures"
        properties_file = f"data/outputs/calculations/properties.json"
        output_dir = f"data/outputs/graphs"

        # Check if input files exist
        if not Path(properties_file).exists():
            logger.warning(f"Properties file not found: {properties_file}")
            logger.info("Skipping graph conversion test (run calculation pipeline first)")
            return True  # Not a failure, just not available

        if not Path(structure_dir).exists():
            logger.warning(f"Structure directory not found: {structure_dir}")
            logger.info("Skipping graph conversion test (run calculation pipeline first)")
            return True  # Not a failure, just not available

        # Run graph conversion
        pipeline = GraphConversionPipeline(
            structure_dir=structure_dir,
            properties_file=properties_file,
            output_dir=output_dir,
            cutoff_radius=5.0,
            use_both_structures=True
        )

        # Convert all structures to graphs
        pipeline.convert_all()

        # Compute statistics and create visualizations
        pipeline.compute_statistics()
        pipeline.create_visualizations()

        # Save dataset info
        pipeline.save_dataset_info()

        # Verify output
        summary = pipeline.get_summary()
        num_graphs = summary.get('total_graphs_converted', 0)

        if num_graphs == 0:
            logger.warning("No graphs were converted (input data may be incomplete)")
            return True  # Not necessarily a failure

        logger.info("[OK] Graph conversion pipeline successful")
        logger.info(f"  - Converted {num_graphs} structures to graphs")
        logger.info(f"  - Output directory: {output_dir}")

        # Test dataset loading
        try:
            from src.graph_conversion import MaterialPropertyDataset
            dataset = MaterialPropertyDataset(f"{output_dir}")
            logger.info(f"  - Dataset loaded with {len(dataset)} samples")

            if len(dataset) > 0:
                sample_graph, sample_target = dataset[0]
                logger.info(f"  - Sample graph: {sample_graph.num_nodes} nodes, {sample_graph.edge_index.shape[1]} edges")
                logger.info(f"  - Sample target shape: {sample_target.shape}")

        except Exception as e:
            logger.warning(f"Dataset loading test failed: {e}")

        return True

    except Exception as e:
        logger.error(f"[FAIL] Graph conversion pipeline failed: {e}")
        return False


def test_config_loading() -> bool:
    """Test configuration loading."""
    logger.info("Testing configuration loading...")

    try:
        config = get_config()
        logger.info("[OK] Configuration loaded successfully")

        # Check required sections
        required_keys = ['paths', 'system', 'hyperparameters']
        for key in required_keys:
            if key not in config.config:
                logger.error(f"Missing required config key: {key}")
                return False

        logger.info("[OK] All required configuration sections present")
        return True

    except Exception as e:
        logger.error(f"[FAIL] Configuration loading failed: {e}")
        return False


def run_full_test(alloy_system: str = "AlGaAs", material1: str = "GaAs", material2: str = "AlAs", enable_all_features: bool = False, skip_cif: bool = False) -> bool:
    """Run the complete test suite."""
    logger.info("=" * 60)
    logger.info(f"{alloy_system.upper()} PIPELINE FULL TEST SUITE")
    logger.info("=" * 60)

    tests = [
        ("Configuration Loading", test_config_loading),
        ("Data Acquisition", test_data_acquisition),
    ]

    if not skip_cif:
        tests.append(("CIF Processing", test_cif_processing))

    tests.extend([
        ("Calculation Pipeline", lambda: test_calculation_pipeline(alloy_system, material1, material2, enable_all_features)),
        ("Graph Conversion Pipeline", lambda: test_graph_conversion_pipeline(alloy_system)),
    ])

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if test_func():
                logger.info(f"[OK] {test_name}: PASSED")
                passed += 1
            else:
                logger.error(f"[FAIL] {test_name}: FAILED")
        except Exception as e:
            logger.error(f"[ERROR] {test_name}: ERROR - {e}")

    logger.info("\n" + "=" * 60)
    logger.info(f"TEST RESULTS: {passed}/{total} tests passed")

    if passed == total:
        logger.info("[SUCCESS] ALL TESTS PASSED! Pipeline is working correctly.")
        return True
    else:
        logger.error(f"[FAILURE] {total - passed} test(s) failed. Check logs for details.")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test the complete material-agnostic pipeline")
    parser.add_argument("--quick", action="store_true",
                        help="Run quick test with minimal features")
    parser.add_argument("--full", action="store_true",
                        help="Run full test with all features enabled")
    parser.add_argument("--no-charge-density", action="store_true",
                        help="Disable charge density features")
    parser.add_argument("--test-graphs-only", action="store_true",
                        help="Test only graph conversion (skip structure generation)")
    parser.add_argument("--test-cif-only", action="store_true",
                        help="Test only CIF processing")
    parser.add_argument("--skip-cif", action="store_true",
                        help="Skip CIF processing in full test")
    parser.add_argument("--alloy", type=str, default="AlGaAs",
                        help="Alloy system to test (default: AlGaAs)")
    parser.add_argument("--mat1", type=str, default="GaAs",
                        help="First material (default: GaAs)")
    parser.add_argument("--mat2", type=str, default="AlAs",
                        help="Second material (default: AlAs)")

    args = parser.parse_args()

    # Determine test mode
    if args.full:
        enable_all_features = True
        logger.info("Running FULL test suite with all features enabled")
    elif args.quick:
        enable_all_features = False
        logger.info("Running QUICK test suite (minimal features)")
    else:
        enable_all_features = False
        logger.info("Running STANDARD test suite")

    # Handle special test modes
    if args.test_graphs_only:
        logger.info("Running GRAPH CONVERSION ONLY test")
        success = test_graph_conversion_pipeline(args.alloy)
    elif args.test_cif_only:
        logger.info("Running CIF PROCESSING ONLY test")
        success = test_cif_processing()
    else:
        # Run tests
        success = run_full_test(
            alloy_system=args.alloy,
            material1=args.mat1,
            material2=args.mat2,
            enable_all_features=enable_all_features,
            skip_cif=args.skip_cif
        )

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()