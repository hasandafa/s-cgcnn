#!/usr/bin/env python3
"""
Full Pipeline Test Script
Tests the complete material-agnostic pipeline from data acquisition to calculation.

This script demonstrates:
1. Data acquisition from Materials Project
2. Structure generation and interpolation (any alloy system)
3. Property calculation with Vegard's Law (any alloy system)
4. Optional charge density interpolation
5. Optional structure relaxation
6. Optional tight-binding electronic structure

Usage:
    python test_full_pipeline.py

Or with specific options:
    python test_full_pipeline.py --quick --no-charge-density --alloy AlGaAs
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import get_config, get_logger, scrape_binary_compounds, run_full_pipeline

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


def test_calculation_pipeline(alloy_system: str = "AlGaAs", material1: str = "GaAs", material2: str = "AlAs", enable_all_features: bool = False) -> bool:
    """Test the calculation pipeline."""
    logger.info(f"Testing calculation pipeline for {alloy_system}...")

    try:
        # Run with minimal features for speed
        results = run_full_pipeline(
            alloy_system=alloy_system,
            material1=material1,
            material2=material2,
            x_values=[0.0, 0.25, 0.5, 0.75, 1.0],  # Fewer compositions for speed
            enable_all_features=enable_all_features
        )

        # Verify results
        structures = results.get('structures', [])
        properties = results.get('properties', {})

        if len(structures) != 5:
            logger.error(f"Expected 5 structures, got {len(structures)}")
            return False

        compositions = properties.get('compositions', {})
        if len(compositions) != 5:
            logger.error(f"Expected 5 property sets, got {len(compositions)}")
            return False

        logger.info("[OK] Calculation pipeline successful")
        logger.info(f"  - Generated {len(structures)} structures")
        logger.info(f"  - Calculated properties for {len(compositions)} compositions")

        return True

    except Exception as e:
        logger.error(f"[FAIL] Calculation pipeline failed: {e}")
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


def run_full_test(alloy_system: str = "AlGaAs", material1: str = "GaAs", material2: str = "AlAs", enable_all_features: bool = False) -> bool:
    """Run the complete test suite."""
    logger.info("=" * 60)
    logger.info(f"{alloy_system.upper()} PIPELINE FULL TEST SUITE")
    logger.info("=" * 60)

    tests = [
        ("Configuration Loading", test_config_loading),
        ("Data Acquisition", test_data_acquisition),
        ("Calculation Pipeline", lambda: test_calculation_pipeline(alloy_system, material1, material2, enable_all_features)),
    ]

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
                        help="Skip charge density tests")
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

    # Run tests
    success = run_full_test(
        alloy_system=args.alloy,
        material1=args.mat1,
        material2=args.mat2,
        enable_all_features=enable_all_features
    )

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()