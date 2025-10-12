"""
s-CGCNN v0.2 - Master Visualization Testing
==========================================

Comprehensive test suite for all visualization modules.

Test Categories:
1. Module imports and initialization
2. Data loading and validation
3. Structure viewer functionality
4. Property plotter outputs
5. Figure generator quality
6. Integration testing
s-cgcnn\tests\2. Visualization Module Testing.py
Author: Abdullah Hasan Dafa
Version: 0.2
"""

import sys
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.visualization import (
    StructureViewer,
    PropertyPlotter,
    FigureGenerator,
    ComparisonTools
)
from src.utils.logger_config import setup_logger

logger = setup_logger('visualization_testing')


class TestVisualizationModules(unittest.TestCase):
    """Master test suite for visualization modules."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.data_dir = Path('data')
        cls.cif_dir = cls.data_dir / 'structures' / 'cif'
        cls.metadata_dir = cls.data_dir / 'structures' / 'metadata'
        cls.output_dir = Path('tests/test_output')
        cls.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("=" * 70)
        logger.info("s-CGCNN v0.2 - Visualization Testing Suite")
        logger.info("=" * 70)
    
    def test_01_module_imports(self):
        """Test 1: Verify all modules import correctly."""
        logger.info("\nTEST 1: Module Imports")
        logger.info("-" * 70)
        
        try:
            # Test imports
            from src.visualization import StructureViewer
            from src.visualization import PropertyPlotter
            from src.visualization import FigureGenerator
            from src.visualization import ComparisonTools
            
            logger.info("✓ All visualization modules imported successfully")
            
            # Test dependencies
            import plotly
            import dash
            import crystal_toolkit
            import matplotlib
            import seaborn
            
            logger.info("✓ All dependencies available")
            
            self.assertTrue(True)
            
        except ImportError as e:
            logger.error(f"✗ Import failed: {e}")
            self.fail(f"Import error: {e}")
    
    def test_02_structure_viewer_init(self):
        """Test 2: StructureViewer initialization."""
        logger.info("\nTEST 2: StructureViewer Initialization")
        logger.info("-" * 70)
        
        try:
            viewer = StructureViewer(data_dir=self.data_dir)
            self.assertIsNotNone(viewer)
            logger.info("✓ StructureViewer initialized")
            
            # Load structures if available
            if self.cif_dir.exists():
                n_structures = viewer.load_structures()
                self.assertGreater(n_structures, 0)
                logger.info(f"✓ Loaded {n_structures} structures")
                
                # Test structure retrieval
                structure = viewer.get_structure(0.5)
                self.assertIsNotNone(structure)
                logger.info("✓ Structure retrieval working")
            else:
                logger.warning("⚠ CIF directory not found, skipping structure loading")
            
        except Exception as e:
            logger.error(f"✗ StructureViewer test failed: {e}")
            self.fail(str(e))
    
    def test_03_property_plotter_init(self):
        """Test 3: PropertyPlotter initialization and data loading."""
        logger.info("\nTEST 3: PropertyPlotter Initialization")
        logger.info("-" * 70)
        
        try:
            plotter = PropertyPlotter(data_dir=self.data_dir)
            self.assertIsNotNone(plotter)
            logger.info("✓ PropertyPlotter initialized")
            
            # Load data if available
            if self.metadata_dir.exists():
                data = plotter.load_data()
                self.assertIsNotNone(data)
                self.assertGreater(len(data), 0)
                logger.info(f"✓ Loaded data for {len(data)} compositions")
                
                # Check required columns
                required_cols = ['x', 'formula', 'band_gap', 'lattice_constant']
                for col in required_cols:
                    self.assertIn(col, data.columns)
                logger.info("✓ All required data columns present")
            else:
                logger.warning("⚠ Metadata directory not found, skipping data loading")
            
        except Exception as e:
            logger.error(f"✗ PropertyPlotter test failed: {e}")
            self.fail(str(e))
    
    def test_04_figure_generator_init(self):
        """Test 4: FigureGenerator initialization."""
        logger.info("\nTEST 4: FigureGenerator Initialization")
        logger.info("-" * 70)
        
        try:
            generator = FigureGenerator(data_dir=self.data_dir, style='mp')
            self.assertIsNotNone(generator)
            logger.info("✓ FigureGenerator initialized (MP style)")
            
            # Load data if available
            if self.metadata_dir.exists():
                data = generator.load_data()
                self.assertGreater(len(data), 0)
                logger.info(f"✓ Loaded data for {len(data)} compositions")
            else:
                logger.warning("⚠ Metadata directory not found, skipping data loading")
            
        except Exception as e:
            logger.error(f"✗ FigureGenerator test failed: {e}")
            self.fail(str(e))
    
    def test_05_comparison_tools_init(self):
        """Test 5: ComparisonTools initialization."""
        logger.info("\nTEST 5: ComparisonTools Initialization")
        logger.info("-" * 70)
        
        try:
            tools = ComparisonTools(data_dir=self.data_dir)
            self.assertIsNotNone(tools)
            logger.info("✓ ComparisonTools initialized")
            
            # Load data and run analysis if available
            if self.metadata_dir.exists():
                data = tools.load_data()
                self.assertGreater(len(data), 0)
                logger.info(f"✓ Loaded data for {len(data)} compositions")
                
                # Test statistics
                stats = tools.calculate_statistics()
                self.assertIsNotNone(stats)
                logger.info("✓ Statistics calculation working")
            else:
                logger.warning("⚠ Metadata directory not found, skipping data loading")
            
        except Exception as e:
            logger.error(f"✗ ComparisonTools test failed: {e}")
            self.fail(str(e))
    
    def test_06_plot_generation(self):
        """Test 6: Plot generation functionality."""
        logger.info("\nTEST 6: Plot Generation")
        logger.info("-" * 70)
        
        if not self.metadata_dir.exists():
            logger.warning("⚠ Metadata not available, skipping plot generation test")
            return
        
        try:
            plotter = PropertyPlotter(data_dir=self.data_dir)
            plotter.load_data()
            
            # Test band gap plot
            fig = plotter.plot_band_gap(show_type=True)
            self.assertIsNotNone(fig)
            logger.info("✓ Band gap plot generated")
            
            # Test lattice constant plot
            fig = plotter.plot_lattice_constant()
            self.assertIsNotNone(fig)
            logger.info("✓ Lattice constant plot generated")
            
            # Test dashboard
            fig = plotter.plot_multi_property_dashboard()
            self.assertIsNotNone(fig)
            logger.info("✓ Multi-property dashboard generated")
            
        except Exception as e:
            logger.error(f"✗ Plot generation test failed: {e}")
            self.fail(str(e))
    
    def test_07_figure_export(self):
        """Test 7: Figure export functionality."""
        logger.info("\nTEST 7: Figure Export")
        logger.info("-" * 70)
        
        if not self.metadata_dir.exists():
            logger.warning("⚠ Metadata not available, skipping figure export test")
            return
        
        try:
            generator = FigureGenerator(data_dir=self.data_dir)
            generator.load_data()
            
            # Test band gap figure
            output_path = self.output_dir / 'test_band_gap'
            generator.figure_band_gap_evolution(str(output_path), formats=['png'])
            
            self.assertTrue((self.output_dir / 'test_band_gap.png').exists())
            logger.info("✓ Band gap figure exported to PNG")
            
        except Exception as e:
            logger.error(f"✗ Figure export test failed: {e}")
            self.fail(str(e))
    
    def test_08_integration(self):
        """Test 8: Integration test - complete pipeline."""
        logger.info("\nTEST 8: Integration Test")
        logger.info("-" * 70)
        
        if not self.metadata_dir.exists():
            logger.warning("⚠ Data not available, skipping integration test")
            return
        
        try:
            # Load data
            plotter = PropertyPlotter(data_dir=self.data_dir)
            plotter.load_data()
            
            generator = FigureGenerator(data_dir=self.data_dir)
            generator.load_data()
            
            tools = ComparisonTools(data_dir=self.data_dir)
            tools.load_data()
            
            # Verify data consistency
            self.assertEqual(len(plotter.data), len(generator.data))
            self.assertEqual(len(plotter.data), len(tools.data))
            
            logger.info("✓ Data consistency verified across modules")
            logger.info("✓ Integration test passed")
            
        except Exception as e:
            logger.error(f"✗ Integration test failed: {e}")
            self.fail(str(e))
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests."""
        logger.info("\n" + "=" * 70)
        logger.info("Test Suite Complete")
        logger.info("=" * 70)


def run_tests():
    """Run all tests and generate report."""
    print("\n" + "=" * 70)
    print("  s-CGCNN v0.2 - Visualization Testing Suite")
    print("=" * 70)
    print()
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVisualizationModules)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("  ✓✓✓ ALL TESTS PASSED - VERSION 0.2 READY ✓✓✓")
    else:
        print("  ✗✗✗ SOME TESTS FAILED ✗✗✗")
        print(f"  Failures: {len(result.failures)}")
        print(f"  Errors: {len(result.errors)}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)