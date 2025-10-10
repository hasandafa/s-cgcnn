"""
Version 0.1 Testing Module
Tests data acquisition and structure interpolation functionality

Run this file to validate that Version 0.1 is working correctly.
"""

import sys
from pathlib import Path
import json
import numpy as np
import pandas as pd
from typing import Dict, List

# Add parent directory to path (to access src/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_acquisition.mp_fetcher import MPDataFetcher
from src.data_acquisition.structure_interpolator import StructureInterpolator
from src.utils.logger_config import setup_logger
from src.utils.constants import X_VALUES, get_lattice_constant, get_band_gap_algaas


class Version01Tester:
    """
    Comprehensive testing for Version 0.1:
    - MP API data fetching
    - Structure interpolation
    - Property calculation
    - Data validation
    """
    
    def __init__(self):
        # Set root directory for all paths
        self.root_dir = Path(__file__).parent.parent
        
        # Setup logger with path relative to root
        log_file = self.root_dir / "logs" / "v0.1_testing.log"
        self.logger = setup_logger(__name__, log_file=str(log_file), level="INFO")
        self.logger.info("="*70)
        self.logger.info("Version 0.1 Testing Suite Initialized")
        self.logger.info("="*70)
        
        self.test_results = {
            "mp_fetching": {},
            "structure_generation": {},
            "property_calculation": {},
            "validation": {},
            "overall_status": "NOT_RUN"
        }
    
    def test_mp_fetcher(self) -> bool:
        """Test Materials Project data fetching."""
        self.logger.info("\n" + "="*70)
        self.logger.info("TEST 1: Materials Project Data Fetching")
        self.logger.info("="*70)
        
        try:
            # Read API key (path relative to root)
            api_key_file = self.root_dir / "config" / "mp_api_key.txt"
            if not api_key_file.exists():
                self.logger.error("✗ API key file not found!")
                self.test_results["mp_fetching"]["status"] = "FAILED"
                self.test_results["mp_fetching"]["error"] = "API key file missing"
                return False
            
            with open(api_key_file, 'r') as f:
                api_key = f.read().strip()
            
            self.logger.info("✓ API key loaded")
            
            # Initialize fetcher with path relative to root
            output_dir = str(self.root_dir / "data" / "raw")
            fetcher = MPDataFetcher(api_key, output_dir=output_dir)
            
            # Check if data already exists
            gaas_data = fetcher.load_saved_data("GaAs")
            alas_data = fetcher.load_saved_data("AlAs")
            
            if gaas_data and alas_data:
                self.logger.info("✓ MP data already fetched, loading from disk")
            else:
                self.logger.info("→ Fetching data from Materials Project...")
                all_data = fetcher.fetch_all_materials()
                gaas_data = all_data.get("GaAs")
                alas_data = all_data.get("AlAs")
            
            # Validate fetched data
            self._validate_mp_data(gaas_data, "GaAs")
            self._validate_mp_data(alas_data, "AlAs")
            
            self.test_results["mp_fetching"]["status"] = "PASSED"
            self.test_results["mp_fetching"]["gaas_structure"] = str(gaas_data["structure"].composition)
            self.test_results["mp_fetching"]["alas_structure"] = str(alas_data["structure"].composition)
            
            self.logger.info("✓ TEST 1 PASSED: MP data fetching successful")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ TEST 1 FAILED: {e}")
            self.test_results["mp_fetching"]["status"] = "FAILED"
            self.test_results["mp_fetching"]["error"] = str(e)
            return False
    
    def _validate_mp_data(self, data: Dict, material_name: str):
        """Validate fetched MP data."""
        self.logger.info(f"\n  Validating {material_name} data:")
        
        assert data["structure"] is not None, f"{material_name} structure is None"
        self.logger.info(f"    ✓ Structure: {data['structure'].composition}")
        
        assert "band_gap" in data["properties"], f"{material_name} missing band gap"
        self.logger.info(f"    ✓ Band gap: {data['properties']['band_gap']:.3f} eV")
        
        assert "density" in data["properties"], f"{material_name} missing density"
        self.logger.info(f"    ✓ Density: {data['properties']['density']:.3f} g/cm³")
        
        self.logger.info(f"  ✓ {material_name} data validated")
    
    def test_structure_interpolation(self) -> bool:
        """Test structure generation for all x values."""
        self.logger.info("\n" + "="*70)
        self.logger.info("TEST 2: Structure Interpolation")
        self.logger.info("="*70)
        
        try:
            # Load MP structures with path relative to root
            output_dir = str(self.root_dir / "data" / "raw")
            fetcher = MPDataFetcher("", output_dir=output_dir)
            gaas_data = fetcher.load_saved_data("GaAs")
            alas_data = fetcher.load_saved_data("AlAs")
            
            if not gaas_data or not alas_data:
                raise RuntimeError("MP data not available. Run TEST 1 first!")
            
            # Initialize interpolator with path relative to root
            structures_dir = str(self.root_dir / "data" / "structures")
            interpolator = StructureInterpolator(
                gaas_structure=gaas_data["structure"],
                alas_structure=alas_data["structure"],
                supercell_size=[2, 2, 2],
                output_dir=structures_dir
            )
            
            # Generate all structures
            self.logger.info(f"→ Generating {len(X_VALUES)} structures...")
            results = interpolator.generate_all_structures()
            
            # Validate results
            assert len(results) == len(X_VALUES), f"Expected {len(X_VALUES)} structures, got {len(results)}"
            
            self.logger.info(f"✓ Generated {len(results)} structures")
            
            # Check a few specific compositions
            self._validate_structure_composition(results[0], 0.0, "GaAs")  # Pure GaAs
            self._validate_structure_composition(results[20], 0.5, "Al0.5Ga0.5As")  # x=0.5
            self._validate_structure_composition(results[-1], 1.0, "AlAs")  # Pure AlAs
            
            self.test_results["structure_generation"]["status"] = "PASSED"
            self.test_results["structure_generation"]["total_structures"] = len(results)
            
            self.logger.info("✓ TEST 2 PASSED: Structure interpolation successful")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ TEST 2 FAILED: {e}")
            self.test_results["structure_generation"]["status"] = "FAILED"
            self.test_results["structure_generation"]["error"] = str(e)
            return False
    
    def _validate_structure_composition(self, result: tuple, expected_x: float, expected_formula: str):
        """Validate individual structure composition."""
        x, structure, properties = result
        
        assert abs(x - expected_x) < 0.001, f"x mismatch: expected {expected_x}, got {x}"
        
        comp = structure.composition
        total_ga_al = comp.get("Ga", 0) + comp.get("Al", 0)
        actual_x = comp.get("Al", 0) / total_ga_al if total_ga_al > 0 else 0
        
        assert abs(actual_x - expected_x) < 0.05, f"Composition mismatch: expected x={expected_x}, got {actual_x}"
        
        self.logger.info(f"    ✓ x={x:.3f}: {structure.composition}")
    
    def test_property_calculation(self) -> bool:
        """Test property interpolation with bowing parameters."""
        self.logger.info("\n" + "="*70)
        self.logger.info("TEST 3: Property Calculation & Bowing Parameters")
        self.logger.info("="*70)
        
        try:
            # Test key properties at critical points
            test_points = [0.0, 0.25, 0.45, 0.5, 0.75, 1.0]
            
            for x in test_points:
                self.logger.info(f"\n  Testing x = {x:.2f}:")
                
                # Lattice constant
                a = get_lattice_constant(x)
                self.logger.info(f"    Lattice constant: {a:.4f} Å")
                assert 5.6 < a < 5.7, f"Lattice constant out of range: {a}"
                
                # Band gap
                bg_data = get_band_gap_algaas(x)
                self.logger.info(f"    Band gap: {bg_data['value']:.3f} eV ({bg_data['type']})")
                assert 1.4 < bg_data['value'] < 3.1, f"Band gap out of range: {bg_data['value']}"
                
                # Check direct-to-indirect crossover
                if x < 0.45:
                    assert bg_data['type'] == 'direct', f"Expected direct gap at x={x}"
                else:
                    assert bg_data['type'] == 'indirect', f"Expected indirect gap at x={x}"
                
                self.logger.info(f"    ✓ Properties validated for x={x:.2f}")
            
            self.test_results["property_calculation"]["status"] = "PASSED"
            self.test_results["property_calculation"]["test_points"] = test_points
            
            self.logger.info("\n✓ TEST 3 PASSED: Property calculation successful")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ TEST 3 FAILED: {e}")
            self.test_results["property_calculation"]["status"] = "FAILED"
            self.test_results["property_calculation"]["error"] = str(e)
            return False
    
    def test_data_validation(self) -> bool:
        """Validate all generated structures and metadata."""
        self.logger.info("\n" + "="*70)
        self.logger.info("TEST 4: Data Validation")
        self.logger.info("="*70)
        
        try:
            # Paths relative to root
            cif_dir = self.root_dir / "data" / "structures" / "cif"
            metadata_dir = self.root_dir / "data" / "structures" / "metadata"
            
            # Check directories exist
            assert cif_dir.exists(), "CIF directory not found"
            assert metadata_dir.exists(), "Metadata directory not found"
            
            # Count files
            cif_files = list(cif_dir.glob("*.cif"))
            json_files = list(metadata_dir.glob("*.json"))
            
            self.logger.info(f"  Found {len(cif_files)} CIF files")
            self.logger.info(f"  Found {len(json_files)} metadata files")
            
            assert len(cif_files) == len(X_VALUES), f"Expected {len(X_VALUES)} CIF files, found {len(cif_files)}"
            assert len(json_files) >= len(X_VALUES), f"Expected at least {len(X_VALUES)} metadata files"
            
            # Validate a sample metadata file
            sample_metadata = metadata_dir / "AlGaAs_x_0_500.json"
            if sample_metadata.exists():
                with open(sample_metadata, 'r') as f:
                    data = json.load(f)
                
                required_keys = ["composition", "x_value", "lattice_parameters", "properties"]
                for key in required_keys:
                    assert key in data, f"Missing key in metadata: {key}"
                
                self.logger.info(f"  ✓ Sample metadata validated: {sample_metadata.name}")
            
            # Check summary file
            summary_file = metadata_dir / "generation_summary.json"
            assert summary_file.exists(), "Summary file not found"
            
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            
            self.logger.info(f"  ✓ Summary file validated")
            self.logger.info(f"    Total structures: {summary['total_structures']}")
            
            self.test_results["validation"]["status"] = "PASSED"
            self.test_results["validation"]["cif_files"] = len(cif_files)
            self.test_results["validation"]["metadata_files"] = len(json_files)
            
            self.logger.info("✓ TEST 4 PASSED: Data validation successful")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ TEST 4 FAILED: {e}")
            self.test_results["validation"]["status"] = "FAILED"
            self.test_results["validation"]["error"] = str(e)
            return False
    
    def generate_report(self):
        """Generate comprehensive testing report."""
        self.logger.info("\n" + "="*70)
        self.logger.info("VERSION 0.1 TESTING REPORT")
        self.logger.info("="*70)
        
        # Calculate overall status
        all_passed = all(
            self.test_results[test].get("status") == "PASSED"
            for test in ["mp_fetching", "structure_generation", "property_calculation", "validation"]
        )
        
        self.test_results["overall_status"] = "PASSED" if all_passed else "FAILED"
        
        # Print results
        for test_name, results in self.test_results.items():
            if test_name == "overall_status":
                continue
            
            status = results.get("status", "NOT_RUN")
            status_symbol = "✓" if status == "PASSED" else "✗"
            
            self.logger.info(f"\n{status_symbol} {test_name.upper().replace('_', ' ')}: {status}")
            
            if status == "FAILED" and "error" in results:
                self.logger.error(f"  Error: {results['error']}")
        
        self.logger.info("\n" + "="*70)
        if all_passed:
            self.logger.info("✓✓✓ ALL TESTS PASSED - VERSION 0.1 READY ✓✓✓")
        else:
            self.logger.error("✗✗✗ SOME TESTS FAILED - FIX ISSUES BEFORE PROCEEDING ✗✗✗")
        self.logger.info("="*70)
        
        # Save report to file (path relative to root)
        report_file = self.root_dir / "logs" / "v0.1_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        self.logger.info(f"\nDetailed report saved to: {report_file}")
        
        return all_passed
    
    def run_all_tests(self) -> bool:
        """Run all tests in sequence."""
        self.logger.info("\n🚀 Starting Version 0.1 Test Suite")
        
        # Test 1: MP Fetching
        test1_passed = self.test_mp_fetcher()
        if not test1_passed:
            self.logger.error("Test 1 failed. Stopping test suite.")
            self.generate_report()
            return False
        
        # Test 2: Structure Interpolation
        test2_passed = self.test_structure_interpolation()
        if not test2_passed:
            self.logger.error("Test 2 failed. Stopping test suite.")
            self.generate_report()
            return False
        
        # Test 3: Property Calculation
        test3_passed = self.test_property_calculation()
        
        # Test 4: Data Validation
        test4_passed = self.test_data_validation()
        
        # Generate final report
        all_passed = self.generate_report()
        
        return all_passed


def main():
    """Main execution function."""
    print("\n" + "="*70)
    print("s-CGCNN Version 0.1 Testing Suite")
    print("Data Acquisition & Structure Interpolation")
    print("="*70)
    
    tester = Version01Tester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✓ Version 0.1 is ready for deployment!")
        print("  Next step: Continue to Version 0.2 (Visualization)")
        sys.exit(0)
    else:
        print("\n✗ Version 0.1 has issues. Please fix before proceeding.")
        sys.exit(1)


if __name__ == "__main__":
    main()