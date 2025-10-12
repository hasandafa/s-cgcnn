"""
Structure Viewer Module
=======================

3D interactive structure visualization using Crystal-toolkit and Dash.

NOTE: Crystal-toolkit has compatibility issues with newer pymatgen versions.
If crystal-toolkit is not available, a simplified 3D viewer using Plotly
will be used instead.

Supports:
    - Interactive 3D structure display
    - Composition selector (dropdown)
    - Atom labeling and bond visualization
    - High-resolution export (PNG/SVG)
    - Dash app integration

Author: Abdullah Hasan Dafa
Version: 0.2
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import json

import numpy as np
from pymatgen.core import Structure
import plotly.graph_objects as go

# Try to import crystal_toolkit, but make it optional
CRYSTAL_TOOLKIT_AVAILABLE = False
try:
    import crystal_toolkit.components as ctc
    from crystal_toolkit.settings import SETTINGS
    import dash
    from dash import dcc, html, Input, Output, State
    CRYSTAL_TOOLKIT_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    import warnings
    warnings.warn(f"Crystal-toolkit not available: {e}. 3D viewer will be limited.", UserWarning)
    # Import dash anyway for basic functionality
    try:
        import dash
        from dash import dcc, html, Input, Output, State
    except ImportError:
        pass

from ..utils.logger_config import setup_logger

logger = setup_logger(__name__)


def load_structure_from_cif(cif_path: str) -> Structure:
    """
    Load structure from CIF file using pymatgen.
    
    Args:
        cif_path: Path to CIF file
        
    Returns:
        Structure object
    """
    return Structure.from_file(cif_path)


class StructureViewer:
    """
    Interactive 3D structure viewer for AlₓGa₁₋ₓAs alloys.
    
    Attributes:
        structures (Dict[float, Structure]): Loaded structures by composition
        metadata (Dict[float, dict]): Structure metadata by composition
        app (dash.Dash): Dash application instance
        
    Example:
        >>> viewer = StructureViewer()
        >>> viewer.load_structures('data/structures/cif/')
        >>> viewer.create_dash_app()
        >>> viewer.run_app()
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize StructureViewer.
        
        Args:
            data_dir: Root directory containing structures/ folder
        """
        self.data_dir = Path(data_dir) if data_dir else Path('data')
        self.structures: Dict[float, Structure] = {}
        self.metadata: Dict[float, dict] = {}
        self.app: Optional[dash.Dash] = None
        
        logger.info("StructureViewer initialized")
    
    def load_structures(self, cif_dir: Optional[str] = None) -> int:
        """
        Load all CIF structures from directory.
        
        Args:
            cif_dir: Path to CIF directory (default: data/structures/cif/)
            
        Returns:
            Number of structures loaded
        """
        if cif_dir is None:
            cif_dir = self.data_dir / 'structures' / 'cif'
        else:
            cif_dir = Path(cif_dir)
        
        if not cif_dir.exists():
            raise FileNotFoundError(f"CIF directory not found: {cif_dir}")
        
        # Load all CIF files
        cif_files = sorted(cif_dir.glob('*.cif'))
        logger.info(f"Found {len(cif_files)} CIF files in {cif_dir}")
        
        for cif_file in cif_files:
            try:
                # Extract composition from filename
                # Handle both formats: AlGaAs_x0.500 or AlGaAs_x_0_500
                stem = cif_file.stem
                if '_x_' in stem:
                    # Format: AlGaAs_x_0_500 -> 0.500
                    x_part = stem.split('_x_')[1]
                    x_comp = float(x_part.replace('_', '.'))
                elif '_x' in stem:
                    # Format: AlGaAs_x0.500 -> 0.500  
                    x_comp = float(stem.split('_x')[1])
                else:
                    logger.warning(f"Cannot parse composition from {cif_file.name}")
                    continue
                
                # Load structure
                structure = load_structure_from_cif(str(cif_file))
                self.structures[x_comp] = structure
                
                # Load corresponding metadata
                metadata_file = cif_dir.parent / 'metadata' / f"{cif_file.stem}.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        self.metadata[x_comp] = json.load(f)
                
            except Exception as e:
                logger.warning(f"Failed to load {cif_file.name}: {e}")
                continue
        
        logger.info(f"Successfully loaded {len(self.structures)} structures")
        return len(self.structures)
    
    def get_structure(self, x: float) -> Optional[Structure]:
        """
        Get structure for specific composition.
        
        Args:
            x: Aluminum fraction (0.0 to 1.0)
            
        Returns:
            Structure object or None if not found
        """
        # Find closest composition
        if x in self.structures:
            return self.structures[x]
        
        # Find nearest composition
        closest_x = min(self.structures.keys(), key=lambda k: abs(k - x))
        logger.info(f"Requested x={x:.3f}, using closest x={closest_x:.3f}")
        return self.structures[closest_x]
    
    def create_structure_component(self, x: float):
        """
        Create Crystal-toolkit structure component.
        
        Args:
            x: Aluminum fraction
            
        Returns:
            StructureMoleculeComponent for Dash integration or None
        """
        structure = self.get_structure(x)
        if structure is None:
            raise ValueError(f"No structure found for x={x}")
        
        if not CRYSTAL_TOOLKIT_AVAILABLE:
            logger.warning("Crystal-toolkit not available. Cannot create structure component.")
            return None
        
        # Create component with customized settings
        struct_component = ctc.StructureMoleculeComponent(
            structure,
            id=f"structure_x{x:.3f}",
            scene_settings={
                "enableZoom": True,
                "defaultZoom": 1.0,
                "zoomToFit2D": True,
                "staticScene": False,
                "toggleVisibility": {
                    "atoms": True,
                    "bonds": True,
                    "polyhedra": False,
                    "unit_cell": True
                }
            }
        )
        
        return struct_component
    
    def create_simple_3d_plot(self, x: float) -> go.Figure:
        """
        Create a simple 3D scatter plot of structure (fallback method).
        
        Args:
            x: Aluminum fraction
            
        Returns:
            Plotly Figure with 3D scatter plot
        """
        structure = self.get_structure(x)
        if structure is None:
            raise ValueError(f"No structure found for x={x}")
        
        # Extract atom positions and types
        coords = []
        elements = []
        colors_map = {'Al': 'blue', 'Ga': 'red', 'As': 'green'}
        colors = []
        
        for site in structure:
            coords.append(site.coords)
            element = site.specie.symbol
            elements.append(element)
            colors.append(colors_map.get(element, 'gray'))
        
        coords = np.array(coords)
        
        # Create 3D scatter plot
        fig = go.Figure(data=[go.Scatter3d(
            x=coords[:, 0],
            y=coords[:, 1],
            z=coords[:, 2],
            mode='markers',
            marker=dict(
                size=10,
                color=colors,
                line=dict(color='black', width=1)
            ),
            text=[f"{el}<br>({c[0]:.2f}, {c[1]:.2f}, {c[2]:.2f})" 
                  for el, c in zip(elements, coords)],
            hoverinfo='text'
        )])
        
        # Add unit cell outline
        lattice = structure.lattice
        vertices = [
            [0, 0, 0],
            [lattice.a, 0, 0],
            [lattice.a, lattice.b, 0],
            [0, lattice.b, 0],
            [0, 0, lattice.c],
            [lattice.a, 0, lattice.c],
            [lattice.a, lattice.b, lattice.c],
            [0, lattice.b, lattice.c]
        ]
        
        # Draw unit cell edges
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # Bottom
            (4, 5), (5, 6), (6, 7), (7, 4),  # Top
            (0, 4), (1, 5), (2, 6), (3, 7)   # Sides
        ]
        
        for edge in edges:
            v1, v2 = vertices[edge[0]], vertices[edge[1]]
            fig.add_trace(go.Scatter3d(
                x=[v1[0], v2[0]],
                y=[v1[1], v2[1]],
                z=[v1[2], v2[2]],
                mode='lines',
                line=dict(color='black', width=2),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        fig.update_layout(
            title=f'Al<sub>{x:.3f}</sub>Ga<sub>{1-x:.3f}</sub>As Structure',
            scene=dict(
                xaxis_title='X (Å)',
                yaxis_title='Y (Å)',
                zaxis_title='Z (Å)',
                aspectmode='data'
            ),
            width=800,
            height=600
        )
        
        return fig
    
    def create_dash_app(self, port: int = 8050) -> dash.Dash:
        """
        Create Dash application for interactive viewing.
        
        Args:
            port: Port number for the app
            
        Returns:
            Dash application instance
        """
        # Initialize Dash app
        # Important: Don't use __name__ as it references this module which imports crystal_toolkit
        self.app = dash.Dash(
            "structure_viewer_app",
            title="s-CGCNN Structure Viewer",
            suppress_callback_exceptions=True
        )
        
        # Get available compositions
        compositions = sorted(self.structures.keys())
        
        # Initial composition
        initial_x = 0.5 if 0.5 in compositions else compositions[0]
        
        if CRYSTAL_TOOLKIT_AVAILABLE:
            # Use Crystal-toolkit component
            struct_component = self.create_structure_component(initial_x)
            structure_display = struct_component.layout()
        else:
            # Use simple 3D plot
            logger.info("Using simple 3D plot (Crystal-toolkit not available)")
            fig = self.create_simple_3d_plot(initial_x)
            structure_display = dcc.Graph(id='structure-graph', figure=fig)
        
        # App layout
        self.app.layout = html.Div([
            html.H1("AlₓGa₁₋ₓAs Interactive Structure Viewer", 
                    style={'textAlign': 'center', 'color': '#2c3e50'}),
            
            html.Hr(),
            
            # Composition selector
            html.Div([
                html.Label("Select Aluminum Fraction (x):", 
                          style={'fontWeight': 'bold', 'fontSize': '16px'}),
                dcc.Dropdown(
                    id='composition-dropdown',
                    options=[{'label': f'x = {x:.3f}', 'value': x} 
                            for x in compositions],
                    value=initial_x,
                    clearable=False,
                    style={'width': '300px'}
                )
            ], style={'padding': '20px'}),
            
            # Structure display
            html.Div([
                html.Div(id='structure-container', children=[structure_display]),
            ], style={'padding': '20px'}),
            
            # Property information
            html.Div(id='property-info', style={
                'padding': '20px',
                'backgroundColor': '#ecf0f1',
                'borderRadius': '10px',
                'margin': '20px'
            }),
            
            # Warning message if crystal-toolkit not available
            html.Div([
                html.P("⚠️ Using simplified 3D viewer. Install crystal-toolkit for full features.",
                      style={'color': 'orange', 'fontStyle': 'italic'})
            ], style={'textAlign': 'center', 'padding': '10px'}) if not CRYSTAL_TOOLKIT_AVAILABLE else html.Div()
            
        ], style={'fontFamily': 'Arial, sans-serif', 'maxWidth': '1200px', 
                  'margin': '0 auto'})
        
        # Callbacks
        if CRYSTAL_TOOLKIT_AVAILABLE:
            @self.app.callback(
                [Output('structure-container', 'children'),
                 Output('property-info', 'children')],
                [Input('composition-dropdown', 'value')]
            )
            def update_structure(x):
                """Update structure display when composition changes."""
                if x not in self.structures:
                    return html.Div("Structure not found"), html.Div()
                
                # Create new structure component
                struct_comp = self.create_structure_component(x)
                
                # Get metadata
                meta = self.metadata.get(x, {})
                
                # Create property display
                property_display = html.Div([
                    html.H3(f"AlₓGa₁₋ₓAs Properties (x = {x:.3f})"),
                    html.Ul([
                        html.Li(f"Formula: {meta.get('formula', 'N/A')}"),
                        html.Li(f"Band Gap: {meta.get('band_gap', {}).get('value', 'N/A')} eV "
                               f"({meta.get('band_gap', {}).get('type', 'N/A')})"),
                        html.Li(f"Lattice Constant: {meta.get('lattice_constant', {}).get('value', 'N/A')} Å"),
                        html.Li(f"Space Group: {meta.get('space_group', 'N/A')}"),
                        html.Li(f"Density: {meta.get('density', 'N/A')} g/cm³"),
                    ])
                ])
                
                return struct_comp.layout(), property_display
        else:
            @self.app.callback(
                [Output('structure-graph', 'figure'),
                 Output('property-info', 'children')],
                [Input('composition-dropdown', 'value')]
            )
            def update_structure_simple(x):
                """Update structure display (simple mode)."""
                if x not in self.structures:
                    return go.Figure(), html.Div("Structure not found")
                
                # Create new 3D plot
                fig = self.create_simple_3d_plot(x)
                
                # Get metadata
                meta = self.metadata.get(x, {})
                
                # Create property display
                property_display = html.Div([
                    html.H3(f"AlₓGa₁₋ₓAs Properties (x = {x:.3f})"),
                    html.Ul([
                        html.Li(f"Formula: {meta.get('formula', 'N/A')}"),
                        html.Li(f"Band Gap: {meta.get('band_gap', {}).get('value', 'N/A')} eV "
                               f"({meta.get('band_gap', {}).get('type', 'N/A')})"),
                        html.Li(f"Lattice Constant: {meta.get('lattice_constant', {}).get('value', 'N/A')} Å"),
                        html.Li(f"Space Group: {meta.get('space_group', 'N/A')}"),
                        html.Li(f"Density: {meta.get('density', 'N/A')} g/cm³"),
                    ])
                ])
                
                return fig, property_display
        
        logger.info(f"Dash app created - will run on port {port}")
        return self.app
    
    def run_app(self, debug: bool = True, port: int = 8050):
            """
            Run the Dash application.
            
            Args:
                debug: Enable debug mode
                port: Port number
            """
            if self.app is None:
                self.create_dash_app(port)
            
            logger.info(f"Starting Dash app on http://localhost:{port}")
            # Dash 3.x uses run() instead of run_server()
            try:
                self.app.run(debug=debug, port=port)
            except AttributeError:
                # Fallback for older Dash versions
                self.app.run_server(debug=debug, port=port)
    
    def export_structure_image(self, x: float, output_path: str, 
                              format: str = 'png', dpi: int = 300):
        """
        Export high-resolution structure image.
        
        Args:
            x: Aluminum fraction
            output_path: Output file path
            format: Image format ('png' or 'svg')
            dpi: Resolution (for PNG)
        """
        structure = self.get_structure(x)
        if structure is None:
            raise ValueError(f"No structure found for x={x}")
        
        # TODO: Implement direct image export
        # This requires matplotlib + pymatgen visualization
        logger.warning("Direct image export not yet implemented. "
                      "Use Dash app screenshot functionality.")
        
    def generate_comparison_view(self, x_values: List[float]) -> go.Figure:
        """
        Generate side-by-side structure comparison plot.
        
        Args:
            x_values: List of compositions to compare
            
        Returns:
            Plotly figure with multiple structure views
        """
        # TODO: Implement multi-structure comparison
        # This requires custom 3D plotting with plotly
        logger.warning("Comparison view not yet implemented")
        return go.Figure()


# Standalone function for quick viewing
def view_structure(x: float = 0.5, data_dir: str = 'data'):
    """
    Quick function to view a single structure.
    
    Args:
        x: Aluminum fraction
        data_dir: Data directory
        
    Example:
        >>> view_structure(0.5)  # View Al₀.₅Ga₀.₅As
        
    Note:
        If crystal-toolkit is not available, will use simplified viewer.
    """
    viewer = StructureViewer(data_dir)
    viewer.load_structures()
    
    if not CRYSTAL_TOOLKIT_AVAILABLE:
        logger.warning("Crystal-toolkit not available. Using simplified viewer.")
        logger.warning("To fix: downgrade pymatgen to 2024.x.x or update crystal-toolkit")
    
    viewer.create_dash_app()
    viewer.run_app()


if __name__ == "__main__":
    # Demo usage
    viewer = StructureViewer()
    viewer.load_structures()
    print(f"Loaded {len(viewer.structures)} structures")
    print(f"Available compositions: {sorted(viewer.structures.keys())}")
    
    if not CRYSTAL_TOOLKIT_AVAILABLE:
        print("\n⚠️  WARNING: Crystal-toolkit not available!")
        print("   Reason: Incompatibility with pymatgen 2025.x.x")
        print("   Solution: Using simplified 3D viewer instead")
        print("\n   To enable full features, downgrade pymatgen:")
        print("   pip install 'pymatgen<2025'")
        print("   pip install crystal-toolkit --upgrade")