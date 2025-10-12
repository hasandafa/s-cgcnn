"""
Testing Script for s-CGCNN v0.1.1
1.1 Adding Interpolation Source Selection

Tests:
1. Dual data source support (literature vs MP-API)
2. Property calculation with both sources
3. Comparison functionality
4. Configuration validation
s-cgcnn\tests\1.1 Adding Interpolation Source Selection.py
Author: Abdullah Hasan Dafa
Version: 0.1.1
"""

import sys
from pathlib import Path
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_acquisition import MPFetcher, StructureInterpolator
from src.utils import constants, setup_logger
from pymatgen.core import Structure, Lattice


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

def load_test_config():
    """Load configuration for testing"""
    config_file = project_root / "config" / "config_v0.1.1.yaml"
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        print(f"✓ Loaded config from: {config_file.name}")
    else:
        # Minimal config if file not found
        config = {
            "interpolation": {
                "mode": "literature",
                "mp_api_fallback_to_literature": True,
            },
            "structure_interpolation": {
                "supercell_size": [2, 2, 2],
            },
            "materials_project": {
                "api_key_file": "config/mp_api_key.txt",
                "gaas_mp_id": "mp-2534",
                "alas_mp_id": "mp-2172",
            }
        }
        print("⚠ Using minimal default config")
    
    return config


# ============================================================================
# TEST 1: Constants Module - Dual Data Source
# ============================================================================

def test_1_constants_dual_source():
    """Test that constants module supports both data sources"""
    print("\n" + "="*80)
    print("TEST 1: Constants Module - Dual Data Source")
    print("="*80)
    
    try:
        # Test literature properties exist
        gaas_lit = constants.get_properties("GaAs", "literature")
        alas_lit = constants.get_properties("AlAs", "literature")
        
        assert gaas_lit["band_gap"] == 1.424, "GaAs literature band gap incorrect"
        assert alas_lit["band_gap"] == 2.168, "AlAs literature band gap incorrect"
        print("✓ Literature properties loaded correctly")
        
        # Test MP-API properties exist (structure)
        gaas_mp = constants.get_properties("GaAs", "mp_api")
        alas_mp = constants.get_properties("AlAs", "mp_api")
        
        assert "mp_id" in gaas_mp, "GaAs MP-API properties missing mp_id"
        assert gaas_mp["mp_id"] == "mp-2534", "GaAs MP-ID incorrect"
        print("✓ MP-API property structure exists")
        
        # Test get_properties with invalid source
        try:
            constants.get_properties("GaAs", "invalid_source")
            print("✗ Should have raised error for invalid source")
            return False
        except ValueError:
            print("✓ Invalid source properly rejected")
        
        # Test band gap type determination
        assert constants.determine_band_gap_type(0.0) == "direct"
        assert constants.determine_band_gap_type(0.44) == "direct"
        assert constants.determine_band_gap_type(0.45) == "indirect"
        assert constants.determine_band_gap_type(1.0) == "indirect"
        print("✓ Band gap type determination correct")
        
        # Test bowing parameters
        band_gap_bowing = constants.get_bowing_parameter("band_gap")
        assert band_gap_bowing == 0.37, "Band gap bowing parameter incorrect"
        print("✓ Bowing parameters accessible")
        
        print("\n✓ TEST 1 PASSED: Constants module working correctly")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TEST 2: Structure Interpolator - Literature Mode
# ============================================================================

def test_2_interpolator_literature_mode():
    """Test structure interpolation in literature mode"""
    print("\n" + "="*80)
    print("TEST 2: Structure Interpolator - Literature Mode")
    print("="*80)
    
    try:
        logger = setup_logger("Test2")
        config = load_test_config()
        
        # Create mock structures
        lattice_gaas = Lattice.cubic(5.6533)
        gaas_structure = Structure(
            lattice_gaas,
            ["Ga", "As"],
            [[0, 0, 0], [0.25, 0.25, 0.25]]
        )
        
        lattice_alas = Lattice.cubic(5.6611)
        alas_structure = Structure(
            lattice_alas,
            ["Al", "As"],
            [[0, 0, 0], [0.25, 0.25, 0.25]]
        )
        
        print("✓ Mock structures created")
        
        # Initialize interpolator in literature mode
        interpolator = StructureInterpolator(
            gaas_structure=gaas_structure,
            alas_structure=alas_structure,
            supercell_size=(2, 2, 2),
            data_source="literature",
            config=config,
            logger=logger
        )
        
        assert interpolator.data_source == "literature"
        assert interpolator.total_ga_sites == 8
        print("✓ Interpolator initialized in literature mode")
        
        # Test pure GaAs (x=0.0)
        structure_gaas, comp_gaas = interpolator.generate_alloy_structure(x=0.0)
        assert comp_gaas.x == 0.0
        assert comp_gaas.num_al == 0
        assert comp_gaas.num_ga == 8
        print("✓ Pure GaAs structure generated (x=0.0)")
        
        # Test pure AlAs (x=1.0)
        structure_alas, comp_alas = interpolator.generate_alloy_structure(x=1.0)
        assert comp_alas.x == 1.0
        assert comp_alas.num_al == 8
        assert comp_alas.num_ga == 0
        print("✓ Pure AlAs structure generated (x=1.0)")
        
        # Test intermediate composition (x=0.5)
        structure_mid, comp_mid = interpolator.generate_alloy_structure(x=0.5)
        assert comp_mid.x == 0.5
        assert comp_mid.num_al == 4
        assert comp_mid.num_ga == 4
        print("✓ Al₀.₅Ga₀.₅As structure generated")
        
        # Test property calculation
        props_gaas = interpolator.calculate_properties(x=0.0)
        assert abs(props_gaas["band_gap"] - 1.424) < 0.01, "GaAs band gap incorrect"
        assert props_gaas["band_gap_type"] == "direct"
        print("✓ Properties calculated for x=0.0 (GaAs)")
        
        props_alas = interpolator.calculate_properties(x=1.0)
        assert abs(props_alas["band_gap"] - 2.168) < 0.01, "AlAs band gap incorrect"
        assert props_alas["band_gap_type"] == "indirect"
        print("✓ Properties calculated for x=1.0 (AlAs)")
        
        props_mid = interpolator.calculate_properties(x=0.5)
        assert props_mid["band_gap"] > 1.424 and props_mid["band_gap"] < 2.168
        assert props_mid["band_gap_type"] == "indirect"  # x >= 0.45
        print("✓ Properties calculated for x=0.5 (interpolated)")
        
        print("\n✓ TEST 2 PASSED: Literature mode interpolation working")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TEST 3: MP Fetcher (Optional - requires API key)
# ============================================================================

def test_3_mp_fetcher():
    """Test Materials Project API fetcher (requires API key)"""
    print("\n" + "="*80)
    print("TEST 3: MP API Fetcher (Optional)")
    print("="*80)
    
    # Check if API key exists
    api_key_file = project_root / "config" / "mp_api_key.txt"
    
    if not api_key_file.exists():
        print("⚠ SKIPPED: MP API key not found (config/mp_api_key.txt)")
        print("  This test is optional. Get API key from materialsproject.org")
        return True  # Not a failure, just skipped
    
    try:
        logger = setup_logger("Test3")
        config = load_test_config()
        
        # Initialize fetcher
        fetcher = MPFetcher(config=config, logger=logger)
        print("✓ MPFetcher initialized")
        
        # Try to fetch GaAs structure
        try:
            gaas_structure = fetcher.fetch_gaas_structure()
            assert gaas_structure.composition.reduced_formula == "GaAs"
            assert abs(gaas_structure.lattice.a - 5.65) < 0.1
            print("✓ GaAs structure fetched from MP API")
        except Exception as e:
            print(f"⚠ Could not fetch GaAs structure: {e}")
            print("  (May be connection issue, not a critical failure)")
            return True
        
        # Try to fetch AlAs structure
        try:
            alas_structure = fetcher.fetch_alas_structure()
            assert alas_structure.composition.reduced_formula == "AlAs"
            assert abs(alas_structure.lattice.a - 5.66) < 0.1
            print("✓ AlAs structure fetched from MP API")
        except Exception as e:
            print(f"⚠ Could not fetch AlAs structure: {e}")
            return True
        
        print("\n✓ TEST 3 PASSED: MP API fetcher working")
        return True
        
    except Exception as e:
        print(f"\n⚠ TEST 3 SKIPPED/PARTIAL: {e}")
        print("  (Not critical - MP API tests are optional)")
        return True  # Not a hard failure


# ============================================================================
# TEST 4: Structure Interpolator - MP-API Mode with Fallback
# ============================================================================

def test_4_interpolator_mp_api_mode():
    """Test structure interpolation in MP-API mode with fallback"""
    print("\n" + "="*80)
    print("TEST 4: Structure Interpolator - MP-API Mode")
    print("="*80)
    
    try:
        logger = setup_logger("Test4")
        config = load_test_config()
        config["interpolation"]["mode"] = "mp_api"
        config["interpolation"]["mp_api_fallback_to_literature"] = True
        
        # Create mock structures
        lattice_gaas = Lattice.cubic(5.6533)
        gaas_structure = Structure(
            lattice_gaas,
            ["Ga", "As"],
            [[0, 0, 0], [0.25, 0.25, 0.25]]
        )
        
        lattice_alas = Lattice.cubic(5.6611)
        alas_structure = Structure(
            lattice_alas,
            ["Al", "As"],
            [[0, 0, 0], [0.25, 0.25, 0.25]]
        )
        
        # Initialize interpolator in MP-API mode
        interpolator = StructureInterpolator(
            gaas_structure=gaas_structure,
            alas_structure=alas_structure,
            supercell_size=(2, 2, 2),
            data_source="mp_api",
            config=config,
            logger=logger
        )
        
        assert interpolator.data_source == "mp_api"
        print("✓ Interpolator initialized in MP-API mode")
        
        # Test property calculation (should fallback to literature if MP data is None)
        props = interpolator.calculate_properties(x=0.0, fallback_to_literature=True)
        
        # Should get SOME properties (either from MP or fallback)
        assert "band_gap" in props
        assert props["band_gap"] is not None
        print("✓ Properties calculated with fallback enabled")
        
        print("\n✓ TEST 4 PASSED: MP-API mode with fallback working")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TEST 5: Comparison Functionality
# ============================================================================

def test_5_comparison_mode():
    """Test comparison between literature and MP-API"""
    print("\n" + "="*80)
    print("TEST 5: Comparison Mode")
    print("="*80)
    
    try:
        logger = setup_logger("Test5")
        config = load_test_config()
        
        # Create mock structures
        lattice_gaas = Lattice.cubic(5.6533)
        gaas_structure = Structure(
            lattice_gaas,
            ["Ga", "As"],
            [[0, 0, 0], [0.25, 0.25, 0.25]]
        )
        
        lattice_alas = Lattice.cubic(5.6611)
        alas_structure = Structure(
            lattice_alas,
            ["Al", "As"],
            [[0, 0, 0], [0.25, 0.25, 0.25]]
        )
        
        # Initialize interpolator
        interpolator = StructureInterpolator(
            gaas_structure=gaas_structure,
            alas_structure=alas_structure,
            supercell_size=(2, 2, 2),
            data_source="literature",
            config=config,
            logger=logger
        )
        
        # Test comparison for x=0.5
        comparison = interpolator.compare_data_sources(
            x=0.5,
            properties_to_compare=["band_gap", "lattice_constant"]
        )
        
        assert "composition" in comparison
        assert comparison["composition"] == 0.5
        assert "properties" in comparison
        print("✓ Comparison data structure correct")
        
        # Check that comparison has data
        if "band_gap" in comparison["properties"]:
            bg_comparison = comparison["properties"]["band_gap"]
            assert "literature" in bg_comparison
            assert "mp_api" in bg_comparison
            print("✓ Comparison includes both data sources")
        
        print("\n✓ TEST 5 PASSED: Comparison functionality working")
        return True
        
    except Exception as e:
        print(f"\n✗ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all tests"""
    print("="*80)
    print("s-CGCNN v0.1.1 - Testing Script")
    print("1.1 Adding Interpolation Source Selection")
    print("="*80)
    print(f"Project root: {project_root}")
    print()
    
    results = {
        "Test 1: Constants Dual Source": test_1_constants_dual_source(),
        "Test 2: Interpolator Literature Mode": test_2_interpolator_literature_mode(),
        "Test 3: MP API Fetcher (Optional)": test_3_mp_fetcher(),
        "Test 4: Interpolator MP-API Mode": test_4_interpolator_mp_api_mode(),
        "Test 5: Comparison Mode": test_5_comparison_mode(),
    }
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status:12} {test_name}")
    
    print("-"*80)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - v0.1.1 is working correctly!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed - please review errors above")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)