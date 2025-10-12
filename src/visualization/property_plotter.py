"""
Property Plotter Module
=======================

Interactive property visualization using Plotly.
Supports:
    - Band gap evolution plots
    - Lattice constant trends
    - Multi-property dashboards
    - Interactive hover tooltips
    - HTML export for sharing

Author: Abdullah Hasan Dafa
Version: 0.2
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

from ..utils.logger_config import setup_logger

logger = setup_logger(__name__)


class PropertyPlotter:
    """
    Interactive property plotter for AlₓGa₁₋ₓAs alloys.
    
    Attributes:
        data (pd.DataFrame): Property data for all compositions
        metadata (Dict[float, dict]): Detailed metadata by composition
        
    Example:
        >>> plotter = PropertyPlotter()
        >>> plotter.load_data('data/structures/metadata/')
        >>> fig = plotter.plot_band_gap()
        >>> fig.show()
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize PropertyPlotter.
        
        Args:
            data_dir: Root directory containing metadata
        """
        self.data_dir = Path(data_dir) if data_dir else Path('data')
        self.data: Optional[pd.DataFrame] = None
        self.metadata: Dict[float, dict] = {}
        
        # Color scheme (Materials Project style)
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'accent': '#2ca02c',
            'error': '#d62728',
            'grid': '#ecf0f1'
        }
        
        logger.info("PropertyPlotter initialized")
    
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
        logger.info(f"Found {len(json_files)} metadata files")
        
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
                
                # Store full metadata
                self.metadata[x] = meta
                
                # FIX: Extract properties from nested 'properties' dict (v0.1.1 format)
                props = meta.get('properties', {})
                
                # Extract key properties
                row = {
                    'x': x,
                    'formula': meta.get('formula', ''),
                    'band_gap': props.get('band_gap', np.nan),  # FIX: Direct access, not nested
                    'band_gap_type': props.get('band_gap_type', ''),  # FIX: Direct access
                    'lattice_constant': props.get('lattice_constant', np.nan),  # FIX: Direct access
                    'density': props.get('density', np.nan),  # FIX: From props
                    'space_group': meta.get('space_group', ''),
                    'data_source': meta.get('data_source', ''),
                }
                
                # Add other properties if available (from v0.1.1 properties dict)
                row['bulk_modulus'] = props.get('bulk_modulus', np.nan)
                row['shear_modulus'] = props.get('shear_modulus', np.nan)
                row['thermal_conductivity'] = props.get('thermal_conductivity', np.nan)
                row['refractive_index'] = props.get('refractive_index', np.nan)
                row['electron_mobility'] = props.get('electron_mobility', np.nan)
                row['hole_mobility'] = props.get('hole_mobility', np.nan)
                
                # Additional properties from v0.1.1
                row['band_gap_direct'] = props.get('band_gap_direct', np.nan)
                row['band_gap_indirect_X'] = props.get('band_gap_indirect_X', np.nan)
                row['electron_affinity'] = props.get('electron_affinity', np.nan)
                row['electron_effective_mass'] = props.get('electron_effective_mass', np.nan)
                row['hole_effective_mass_heavy'] = props.get('hole_effective_mass_heavy', np.nan)
                row['static_dielectric'] = props.get('static_dielectric', np.nan)
                row['optical_dielectric'] = props.get('optical_dielectric', np.nan)
                row['elastic_c11'] = props.get('elastic_c11', np.nan)
                row['elastic_c12'] = props.get('elastic_c12', np.nan)
                row['elastic_c44'] = props.get('elastic_c44', np.nan)
                row['thermal_expansion'] = props.get('thermal_expansion', np.nan)
                row['specific_heat'] = props.get('specific_heat', np.nan)
                row['debye_temperature'] = props.get('debye_temperature', np.nan)
                
                data_list.append(row)
                
            except Exception as e:
                logger.warning(f"Failed to load {json_file.name}: {e}")
                continue
        
        # Create DataFrame
        self.data = pd.DataFrame(data_list).sort_values('x').reset_index(drop=True)
        logger.info(f"Loaded data for {len(self.data)} compositions")
        
        # Diagnostic output
        if len(self.data) > 0:
            logger.info(f"Data quality: Band gap {self.data['band_gap'].notna().sum()}/{len(self.data)}, "
                    f"Lattice constant {self.data['lattice_constant'].notna().sum()}/{len(self.data)}")
        
        return self.data
    
    def plot_band_gap(self, show_type: bool = True, 
                     export_html: Optional[str] = None) -> go.Figure:
        """
        Plot band gap vs composition with direct/indirect transition.
        
        Args:
            show_type: Color by band gap type (direct/indirect)
            export_html: Path to export HTML (optional)
            
        Returns:
            Plotly figure
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        fig = go.Figure()
        
        if show_type and 'band_gap_type' in self.data.columns:
            # Separate direct and indirect
            direct = self.data[self.data['band_gap_type'] == 'direct']
            indirect = self.data[self.data['band_gap_type'] == 'indirect']
            
            # Plot direct
            fig.add_trace(go.Scatter(
                x=direct['x'],
                y=direct['band_gap'],
                mode='markers+lines',
                name='Direct',
                marker=dict(size=8, color=self.colors['primary']),
                line=dict(width=2, color=self.colors['primary']),
                hovertemplate='<b>x = %{x:.3f}</b><br>' +
                             'Band Gap = %{y:.3f} eV<br>' +
                             'Type: Direct<extra></extra>'
            ))
            
            # Plot indirect
            fig.add_trace(go.Scatter(
                x=indirect['x'],
                y=indirect['band_gap'],
                mode='markers+lines',
                name='Indirect',
                marker=dict(size=8, color=self.colors['secondary']),
                line=dict(width=2, color=self.colors['secondary']),
                hovertemplate='<b>x = %{x:.3f}</b><br>' +
                             'Band Gap = %{y:.3f} eV<br>' +
                             'Type: Indirect<extra></extra>'
            ))
            
            # Add crossover annotation (typically around x=0.45)
            crossover_x = 0.45
            fig.add_vline(x=crossover_x, line_dash="dash", 
                         line_color="gray", opacity=0.5)
            fig.add_annotation(x=crossover_x, y=self.data['band_gap'].max(),
                              text="Direct → Indirect", showarrow=False,
                              yshift=10, font=dict(size=10, color='gray'))
        else:
            # Single series plot
            fig.add_trace(go.Scatter(
                x=self.data['x'],
                y=self.data['band_gap'],
                mode='markers+lines',
                name='Band Gap',
                marker=dict(size=8, color=self.colors['primary']),
                line=dict(width=2),
                hovertemplate='<b>x = %{x:.3f}</b><br>' +
                             'Band Gap = %{y:.3f} eV<extra></extra>'
            ))
        
        # Update layout
        fig.update_layout(
            title='Band Gap Evolution: AlₓGa₁₋ₓAs',
            xaxis_title='Aluminum Fraction (x)',
            yaxis_title='Band Gap (eV)',
            template='plotly_white',
            hovermode='closest',
            font=dict(family='Arial', size=12),
            legend=dict(x=0.02, y=0.98),
            width=800,
            height=500
        )
        
        fig.update_xaxes(range=[-0.05, 1.05], dtick=0.1)
        
        # Export if requested
        if export_html:
            fig.write_html(export_html)
            logger.info(f"Band gap plot exported to {export_html}")
        
        return fig
    
    def plot_lattice_constant(self, export_html: Optional[str] = None) -> go.Figure:
        """
        Plot lattice constant vs composition (Vegard's Law).
        
        Args:
            export_html: Path to export HTML (optional)
            
        Returns:
            Plotly figure
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        fig = go.Figure()
        
        # Actual data
        fig.add_trace(go.Scatter(
            x=self.data['x'],
            y=self.data['lattice_constant'],
            mode='markers+lines',
            name='Calculated',
            marker=dict(size=8, color=self.colors['primary']),
            line=dict(width=2),
            hovertemplate='<b>x = %{x:.3f}</b><br>' +
                         'Lattice = %{y:.4f} Å<extra></extra>'
        ))
        
        # Vegard's Law (linear interpolation)
        a_GaAs = self.data[self.data['x'] == 0.0]['lattice_constant'].iloc[0]
        a_AlAs = self.data[self.data['x'] == 1.0]['lattice_constant'].iloc[0]
        x_vegard = np.linspace(0, 1, 100)
        a_vegard = a_GaAs + x_vegard * (a_AlAs - a_GaAs)
        
        fig.add_trace(go.Scatter(
            x=x_vegard,
            y=a_vegard,
            mode='lines',
            name="Vegard's Law",
            line=dict(width=2, dash='dash', color='gray'),
            hovertemplate='Vegard: %{y:.4f} Å<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title='Lattice Constant Evolution: AlₓGa₁₋ₓAs',
            xaxis_title='Aluminum Fraction (x)',
            yaxis_title='Lattice Constant (Å)',
            template='plotly_white',
            hovermode='closest',
            font=dict(family='Arial', size=12),
            legend=dict(x=0.02, y=0.02),
            width=800,
            height=500
        )
        
        fig.update_xaxes(range=[-0.05, 1.05], dtick=0.1)
        
        # Export if requested
        if export_html:
            fig.write_html(export_html)
            logger.info(f"Lattice constant plot exported to {export_html}")
        
        return fig
    
    def plot_multi_property_dashboard(self, 
                                     properties: Optional[List[str]] = None,
                                     export_html: Optional[str] = None) -> go.Figure:
        """
        Create multi-property dashboard (2x3 subplot grid).
        
        Args:
            properties: List of properties to plot (default: 6 key properties)
            export_html: Path to export HTML (optional)
            
        Returns:
            Plotly figure with subplots
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        # Default properties
        if properties is None:
            properties = [
                'band_gap',
                'lattice_constant',
                'bulk_modulus',
                'thermal_conductivity',
                'refractive_index',
                'electron_mobility'
            ]
        
        # Property labels and units
        prop_config = {
            'band_gap': ('Band Gap', 'eV'),
            'lattice_constant': ('Lattice Constant', 'Å'),
            'bulk_modulus': ('Bulk Modulus', 'GPa'),
            'thermal_conductivity': ('Thermal Conductivity', 'W/m·K'),
            'refractive_index': ('Refractive Index', ''),
            'electron_mobility': ('Electron Mobility', 'cm²/V·s')
        }
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=[prop_config.get(p, (p, ''))[0] for p in properties],
            vertical_spacing=0.12,
            horizontal_spacing=0.10
        )
        
        # Plot each property
        for idx, prop in enumerate(properties):
            row = idx // 3 + 1
            col = idx % 3 + 1
            
            if prop in self.data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=self.data['x'],
                        y=self.data[prop],
                        mode='markers+lines',
                        name=prop_config.get(prop, (prop, ''))[0],
                        marker=dict(size=6, color=self.colors['primary']),
                        line=dict(width=1.5),
                        showlegend=False,
                        hovertemplate=f'x = %{{x:.3f}}<br>{prop} = %{{y:.3f}}<extra></extra>'
                    ),
                    row=row, col=col
                )
                
                # Update axes
                fig.update_xaxes(title_text='x', row=row, col=col, range=[-0.05, 1.05])
                unit = prop_config.get(prop, ('', ''))[1]
                ylabel = unit if unit else prop
                fig.update_yaxes(title_text=ylabel, row=row, col=col)
        
        # Update layout
        fig.update_layout(
            title_text='Multi-Property Dashboard: AlₓGa₁₋ₓAs',
            template='plotly_white',
            font=dict(family='Arial', size=10),
            height=700,
            width=1200
        )
        
        # Export if requested
        if export_html:
            fig.write_html(export_html)
            logger.info(f"Dashboard exported to {export_html}")
        
        return fig
    
    def plot_comparison(self, property_name: str, 
                       sources: List[str] = ['literature', 'mp-api'],
                       export_html: Optional[str] = None) -> go.Figure:
        """
        Compare property values from different data sources.
        
        Args:
            property_name: Property to compare
            sources: Data sources to compare
            export_html: Path to export HTML (optional)
            
        Returns:
            Plotly figure
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        fig = go.Figure()
        
        # Plot each source
        for source in sources:
            source_data = self.data[self.data['data_source'] == source]
            
            if len(source_data) > 0:
                fig.add_trace(go.Scatter(
                    x=source_data['x'],
                    y=source_data[property_name],
                    mode='markers+lines',
                    name=source.capitalize(),
                    marker=dict(size=8),
                    line=dict(width=2),
                    hovertemplate=f'<b>x = %{{x:.3f}}</b><br>' +
                                 f'{property_name} = %{{y:.3f}}<br>' +
                                 f'Source: {source}<extra></extra>'
                ))
        
        # Update layout
        fig.update_layout(
            title=f'{property_name.replace("_", " ").title()} Comparison: Literature vs MP-API',
            xaxis_title='Aluminum Fraction (x)',
            yaxis_title=property_name.replace('_', ' ').title(),
            template='plotly_white',
            hovermode='closest',
            font=dict(family='Arial', size=12),
            legend=dict(x=0.02, y=0.98),
            width=800,
            height=500
        )
        
        # Export if requested
        if export_html:
            fig.write_html(export_html)
            logger.info(f"Comparison plot exported to {export_html}")
        
        return fig
    
    def export_all_plots(self, output_dir: str):
        """
        Generate and export all standard plots.
        
        Args:
            output_dir: Directory to save plots
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Exporting all plots to {output_dir}")
        
        # Band gap
        self.plot_band_gap(export_html=str(output_path / 'band_gap.html'))
        
        # Lattice constant
        self.plot_lattice_constant(export_html=str(output_path / 'lattice_constant.html'))
        
        # Dashboard
        self.plot_multi_property_dashboard(export_html=str(output_path / 'dashboard.html'))
        
        logger.info("All plots exported successfully")


if __name__ == "__main__":
    # Demo usage
    plotter = PropertyPlotter()
    plotter.load_data()
    print(f"Loaded data for {len(plotter.data)} compositions")
    print(f"Available properties: {list(plotter.data.columns)}")