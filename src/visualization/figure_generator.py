"""
Figure Generator Module
=======================

Publication-ready figure generation with matplotlib and seaborn.
Supports:
    - High-resolution output (300+ DPI)
    - Vector graphics (PDF/SVG)
    - Materials Project style
    - Academic journal formatting
    - Batch figure generation

Author: Abdullah Hasan Dafa
Version: 0.2
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Rectangle
import seaborn as sns

from ..utils.logger_config import setup_logger

logger = setup_logger(__name__)


# Configure matplotlib for publication-quality figures
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
mpl.rcParams['font.size'] = 10
mpl.rcParams['axes.labelsize'] = 11
mpl.rcParams['axes.titlesize'] = 12
mpl.rcParams['xtick.labelsize'] = 9
mpl.rcParams['ytick.labelsize'] = 9
mpl.rcParams['legend.fontsize'] = 9
mpl.rcParams['figure.dpi'] = 150  # Display DPI
mpl.rcParams['savefig.dpi'] = 300  # Save DPI
mpl.rcParams['savefig.bbox'] = 'tight'
mpl.rcParams['savefig.pad_inches'] = 0.1


class FigureGenerator:
    """
    Generate publication-ready figures for AlₓGa₁₋ₓAs research.
    
    Attributes:
        data (pd.DataFrame): Property data
        style (str): Figure style ('default', 'mp', 'nature')
        
    Example:
        >>> generator = FigureGenerator()
        >>> generator.load_data('data/structures/metadata/')
        >>> generator.generate_all_figures('results/figures/')
    """
    
    def __init__(self, data_dir: Optional[str] = None, style: str = 'mp'):
        """
        Initialize FigureGenerator.
        
        Args:
            data_dir: Root directory containing metadata
            style: Figure style ('default', 'mp', 'nature')
        """
        self.data_dir = Path(data_dir) if data_dir else Path('data')
        self.data: Optional[pd.DataFrame] = None
        self.style = style
        
        # Set seaborn style
        if style == 'mp':
            # Materials Project style
            sns.set_style("whitegrid")
            self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        elif style == 'nature':
            # Nature journal style
            sns.set_style("ticks")
            self.colors = ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F']
        else:
            sns.set_style("darkgrid")
            self.colors = sns.color_palette("husl", 5)
        
        logger.info(f"FigureGenerator initialized with '{style}' style")
    
    def load_data(self, metadata_dir: Optional[str] = None) -> pd.DataFrame:
        """
        Load property data from JSON metadata files.
        
        Args:
            metadata_dir: Path to metadata directory
            
        Returns:
            DataFrame with all properties
        """
        if metadata_dir is None:
            metadata_dir = self.data_dir / 'structures' / 'metadata'
        else:
            metadata_dir = Path(metadata_dir)
        
        if not metadata_dir.exists():
            raise FileNotFoundError(f"Metadata directory not found: {metadata_dir}")
        
        # Load all JSON files
        json_files = sorted(metadata_dir.glob('*.json'))
        data_list = []
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    meta = json.load(f)
                
                # Extract composition (handle multiple JSON formats)
                x = None
                if isinstance(meta, dict):
                    # FIX: Try x_value first (v0.1.1 format)
                    if 'x_value' in meta:
                        x = meta['x_value']
                    # Try nested 'composition' dict
                    elif 'composition' in meta and isinstance(meta['composition'], dict):
                        x = meta['composition'].get('x')
                    # Try direct 'x' key
                    elif 'x' in meta:
                        x = meta['x']
                    # Try extracting from filename as fallback
                    if x is None:
                        stem = json_file.stem
                        if '_x_' in stem:
                            x_part = stem.split('_x_')[1]
                            x = float(x_part.replace('_', '.'))

                if x is None:
                    continue
                
                # FIX: Extract properties from nested 'properties' dict (v0.1.1 format)
                props = meta.get('properties', {})
                
                row = {
                    'x': x,
                    'formula': meta.get('formula', ''),
                    'band_gap': props.get('band_gap', np.nan),  # FIX: Direct access
                    'band_gap_type': props.get('band_gap_type', ''),  # FIX: Direct access
                    'lattice_constant': props.get('lattice_constant', np.nan),  # FIX: Direct access
                    'data_source': meta.get('data_source', ''),
                }
                
                # Add optional properties (from v0.1.1 properties dict)
                row['bulk_modulus'] = props.get('bulk_modulus', np.nan)
                row['shear_modulus'] = props.get('shear_modulus', np.nan)
                row['thermal_conductivity'] = props.get('thermal_conductivity', np.nan)
                row['refractive_index'] = props.get('refractive_index', np.nan)
                row['electron_mobility'] = props.get('electron_mobility', np.nan)
                row['hole_mobility'] = props.get('hole_mobility', np.nan)
                row['density'] = props.get('density', np.nan)
                
                # Additional properties for comprehensive figures
                row['band_gap_direct'] = props.get('band_gap_direct', np.nan)
                row['band_gap_indirect_X'] = props.get('band_gap_indirect_X', np.nan)
                row['electron_affinity'] = props.get('electron_affinity', np.nan)
                row['electron_effective_mass'] = props.get('electron_effective_mass', np.nan)
                row['static_dielectric'] = props.get('static_dielectric', np.nan)
                row['optical_dielectric'] = props.get('optical_dielectric', np.nan)
                
                data_list.append(row)
                
            except Exception as e:
                logger.warning(f"Failed to load {json_file.name}: {e}")
                continue
        
        self.data = pd.DataFrame(data_list).sort_values('x').reset_index(drop=True)
        logger.info(f"Loaded data for {len(self.data)} compositions")
        
        return self.data
    
    def figure_band_gap_evolution(self, output_path: str, 
                                  formats: List[str] = ['pdf', 'png']):
        """
        Generate Figure 1: Band gap evolution with direct/indirect transition.
        
        Args:
            output_path: Output file path (without extension)
            formats: List of output formats
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        fig, ax = plt.subplots(figsize=(6, 4))
        
        # Separate direct and indirect
        direct = self.data[self.data['band_gap_type'] == 'direct']
        indirect = self.data[self.data['band_gap_type'] == 'indirect']
        
        # Plot data
        ax.plot(direct['x'], direct['band_gap'], 'o-', 
               color=self.colors[0], linewidth=2, markersize=6, 
               label='Direct', markeredgecolor='white', markeredgewidth=0.5)
        
        ax.plot(indirect['x'], indirect['band_gap'], 's-', 
               color=self.colors[1], linewidth=2, markersize=6,
               label='Indirect', markeredgecolor='white', markeredgewidth=0.5)
        
        # Add crossover region
        crossover_x = 0.45
        ax.axvline(crossover_x, color='gray', linestyle='--', 
                  linewidth=1, alpha=0.5, zorder=0)
        ax.text(crossover_x, ax.get_ylim()[1] * 0.95, 
               'Direct → Indirect\nCrossover',
               ha='center', va='top', fontsize=8, 
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Labels and formatting
        ax.set_xlabel('Aluminum Fraction (x)', fontweight='bold')
        ax.set_ylabel('Band Gap (eV)', fontweight='bold')
        ax.set_title('Band Gap Evolution: Al$_{x}$Ga$_{1-x}$As', 
                    fontweight='bold', pad=10)
        
        ax.set_xlim(-0.05, 1.05)
        ax.set_xticks(np.arange(0, 1.1, 0.2))
        ax.grid(True, alpha=0.3, linestyle=':')
        ax.legend(loc='best', frameon=True, shadow=False)
        
        # Add annotations for endpoints (with safety checks)
        if len(direct) > 0:
            gaas_bg = direct['band_gap'].iloc[0]
            ax.annotate('GaAs', xy=(0, gaas_bg), 
                       xytext=(-10, 10), textcoords='offset points',
                       fontsize=9, fontweight='bold')
        elif len(indirect) > 0 and 0.0 in indirect['x'].values:
            # GaAs might be in indirect data
            gaas_data = indirect[indirect['x'] == 0.0]
            if len(gaas_data) > 0:
                gaas_bg = gaas_data['band_gap'].iloc[0]
                ax.annotate('GaAs', xy=(0, gaas_bg), 
                           xytext=(-10, 10), textcoords='offset points',
                           fontsize=9, fontweight='bold')
        
        if len(indirect) > 0:
            alas_bg = indirect['band_gap'].iloc[-1]
            ax.annotate('AlAs', xy=(1, alas_bg), 
                       xytext=(10, -10), textcoords='offset points',
                       fontsize=9, fontweight='bold')
        elif len(direct) > 0 and 1.0 in direct['x'].values:
            # AlAs might be in direct data
            alas_data = direct[direct['x'] == 1.0]
            if len(alas_data) > 0:
                alas_bg = alas_data['band_gap'].iloc[0]
                ax.annotate('AlAs', xy=(1, alas_bg), 
                           xytext=(10, -10), textcoords='offset points',
                           fontsize=9, fontweight='bold')
        
        plt.tight_layout()
        
        # Save in multiple formats
        for fmt in formats:
            save_path = f"{output_path}.{fmt}"
            plt.savefig(save_path, format=fmt, dpi=300, bbox_inches='tight')
            logger.info(f"Saved band gap figure: {save_path}")
        
        plt.close()
    
    def figure_lattice_constant(self, output_path: str,
                               formats: List[str] = ['pdf', 'png']):
        """
        Generate Figure 2: Lattice constant with Vegard's Law.
        
        Args:
            output_path: Output file path (without extension)
            formats: List of output formats
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        fig, ax = plt.subplots(figsize=(6, 4))
        
        # Actual data
        ax.plot(self.data['x'], self.data['lattice_constant'], 'o-',
               color=self.colors[0], linewidth=2, markersize=6,
               label='Calculated', markeredgecolor='white', markeredgewidth=0.5)
        
        # Vegard's Law
        a_GaAs = self.data[self.data['x'] == 0.0]['lattice_constant'].iloc[0]
        a_AlAs = self.data[self.data['x'] == 1.0]['lattice_constant'].iloc[0]
        x_vegard = np.linspace(0, 1, 100)
        a_vegard = a_GaAs + x_vegard * (a_AlAs - a_GaAs)
        
        ax.plot(x_vegard, a_vegard, '--', color='gray', linewidth=2,
               label="Vegard's Law", alpha=0.7)
        
        # Labels
        ax.set_xlabel('Aluminum Fraction (x)', fontweight='bold')
        ax.set_ylabel('Lattice Constant (Å)', fontweight='bold')
        ax.set_title('Lattice Constant Evolution: Al$_{x}$Ga$_{1-x}$As',
                    fontweight='bold', pad=10)
        
        ax.set_xlim(-0.05, 1.05)
        ax.set_xticks(np.arange(0, 1.1, 0.2))
        ax.grid(True, alpha=0.3, linestyle=':')
        ax.legend(loc='best', frameon=True)
        
        # Add values at endpoints
        ax.text(0, a_GaAs, f'{a_GaAs:.3f} Å', 
               ha='right', va='bottom', fontsize=8)
        ax.text(1, a_AlAs, f'{a_AlAs:.3f} Å',
               ha='left', va='top', fontsize=8)
        
        plt.tight_layout()
        
        for fmt in formats:
            save_path = f"{output_path}.{fmt}"
            plt.savefig(save_path, format=fmt, dpi=300, bbox_inches='tight')
            logger.info(f"Saved lattice constant figure: {save_path}")
        
        plt.close()
    
    def figure_multi_property(self, output_path: str,
                             properties: Optional[List[str]] = None,
                             formats: List[str] = ['pdf', 'png']):
        """
        Generate Figure 3: Multi-property panel (2x3 grid).
        
        Args:
            output_path: Output file path (without extension)
            properties: List of 6 properties to plot
            formats: List of output formats
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        if properties is None:
            properties = [
                'band_gap', 'lattice_constant', 'bulk_modulus',
                'thermal_conductivity', 'refractive_index', 'electron_mobility'
            ]
        
        # Property labels
        labels = {
            'band_gap': ('Band Gap', 'eV'),
            'lattice_constant': ('Lattice Constant', 'Å'),
            'bulk_modulus': ('Bulk Modulus', 'GPa'),
            'thermal_conductivity': ('Thermal Conductivity', 'W/m·K'),
            'refractive_index': ('Refractive Index', ''),
            'electron_mobility': ('Electron Mobility', 'cm²/V·s')
        }
        
        fig, axes = plt.subplots(2, 3, figsize=(12, 7))
        axes = axes.flatten()
        
        for idx, prop in enumerate(properties):
            ax = axes[idx]
            
            if prop in self.data.columns:
                ax.plot(self.data['x'], self.data[prop], 'o-',
                       color=self.colors[idx % len(self.colors)],
                       linewidth=1.5, markersize=5,
                       markeredgecolor='white', markeredgewidth=0.5)
                
                label, unit = labels.get(prop, (prop, ''))
                ax.set_xlabel('x', fontweight='bold', fontsize=9)
                ylabel = f'{label}' if not unit else f'{label} ({unit})'
                ax.set_ylabel(ylabel, fontweight='bold', fontsize=9)
                ax.set_title(label, fontweight='bold', fontsize=10)
                
                ax.set_xlim(-0.05, 1.05)
                ax.grid(True, alpha=0.2, linestyle=':')
            else:
                ax.text(0.5, 0.5, f'{prop}\nNo Data',
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_xticks([])
                ax.set_yticks([])
        
        plt.suptitle('Property Evolution: Al$_{x}$Ga$_{1-x}$As',
                    fontweight='bold', fontsize=14, y=0.98)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        for fmt in formats:
            save_path = f"{output_path}.{fmt}"
            plt.savefig(save_path, format=fmt, dpi=300, bbox_inches='tight')
            logger.info(f"Saved multi-property figure: {save_path}")
        
        plt.close()
    
    def figure_comparison(self, output_path: str, property_name: str = 'band_gap',
                         formats: List[str] = ['pdf', 'png']):
        """
        Generate Figure 4: Literature vs MP-API comparison.
        
        Args:
            output_path: Output file path (without extension)
            property_name: Property to compare
            formats: List of output formats
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        fig, ax = plt.subplots(figsize=(6, 4))
        
        # Separate by source
        sources = self.data['data_source'].unique()
        colors_map = {'literature': self.colors[0], 'mp-api': self.colors[1]}
        
        for source in sources:
            source_data = self.data[self.data['data_source'] == source]
            ax.plot(source_data['x'], source_data[property_name], 'o-',
                   color=colors_map.get(source, self.colors[2]),
                   linewidth=2, markersize=6, label=source.capitalize(),
                   markeredgecolor='white', markeredgewidth=0.5)
        
        ax.set_xlabel('Aluminum Fraction (x)', fontweight='bold')
        ax.set_ylabel(property_name.replace('_', ' ').title(), fontweight='bold')
        ax.set_title(f'{property_name.replace("_", " ").title()} Comparison',
                    fontweight='bold', pad=10)
        
        ax.set_xlim(-0.05, 1.05)
        ax.grid(True, alpha=0.3, linestyle=':')
        ax.legend(loc='best', frameon=True)
        
        plt.tight_layout()
        
        for fmt in formats:
            save_path = f"{output_path}.{fmt}"
            plt.savefig(save_path, format=fmt, dpi=300, bbox_inches='tight')
            logger.info(f"Saved comparison figure: {save_path}")
        
        plt.close()
    
    def generate_all_figures(self, output_dir: str, 
                            formats: List[str] = ['pdf', 'png', 'svg']):
        """
        Generate all publication figures.
        
        Args:
            output_dir: Output directory
            formats: List of output formats
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating all figures in {output_dir}")
        
        # Figure 1: Band gap
        self.figure_band_gap_evolution(
            str(output_path / 'figure1_band_gap'),
            formats=formats
        )
        
        # Figure 2: Lattice constant
        self.figure_lattice_constant(
            str(output_path / 'figure2_lattice'),
            formats=formats
        )
        
        # Figure 3: Multi-property
        self.figure_multi_property(
            str(output_path / 'figure3_properties'),
            formats=formats
        )
        
        # Figure 4: Comparison
        self.figure_comparison(
            str(output_path / 'figure4_comparison'),
            property_name='band_gap',
            formats=formats
        )
        
        logger.info("All figures generated successfully")


if __name__ == "__main__":
    # Demo usage
    generator = FigureGenerator(style='mp')
    generator.load_data()
    print(f"Loaded data for {len(generator.data)} compositions")
    print("Ready to generate figures")