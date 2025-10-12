"""
s-CGCNN Version 0.2 - Master Pipeline
=====================================

Complete visualization pipeline for AlₓGa₁₋ₓAs analysis.
Generates all interactive plots, publication figures, and reports.

Usage:
    python run_version_0.2.py [--mode MODE]
    
Modes:
    - all: Generate everything (default)
    - interactive: Interactive plots only
    - publication: Publication figures only
    - app: Launch Dash app

Author: Abdullah Hasan Dafa
Version: 0.2
"""

import argparse
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.visualization import (
    StructureViewer,
    PropertyPlotter,
    FigureGenerator,
    ComparisonTools
)
from src.utils.logger_config import setup_logger

logger = setup_logger(__name__)


def run_interactive_visualization(data_dir: str = 'data', 
                                  output_dir: str = 'results/interactive'):
    """
    Generate interactive visualizations with Plotly.
    
    Args:
        data_dir: Data directory
        output_dir: Output directory for HTML files
    """
    logger.info("=" * 70)
    logger.info("STEP 1: Interactive Visualization (Plotly)")
    logger.info("=" * 70)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize plotter
    plotter = PropertyPlotter(data_dir)
    plotter.load_data()
    
    logger.info(f"Loaded data for {len(plotter.data)} compositions")
    
    # Generate interactive plots
    logger.info("Generating band gap plot...")
    plotter.plot_band_gap(export_html=str(output_path / 'band_gap.html'))
    
    logger.info("Generating lattice constant plot...")
    plotter.plot_lattice_constant(export_html=str(output_path / 'lattice_constant.html'))
    
    logger.info("Generating multi-property dashboard...")
    plotter.plot_multi_property_dashboard(export_html=str(output_path / 'dashboard.html'))
    
    logger.info(f"✅ Interactive plots saved to {output_dir}")


def run_publication_figures(data_dir: str = 'data',
                           output_dir: str = 'results/figures'):
    """
    Generate publication-ready figures.
    
    Args:
        data_dir: Data directory
        output_dir: Output directory for figures
    """
    logger.info("=" * 70)
    logger.info("STEP 2: Publication-Ready Figures")
    logger.info("=" * 70)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize generator
    generator = FigureGenerator(data_dir, style='mp')
    generator.load_data()
    
    logger.info(f"Loaded data for {len(generator.data)} compositions")
    
    # Generate all figures
    logger.info("Generating all publication figures...")
    generator.generate_all_figures(output_dir, formats=['pdf', 'png', 'svg'])
    
    logger.info(f"✅ Publication figures saved to {output_dir}")


def run_analysis(data_dir: str = 'data',
                output_dir: str = 'results/analysis'):
    """
    Run comprehensive analysis.
    
    Args:
        data_dir: Data directory
        output_dir: Output directory for analysis results
    """
    logger.info("=" * 70)
    logger.info("STEP 3: Comprehensive Analysis")
    logger.info("=" * 70)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize tools
    tools = ComparisonTools(data_dir)
    tools.load_data()
    
    logger.info(f"Loaded data for {len(tools.data)} compositions")
    
    # Generate correlation heatmap
    logger.info("Generating correlation heatmap...")
    tools.plot_correlation_heatmap(
        output_path=str(output_path / 'correlation_heatmap.png')
    )
    
    # Export summary report
    logger.info("Generating summary report...")
    tools.export_summary_report(str(output_path / 'summary_report.txt'))
    
    # Statistics
    logger.info("Calculating statistics...")
    stats = tools.calculate_statistics()
    stats.to_csv(output_path / 'property_statistics.csv')
    
    logger.info(f"✅ Analysis results saved to {output_dir}")


def launch_dash_app():
    """
    Launch the interactive Dash application.
    """
    logger.info("=" * 70)
    logger.info("Launching Structure Viewer App")
    logger.info("=" * 70)
    
    viewer = StructureViewer()
    n_structures = viewer.load_structures()
    
    logger.info(f"Loaded {n_structures} structures")
    
    viewer.create_dash_app()
    
    print("\n" + "=" * 70)
    print("  s-CGCNN Interactive Structure Viewer")
    print("=" * 70)
    print(f"  Loaded {n_structures} AlₓGa₁₋ₓAs structures")
    print()
    print("  Opening app at: http://localhost:8050")
    print("  Press Ctrl+C to stop the server")
    print("=" * 70 + "\n")
    
    viewer.run_app(debug=False, port=8050)


def main():
    """
    Main execution function.
    """
    parser = argparse.ArgumentParser(
        description='s-CGCNN v0.2 Visualization Pipeline'
    )
    parser.add_argument(
        '--mode',
        type=str,
        default='all',
        choices=['all', 'interactive', 'publication', 'analysis', 'app'],
        help='Execution mode (default: all)'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='data',
        help='Data directory (default: data)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='results',
        help='Output directory (default: results)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("  s-CGCNN Version 0.2 - Visualization Pipeline")
    print("=" * 70)
    print(f"  Mode: {args.mode}")
    print(f"  Data Directory: {args.data_dir}")
    print(f"  Output Directory: {args.output_dir}")
    print("=" * 70 + "\n")
    
    try:
        if args.mode == 'app':
            launch_dash_app()
        elif args.mode == 'all':
            # Run complete pipeline
            run_interactive_visualization(
                args.data_dir, 
                f"{args.output_dir}/interactive"
            )
            run_publication_figures(
                args.data_dir,
                f"{args.output_dir}/figures"
            )
            run_analysis(
                args.data_dir,
                f"{args.output_dir}/analysis"
            )
            
            print("\n" + "=" * 70)
            print("  ✅ PIPELINE COMPLETE!")
            print("=" * 70)
            print(f"  Results saved to: {args.output_dir}/")
            print("  - Interactive plots: interactive/")
            print("  - Publication figures: figures/")
            print("  - Analysis results: analysis/")
            print("=" * 70 + "\n")
            
        elif args.mode == 'interactive':
            run_interactive_visualization(
                args.data_dir,
                f"{args.output_dir}/interactive"
            )
        elif args.mode == 'publication':
            run_publication_figures(
                args.data_dir,
                f"{args.output_dir}/figures"
            )
        elif args.mode == 'analysis':
            run_analysis(
                args.data_dir,
                f"{args.output_dir}/analysis"
            )
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()