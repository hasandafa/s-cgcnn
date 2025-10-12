"""
Simple Structure Viewer with Bonds - Materials Project Style
FULLY FIXED: Pymatgen 2025 compatibility + Visible bonds
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from pymatgen.core import Structure
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output
import json

def load_structures(cif_dir='data/structures/cif'):
    """Load all structures from CIF directory"""
    structures = {}
    metadata = {}
    
    cif_path = Path(cif_dir)
    for cif_file in sorted(cif_path.glob('*.cif')):
        try:
            stem = cif_file.stem
            if '_x' in stem:
                # Extract x value - handles both AlGaAs_x_0_000 and AlGaAs_x0.000
                x_part = stem.split('_x')[1]  # Get part after '_x'
                # Remove any remaining underscores and convert to float
                x_str = x_part.replace('_', '.')
                x = float(x_str)
            else:
                continue
            
            structure = Structure.from_file(str(cif_file))
            structures[x] = structure
            
            meta_file = cif_path.parent / 'metadata' / f"{cif_file.stem}.json"
            if meta_file.exists():
                with open(meta_file, 'r') as f:
                    metadata[x] = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load {cif_file.name}: {e}")
            continue
    
    return structures, metadata

def create_3d_plot_with_bonds(structure, x, bond_cutoff=3.0):
    """
    Create 3D Plotly visualization with bonds (Materials Project style)
    FIXED: Pymatgen 2025 compatibility
    
    Args:
        structure: Pymatgen Structure
        x: Aluminum fraction
        bond_cutoff: Maximum bond distance in Angstroms (default: 3.0)
    """
    # Color scheme (Materials Project style)
    colors_map = {
        'Al': '#1f77b4',  # Blue
        'Ga': '#ff7f0e',  # Orange
        'As': '#2ca02c'   # Green
    }
    
    # Element sizes
    sizes_map = {
        'Al': 14,
        'Ga': 16,
        'As': 18
    }
    
    fig = go.Figure()
    
    # 1. ADD ATOMS FIRST (so bonds appear on top)
    atoms_by_element = {}
    
    for site in structure:
        element = site.specie.symbol
        if element not in atoms_by_element:
            atoms_by_element[element] = {'coords': [], 'text': []}
        
        atoms_by_element[element]['coords'].append(site.coords)
        atoms_by_element[element]['text'].append(
            f"{element}<br>({site.coords[0]:.2f}, {site.coords[1]:.2f}, {site.coords[2]:.2f})"
        )
    
    # Add trace for each element type
    for element, data in atoms_by_element.items():
        coords = np.array(data['coords'])
        
        fig.add_trace(go.Scatter3d(
            x=coords[:, 0],
            y=coords[:, 1],
            z=coords[:, 2],
            mode='markers',
            marker=dict(
                size=sizes_map.get(element, 14),
                color=colors_map.get(element, 'gray'),
                line=dict(color='white', width=2),
                opacity=0.9
            ),
            text=data['text'],
            hovertemplate='%{text}<extra></extra>',
            name=f'{element} ({len(coords)})',
            legendgroup=element
        ))
    
    # 2. ADD BONDS - FIXED FOR PYMATGEN 2025
    bond_count = 0
    bonds_added = set()  # Track bonds to avoid duplicates
    
    for i, site1 in enumerate(structure):
        # Get neighbors within cutoff distance
        neighbors = structure.get_neighbors(site1, bond_cutoff)
        
        for neighbor in neighbors:
            # FIX: In pymatgen 2025, neighbor IS the PeriodicSite
            # No need for neighbor.nn_site - just use neighbor directly
            site2_coords = neighbor.coords
            
            # Find index of neighbor site in structure
            j = None
            for idx, s in enumerate(structure):
                if np.allclose(s.coords, site2_coords, atol=0.01):
                    j = idx
                    break
            
            # Only draw each bond once using a unique identifier
            if j is not None and i < j:
                bond_id = tuple(sorted([i, j]))
                if bond_id not in bonds_added:
                    # Add individual bond as separate trace for better visibility
                    fig.add_trace(go.Scatter3d(
                        x=[site1.coords[0], site2_coords[0]],
                        y=[site1.coords[1], site2_coords[1]],
                        z=[site1.coords[2], site2_coords[2]],
                        mode='lines',
                        line=dict(
                            color='rgba(80, 80, 80, 0.8)',  # Dark gray with transparency
                            width=6  # Thick for visibility
                        ),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
                    bonds_added.add(bond_id)
                    bond_count += 1
    
    # Add bond counter in legend
    if bond_count > 0:
        fig.add_trace(go.Scatter3d(
            x=[None], y=[None], z=[None],
            mode='lines',
            line=dict(color='rgba(80, 80, 80, 0.8)', width=6),
            name=f'Bonds ({bond_count})',
            showlegend=True
        ))
        print(f"  ✅ Drew {bond_count} bonds with cutoff {bond_cutoff:.1f}Å")
    else:
        print(f"  ⚠️  No bonds found with cutoff {bond_cutoff:.1f}Å")
        # Calculate typical nearest neighbor distance
        if len(structure) > 1:
            min_dist = float('inf')
            for i, site1 in enumerate(structure):
                for j, site2 in enumerate(structure):
                    if i != j:
                        dist = np.linalg.norm(site1.coords - site2.coords)
                        min_dist = min(min_dist, dist)
            print(f"      Minimum interatomic distance: {min_dist:.2f}Å")
            print(f"      Recommended cutoff: {min_dist * 1.2:.2f}Å")
    
    # 3. ADD UNIT CELL EDGES
    lattice = structure.lattice
    # Get the actual lattice vectors for proper unit cell display
    a, b, c = lattice.matrix[0], lattice.matrix[1], lattice.matrix[2]
    origin = np.array([0, 0, 0])
    
    # 8 vertices of unit cell
    vertices = [
        origin,
        origin + a,
        origin + a + b,
        origin + b,
        origin + c,
        origin + a + c,
        origin + a + b + c,
        origin + b + c
    ]
    
    edges = [
        (0,1), (1,2), (2,3), (3,0),  # Bottom
        (4,5), (5,6), (6,7), (7,4),  # Top
        (0,4), (1,5), (2,6), (3,7)   # Sides
    ]
    
    for edge in edges:
        v1, v2 = vertices[edge[0]], vertices[edge[1]]
        fig.add_trace(go.Scatter3d(
            x=[v1[0], v2[0]],
            y=[v1[1], v2[1]],
            z=[v1[2], v2[2]],
            mode='lines',
            line=dict(color='black', width=4),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Update layout (Materials Project style)
    fig.update_layout(
        title=dict(
            text=f'Al<sub>{x:.3f}</sub>Ga<sub>{1-x:.3f}</sub>As Structure',
            x=0.5,
            xanchor='center',
            font=dict(size=20, color='#2c3e50', family='Arial')
        ),
        scene=dict(
            xaxis=dict(
                title='X (Å)',
                backgroundcolor='rgb(250, 250, 250)',
                gridcolor='white',
                showbackground=True
            ),
            yaxis=dict(
                title='Y (Å)',
                backgroundcolor='rgb(250, 250, 250)',
                gridcolor='white',
                showbackground=True
            ),
            zaxis=dict(
                title='Z (Å)',
                backgroundcolor='rgb(250, 250, 250)',
                gridcolor='white',
                showbackground=True
            ),
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        width=950,
        height=750,
        showlegend=True,
        legend=dict(
            x=0.82,
            y=0.98,
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='black',
            borderwidth=1,
            font=dict(size=11)
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    
    return fig

def main():
    """Main application"""
    print("\n" + "="*70)
    print("  s-CGCNN Structure Viewer - Materials Project Style")
    print("="*70)
    
    # Load data
    structures, metadata = load_structures()
    print(f"  Loaded {len(structures)} structures")
    
    if len(structures) == 0:
        print("  ERROR: No structures found!")
        return
    
    # Create Dash app
    app = dash.Dash(__name__, title="s-CGCNN Structure Viewer")
    
    # Get compositions
    compositions = sorted(structures.keys())
    initial_x = 0.5 if 0.5 in compositions else compositions[0]
    
    # App layout
    app.layout = html.Div([
        html.H1(
            "AlₓGa₁₋ₓAs Interactive Structure Viewer",
            style={
                'textAlign': 'center', 
                'color': '#2c3e50', 
                'marginTop': '20px',
                'fontFamily': 'Arial, sans-serif'
            }
        ),
        
        html.Hr(),
        
        # Controls
        html.Div([
            html.Div([
                html.Label(
                    "Select Aluminum Fraction (x):",
                    style={'fontWeight': 'bold', 'fontSize': '16px'}
                ),
                dcc.Dropdown(
                    id='composition-dropdown',
                    options=[{'label': f'x = {x:.3f}', 'value': x} for x in compositions],
                    value=initial_x,
                    clearable=False,
                    style={'width': '250px', 'marginTop': '10px'}
                )
            ], style={'display': 'inline-block', 'marginRight': '30px'}),
            
            html.Div([
                html.Label(
                    "Bond Cutoff Distance (Å):",
                    style={'fontWeight': 'bold', 'fontSize': '16px'}
                ),
                dcc.Slider(
                    id='bond-cutoff-slider',
                    min=2.0,
                    max=6.0,
                    step=0.1,
                    value=4.0,  # Start with higher default
                    marks={i: f'{i}Å' for i in range(2, 7)},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], style={'display': 'inline-block', 'width': '400px'})
            
        ], style={'padding': '20px'}),
        
        # 3D Graph
        dcc.Graph(
            id='structure-graph',
            style={'padding': '10px'}
        ),
        
        # Properties panel
        html.Div(
            id='property-info',
            style={
                'padding': '20px',
                'backgroundColor': '#ecf0f1',
                'borderRadius': '10px',
                'margin': '20px',
                'fontSize': '14px',
                'fontFamily': 'Arial, sans-serif'
            }
        ),
        
        # Info footer
        html.Div([
            html.P([
                html.Strong("Visualization Features:"),
                html.Br(),
                "• Bonds shown as dark gray lines between atoms within cutoff distance",
                html.Br(),
                "• Colors: Al (blue), Ga (orange), As (green)",
                html.Br(),
                "• Click and drag to rotate, scroll to zoom, double-click to reset",
                html.Br(),
                html.Strong("💡 Tip: "),
                "If no bonds visible, increase cutoff to 4-5 Å",
                html.Br(),
                html.Strong("⚠ Note: "),
                "Space group changes (F-43m → R3m, Amm2, etc.) are NORMAL for interpolated alloys"
            ], style={'fontSize': '12px', 'color': '#555'})
        ], style={'padding': '20px', 'textAlign': 'center'})
        
    ], style={
        'fontFamily': 'Arial, sans-serif', 
        'maxWidth': '1400px', 
        'margin': '0 auto',
        'backgroundColor': '#f8f9fa'
    })
    
    # CRITICAL FIX: Callback with proper dependencies
    @app.callback(
        [Output('structure-graph', 'figure'),
         Output('property-info', 'children')],
        [Input('composition-dropdown', 'value'),
         Input('bond-cutoff-slider', 'value')]
    )
    def update_structure(x, bond_cutoff):
        """
        Update structure when composition or bond cutoff changes
        FIXED: Pymatgen 2025 compatibility
        """
        print(f"\n{'='*70}")
        print(f"CALLBACK TRIGGERED: x={x:.3f}, bond_cutoff={bond_cutoff:.1f}Å")
        print('='*70)
        
        # Get structure
        structure = structures[x]
        
        # Create new plot with bonds
        fig = create_3d_plot_with_bonds(structure, x, bond_cutoff)
        
        # Get metadata - FIXED PARSER
        meta = metadata.get(x, {})
        props = meta.get('properties', {})  # FIX: Get properties dict first!
        
        # Count atoms
        n_al = sum(1 for site in structure if site.specie.symbol == 'Al')
        n_ga = sum(1 for site in structure if site.specie.symbol == 'Ga')
        n_as = sum(1 for site in structure if site.specie.symbol == 'As')
        
        print(f"  Structure info: {n_al} Al, {n_ga} Ga, {n_as} As")
        
        # Extract properties correctly from nested dict
        lattice_const = props.get('lattice_constant', 'N/A')
        band_gap = props.get('band_gap', 'N/A')
        band_gap_type = props.get('band_gap_type', 'N/A')
        density = props.get('density', 'N/A')
        space_group = meta.get('space_group', 'N/A')
        
        # Format values
        lattice_str = f"{lattice_const:.4f} Å" if isinstance(lattice_const, (int, float)) else str(lattice_const)
        band_gap_str = f"{band_gap:.3f} eV ({band_gap_type})" if isinstance(band_gap, (int, float)) else 'N/A'
        density_str = f"{density:.4f} g/cm³" if isinstance(density, (int, float)) else str(density)
        
        print(f"  Properties: Band gap={band_gap_str}, Density={density_str}")
        print('='*70 + '\n')
        
        # Create property display
        property_display = html.Div([
            html.H3(f"Al{x:.3f}Ga{1-x:.3f}As Properties", 
                   style={'color': '#2c3e50', 'marginBottom': '15px'}),
            html.Div([
                html.Div([
                    html.P([html.Strong("Formula: "), meta.get('formula', 'N/A')]),
                    html.P([html.Strong("Space Group: "), space_group]),
                    html.P([html.Strong("Lattice Constant: "), lattice_str]),
                    html.P([html.Strong("Atoms: "), 
                           f"Al={n_al}, Ga={n_ga}, As={n_as} (Total: {len(structure)})"]),
                ], style={'display': 'inline-block', 'width': '45%', 'verticalAlign': 'top'}),
                
                html.Div([
                    html.P([html.Strong("Band Gap: "), band_gap_str]),
                    html.P([html.Strong("Density: "), density_str]),
                    html.P([html.Strong("Bond Cutoff: "), f"{bond_cutoff:.1f} Å"]),
                    html.P([html.Strong("Data Source: "), meta.get('data_source', 'Interpolated')]),
                ], style={'display': 'inline-block', 'width': '45%', 'verticalAlign': 'top', 'marginLeft': '5%'})
            ])
        ])
        
        return fig, property_display
    
    print(f"  Starting server at: http://localhost:8050")
    print(f"  Features:")
    print(f"    • Interactive 3D rotation/zoom")
    print(f"    • Visible bonds (dark gray, thick lines)")
    print(f"    • Adjustable bond cutoff (2-6 Å)")
    print(f"    • Real-time structure updates")
    print(f"  Pymatgen version: 2025.10.7 compatible")
    print(f"  Press Ctrl+C to stop")
    print("="*70 + "\n")
    
    # Run app
    app.run(debug=False, port=8050)

if __name__ == "__main__":
    main()