from dash import html, dcc, dash_table, register_page
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import dash
from dash import html, dcc

dash.register_page(__name__, path='/market')


# Load the dataset for plotting
df_plot = pd.read_csv("data/LUX_2026_V6_Training.csv")  # For plotting
df_search = pd.read_csv("data/LUX_combinations_with_predictions.csv")  # For kNN search

# Load products data for product name lookup
try:
    df_products = pd.read_excel("data/products.xlsx", engine='openpyxl')
    # Create a dictionary for fast lookup: scenario -> product names and IDs
    products_lookup = df_products.set_index('scenario')[['wall_name_shorter', 'window_name_shorter', 'roof_name_shorter', 'wall_id', 'window_id', 'roof_id']].to_dict('index')
except Exception as e:
    print(f"Warning: Could not load products.xlsx: {e}")
    products_lookup = {}

# Load layers data for layer descriptions
try:
    layers_data = pd.read_excel("data/layers.xlsx", sheet_name=None, engine='openpyxl')
    # Available sheets: External Wall, Roof, Window
    layers_lookup = {
        'wall': layers_data.get('External Wall', pd.DataFrame()),
        'roof': layers_data.get('Roof', pd.DataFrame()),
        'window': layers_data.get('Window', pd.DataFrame())
    }
except Exception as e:
    print(f"Warning: Could not load layers.xlsx: {e}")
    layers_lookup = {'wall': pd.DataFrame(), 'roof': pd.DataFrame(), 'window': pd.DataFrame()}

def get_product_names(scenario_id):
    """Get product names for a given scenario ID (e.g., 'p1', 'p123')"""
    if scenario_id in products_lookup:
        products = products_lookup[scenario_id]
        return {
            'wall_product': products.get('wall_name_shorter', '-'),
            'window_product': products.get('window_name_shorter', '-'), 
            'roof_product': products.get('roof_name_shorter', '-'),
            'wall_id': products.get('wall_id', None),
            'window_id': products.get('window_id', None),
            'roof_id': products.get('roof_id', None)
        }
    return {'wall_product': '-', 'window_product': '-', 'roof_product': '-', 'wall_id': None, 'window_id': None, 'roof_id': None}

def get_layer_descriptions(product_type, product_id):
    """Get layer descriptions for a product type and ID"""
    if product_id is None or pd.isna(product_id):
        print(f"DEBUG: product_id is None or NaN for {product_type}")
        return []
    
    # Get the appropriate sheet data
    if product_type not in layers_lookup:
        print(f"DEBUG: product_type {product_type} not in layers_lookup")
        return []
    
    df_layers = layers_lookup[product_type]
    if df_layers.empty:
        print(f"DEBUG: {product_type} sheet is empty")
        return []
    
    if 'ID' not in df_layers.columns:
        print(f"DEBUG: 'ID' column not found in {product_type}. Available columns: {list(df_layers.columns)}")
        return []
    
    if 'Layer Description' not in df_layers.columns:
        print(f"DEBUG: 'Layer Description' column not found in {product_type}. Available columns: {list(df_layers.columns)}")
        return []
    
    print(f"DEBUG: Looking for ID {product_id} in {product_type} sheet")
    print(f"DEBUG: Available IDs in {product_type}: {df_layers['ID'].unique()[:10]}...")  # Show first 10 IDs
    
    # Filter by product ID (ID column)
    matching_layers = df_layers[df_layers['ID'] == product_id]
    print(f"DEBUG: Found {len(matching_layers)} matching rows for ID {product_id} in {product_type}")
    
    # Extract layer descriptions
    layer_descriptions = matching_layers['Layer Description'].dropna().tolist()
    print(f"DEBUG: Extracted layer descriptions for {product_type} ID {product_id}: {layer_descriptions}")
    
    return layer_descriptions

def find_closest_instances(selected_idx, n_neighbors=5):
    """Find closest instances to the selected one based on normalized 2D coordinates"""
    if selected_idx is None or selected_idx >= len(df_plot):
        return []
    
    # Get the selected point coordinates from plot dataset
    selected_row = df_plot.iloc[selected_idx]
    selected_heating = selected_row['heating_load']
    selected_cooling = selected_row['cooling_load']
    
    # Use search dataset for finding neighbors
    search_features = ['predicted_heating_load', 'predicted_cooling_load']
    
    # Verify columns exist in search dataset
    if 'predicted_heating_load' not in df_search.columns or 'predicted_cooling_load' not in df_search.columns:
        # Fallback to alternative column names
        heating_cols = [col for col in df_search.columns if 'heating' in col.lower()]
        cooling_cols = [col for col in df_search.columns if 'cooling' in col.lower()]
        if heating_cols and cooling_cols:
            search_features = [heating_cols[0], cooling_cols[0]]
        else:
            print(f"WARNING: Could not find heating/cooling columns in search dataset. Available columns: {list(df_search.columns)}")
            return []
    
    # Get the features matrix from search dataset
    feature_matrix = df_search[search_features].values
    
    # NORMALIZE DATA TO HANDLE SCALE MISMATCH
    # Get statistics for both datasets
    plot_heating_stats = df_plot['heating_load']
    plot_cooling_stats = df_plot['cooling_load']
    search_heating_stats = df_search[search_features[0]]
    search_cooling_stats = df_search[search_features[1]]
    
    # Normalize selected point to 0-1 range based on plot dataset
    norm_selected_heating = (selected_heating - plot_heating_stats.min()) / (plot_heating_stats.max() - plot_heating_stats.min())
    norm_selected_cooling = (selected_cooling - plot_cooling_stats.min()) / (plot_cooling_stats.max() - plot_cooling_stats.min())
    
    # Normalize search dataset to 0-1 range based on search dataset
    norm_search_heating = (feature_matrix[:, 0] - search_heating_stats.min()) / (search_heating_stats.max() - search_heating_stats.min())
    norm_search_cooling = (feature_matrix[:, 1] - search_cooling_stats.min()) / (search_cooling_stats.max() - search_cooling_stats.min())
    
    # Create normalized feature matrices
    normalized_selected = np.array([[norm_selected_heating, norm_selected_cooling]])
    normalized_search = np.column_stack([norm_search_heating, norm_search_cooling])
    
    # Calculate distances using normalized data
    from sklearn.metrics.pairwise import euclidean_distances
    distances = euclidean_distances(normalized_selected, normalized_search)[0]
    
    # Get indices of closest instances
    closest_indices = np.argsort(distances)[:n_neighbors]
    
    return closest_indices.tolist()

def normalize_for_spider(value, param_name):
    """Normalize values for spider chart (0-1 range) using combined datasets"""
    # Define reasonable ranges for each parameter
    param_ranges = {
        'Wall-U (W/m²K)': (0.1, 0.8),
        'Window-U (W/m²K)': (0.7, 2.5), 
        'Roof-U (W/m²K)': (0.1, 0.5),
        'SHGC': (0.3, 0.9),
        'Ideal Heating (kWh)': (15000, 35000),
        'Ideal Cooling (kWh)': (100, 1000),
        'Transmittance (%)': (10, 90)
    }
    
    if param_name in param_ranges:
        min_val, max_val = param_ranges[param_name]
        # Clamp value to range and normalize
        clamped_value = max(min_val, min(value, max_val))
        normalized = (clamped_value - min_val) / (max_val - min_val)
        return max(0.1, min(0.9, normalized))  # Keep within 0.1-0.9 for visibility
    else:
        return 0.5

def create_spider_chart(selected_idx, closest_indices):
    """Create spider chart with selected instance and closest neighbors"""
    
    if selected_idx is None:
        return go.Figure()
    
    # Define the parameters for spider chart (rotated counter-clockwise by one unit)
    parameters = [
        'Wall-U (W/m²K)', 'Roof-U (W/m²K)', 'SHGC',  
         'Ideal Heating (kWh)', 'Ideal Cooling (kWh)', 'Transmittance (%)', 'Window-U (W/m²K)', 
    ]
    
    # Map to DataFrame columns
    col_mapping = {
        'Wall-U (W/m²K)': 'wall_u',
        'Window-U (W/m²K)': 'window_u', 
        'Roof-U (W/m²K)': 'roof_u',
        'SHGC': 'window_shgc',
        'Ideal Heating (kWh)': 'heating_load',
        'Ideal Cooling (kWh)': 'cooling_load',
        'Transmittance (%)': 'transmittance'
    }
    
    fig = go.Figure()
    
    # Colors: Selected Instance (darkest) -> Neighbors (progressively brighter)
    base_colors = [
        '#011928',  # Selected Instance (darkest/closest)
        '#083D5E',  # P1
        '#107ABC',  # P2/P3
        '#2AACFD',  # P4 - More saturated than CAE9FA
        '#86D0FE'   # P5+ (brightest/furthest) - More saturated than FAFFFF
    ]
    
    # Expand colors array for more neighbors by interpolating between base colors
    colors = [base_colors[0]]  # Selected instance
    for i in range(1, 11):  # P1 to P10
        if i == 1:
            colors.append(base_colors[1])  # P1
        elif i <= 3:
            colors.append(base_colors[2])  # P2, P3
        elif i == 4:
            colors.append(base_colors[3])  # P4
        else:
            colors.append(base_colors[4])  # P5+
    
    # Add selected instance (darkest color) - get from plot dataset
    selected_row = df_plot.iloc[selected_idx]
    r_values = []
    for param in parameters:
        col = col_mapping[param]
        # Map column names for plot dataset with correct column names
        value = None
        if col == 'heating_load':
            value = selected_row['heating_load']
        elif col == 'cooling_load':
            value = selected_row['cooling_load'] 
        elif col == 'window_shgc':
            value = selected_row['window_shgc']
        elif col == 'wall_u':
            value = selected_row['wall_u']
        elif col == 'transmittance':
            value = selected_row['transmittance']
        elif col in selected_row.index:
            value = selected_row[col]
        
        if value is not None:
            if param == 'Transmittance (%)':
                value = value * 100  # Convert to percentage
            normalized_value = normalize_for_spider(value, param)
            r_values.append(normalized_value)
        else:
            r_values.append(0.5)  # Default value if column not found
    
    fig.add_trace(go.Scatterpolar(
        r=r_values + [r_values[0]],  # Close the polygon
        theta=parameters + [parameters[0]],
        fill='toself',
        name='Selected Instance',
        line_color='white',  # White stroke for border
        fillcolor=colors[0],
        opacity=1,  # Higher opacity to show true colors
        line=dict(width=2, color='white'),  # White border with appropriate width
        showlegend=True
    ))
    
    # Add closest instances - get from search dataset
    for i, idx in enumerate(closest_indices):  # Use all provided neighbors
        neighbor_row = df_search.iloc[idx]
        r_values = []
        for param in parameters:
            col = col_mapping[param]
            # Map column names for search dataset with correct column names
            value = None
            if col == 'heating_load':
                value = neighbor_row['predicted_heating_load']
            elif col == 'cooling_load':
                value = neighbor_row['predicted_cooling_load']
            elif col == 'window_shgc':
                value = neighbor_row['window_shgc']
            elif col == 'wall_u':
                value = neighbor_row['wall_u']
            elif col == 'transmittance':
                value = neighbor_row['transmittance']
            elif col in neighbor_row.index:
                value = neighbor_row[col]
            
            if value is not None:
                if param == 'Transmittance (%)':
                    value = value * 100
                normalized_value = normalize_for_spider(value, param)
                r_values.append(normalized_value)
            else:
                r_values.append(0.5)  # Default value if column not found
        
        # Ensure we don't exceed color array bounds
        color_index = min(i+1, len(colors)-1)
        fig.add_trace(go.Scatterpolar(
            r=r_values + [r_values[0]],
            theta=parameters + [parameters[0]],
            fill='toself',
            name=f'P{i+1}',
            line_color='white',  # White stroke for border
            fillcolor=colors[color_index],
            opacity=0.6,  # Higher opacity to show true colors
            line=dict(width=1.5, color='white'),  # White border with appropriate width
            showlegend=True
        ))
    
    # Create fixed gradient bar with specified colors
    gradient_y = np.linspace(0, 1, 80)  # More points for smoother gradient
    gradient_x = [1] * len(gradient_y)  # Fixed x position
    gradient_values = np.linspace(0, 1, len(gradient_y))  # Values for colorscale
    
    # Fixed colorscale that exactly matches the base_colors defined above
    fixed_colorscale = [
        [0, '#011928'],    # 0% - Selected Instance (Closest) - base_colors[0]
        [0.25, '#083D5E'], # 25% - P1 - base_colors[1]
        [0.5, '#107ABC'],  # 50% - P2/P3 - base_colors[2]
        [0.75, '#2AACFD'], # 75% - P4 - base_colors[3]
        [1, '#86D0FE']     # 100% - P5+ (Furthest) - base_colors[4]
    ]
    
    # Add the gradient bar trace
    fig.add_trace(go.Scatter(
        x=gradient_x,
        y=gradient_y,
        mode='markers',
        marker=dict(
            size=18,  # Slightly smaller for cleaner appearance
            color=gradient_values,
            colorscale=fixed_colorscale,  # Fixed colorscale
            showscale=False,
            symbol='square',
            line=dict(width=0)
        ),
        showlegend=False,
        hoverinfo='skip',
        xaxis='x2',
        yaxis='y2'
    ))
    
    # Create annotations for labels
    legend_annotations = []
    
    # Add "Furthest" label at top (light blue at top)
    legend_annotations.append(dict(
        text="<b>Furthest</b>",
        x=0.99, y=0.95,  # Centered with gradient bar
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=12, color="#7B7B7B"),
        xanchor="center"
    ))
    
    # Add "Closest" label at bottom (dark blue at bottom)
    legend_annotations.append(dict(
        text="<b>Closest</b>",
        x=0.99, y=0.07,  # Centered with gradient bar
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=12, color="#7B7B7B"),
        xanchor="center"
    ))

    # Update layout with dual axis for gradient bar
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                showticklabels=True,
                tickvals=[0.2, 0.4, 0.6, 0.8, 1.0],
                ticktext=["20%", "40%", "60%", "80%", "100%"],
                tickfont=dict(size=8, color="grey"),
                gridcolor="lightgrey",
                gridwidth=1
            ),
            angularaxis=dict(
                tickfont_size=11,
                rotation=90,
                direction="clockwise",
                gridcolor="lightgrey",
                linecolor="grey"
            )
        ),
        # Second axis for gradient bar
        xaxis2=dict(
            domain=[0.98, 1.0],  # Gradient bar position
            visible=False,
            range=[0.8, 1.2]
        ),
        yaxis2=dict(
            domain=[0.15, 0.88],  # Vertical position range matching labels
            visible=False,
            range=[0, 1]
        ),
        showlegend=True,  # Show legend at bottom for main spider traces
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="lightgrey",
            borderwidth=1
        ),
        annotations=legend_annotations,
        font=dict(size=10),
        margin=dict(l=50, r=140, t=30, b=80),  # Increased right margin for gradient
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        height=400,
        uirevision=True  # Force updates
    )
    
    return fig

# Create initial 2D scatter plot
def create_initial_scatter():
    fig = px.scatter(
        df_plot, 
        x="heating_load", 
        y="cooling_load",
        labels={
            "heating_load": "Ideal Heating Load (kWh)",
            "cooling_load": "Ideal Cooling Load (kWh)"
        }
    )
    
    fig.update_traces(
        marker=dict(size=6, opacity=0.7, color="#2AACFD"),
        hovertemplate="Ideal Heating Load: %{x:.1f} kWh<br>" +
                     "Ideal Cooling Load: %{y:.1f} kWh<extra></extra>"
    )
    
    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font_color="#2C3E50",
        showlegend=False,
        margin=dict(l=50, r=50, t=20, b=50),
        xaxis=dict(showgrid=True, gridcolor="lightgrey"),
        yaxis=dict(showgrid=True, gridcolor="lightgrey"),
        dragmode=False  # Disable zooming and panning
    )
    
    return fig

# Create initial spider chart
def create_initial_spider():
    fig = go.Figure()
    
    # Add empty spider chart
    fig.add_trace(go.Scatterpolar(
        r=[],
        theta=[],
        mode='lines+markers',
        name='Select a point'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1]),
            angularaxis=dict(
                tickfont_size=10,
                rotation=90,
                direction="clockwise"
            )
        ),
        showlegend=True,
        font=dict(size=10),
        margin=dict(l=50, r=50, t=20, b=50),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    
    return fig

# Card styles
CARDHEADER_STYLE = {
    "backgroundColor": "#F5F5F5",
    "color": "#7B7B7B",
    "borderRadius": "8px 8px 0 0",
    "borderBottom": "none",
    "padding": "8px 16px",
    "fontSize": "20px",
    "paddingBottom": "0px",
    "fontWeight": "200",
    "margin": "0px"
}

CARD_STYLE = {
    "backgroundColor": "#F5F5F5",
    "borderRadius": "8px",
    "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.15)",
    "border": "none",
    "paddingTop": "12px",
    "padding": "0px",
    "overflow": "visible"
}

CARDBODY_STYLE = {
    "paddingTop": "2px",
    "paddingRight": "16px",
    "paddingBottom": "16px",
    "paddingLeft": "16px"
}

# Page layout
layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1(
                "Closest Market-Available Scenarios",
                style={
                    "fontFamily": "Poppins, sans-serif",
                    "fontWeight": "600",
                    "fontSize": "36px",
                    "color": "#2C3E50",
                    "textAlign": "center",
                    "marginTop": "30px",
                    "marginBottom": "30px"
                }
            )
        ], width=12)
    ]),
    
    # Top section with plots
    dbc.Row([
        # Left plot - 2D Scatter
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("Ideal Loads", style={
                        "fontWeight": "300",
                        "fontSize": "20px",
                        "margin": "0",
                        "color": "#7B7B7B"
                    })
                ], style=CARDHEADER_STYLE),
                dbc.CardBody([
                    dcc.Graph(
                        id="market-scatter-plot",
                        figure=create_initial_scatter(),
                        style={"height": "400px"},
                        config={
                            'displayModeBar': False,  # Hide the toolbar completely
                            'staticPlot': False,      # Keep interactions for clicking
                            'scrollZoom': False,      # Disable scroll zoom
                            'doubleClick': False,     # Disable double click zoom
                            'showTips': False,        # Hide tips
                            'displaylogo': False      # Hide plotly logo
                        }
                    )
                ], style=CARDBODY_STYLE)
            ], style=CARD_STYLE, className="h-100")
        ], width=6),
        
        # Right plot - Spider Chart
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("Building Parameters", style={
                        "fontWeight": "300",
                        "fontSize": "20px",
                        "margin": "0",
                        "color": "#7B7B7B"
                    })
                ], style=CARDHEADER_STYLE),
                dbc.CardBody([
                    dcc.Graph(
                        id="market-spider-chart",
                        figure=create_initial_spider(),
                        style={"height": "400px"},
                        config={
                            'displayModeBar': False,  # Hide the toolbar
                            'staticPlot': False,      # Keep interactive legend
                            'scrollZoom': False,      # Disable scroll zoom
                            'doubleClick': False,     # Disable double click zoom
                            'showTips': False,        # Hide tips
                            'displaylogo': False      # Hide plotly logo
                        }
                    )
                ], style=CARDBODY_STYLE)
            ], style=CARD_STYLE, className="h-100")
        ], width=6)
    ], className="mb-4"),
    
    # Middle section - Number selector
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Label(
                    "Closest Market-Available Instances",
                    style={
                        "fontFamily": "Poppins, sans-serif",
                        "fontWeight": "400",
                        "fontSize": "16px",
                        "color": "#9B9B9B",
                        "marginBottom": "15px"
                    }
                ),
                dcc.Slider(
                    id="neighbors-slider",
                    min=1,
                    max=10,
                    step=1,
                    value=5,
                    marks={i: str(i) for i in range(1, 11)},
                    tooltip={
                        "placement": "top", 
                        "always_visible": True,
                        "style": {"fontSize": "14px", "fontWeight": "600"}
                    },
                    className="market-slider"
                )
            ], style={
                "textAlign": "center",
                "padding": "20px",
                "backgroundColor": "#F8F9FA",
                "borderRadius": "8px",
                "margin": "0 auto",
                "maxWidth": "500px"
            })
        ], width=12)
    ], className="mb-4"),
    
    # Bottom section - Simplified Market Instance Table
    dbc.Row([
        dbc.Col([
            dbc.Card(id="market-instance-table-card", children=[
                dbc.CardHeader([
                    html.H5("Closest Market-Available Instance Table", style={
                        "fontWeight": "300",
                        "fontSize": "20px",
                        "margin": "0",
                        "color": "#7B7B7B",
                        "display": "inline-block",
                        "marginRight": "16px"
                    })
                ], style={
                    "backgroundColor": "#F5F5F5",
                    "borderRadius": "8px 8px 0 0",
                    "padding": "12px 16px",
                    "borderBottom": "none",
                    "position": "relative",
                    "minHeight": "50px"
                }),
                dbc.CardBody([
                    # Simplified Market Instance Table (removed filters, search, pagination)
                    dash_table.DataTable(
                        id="market-instance-table",
                        columns=[
                            {"name": "Instance Name", "id": "instance_name", "type": "text"},
                            {"name": "Transmittance (%)", "id": "transmittance", "type": "numeric", "format": {"specifier": ".1f"}},
                            {"name": "SHGC", "id": "window_shgc", "type": "numeric", "format": {"specifier": ".3f"}},
                            {"name": "Window-U (W/m²K)", "id": "window_u", "type": "numeric", "format": {"specifier": ".3f"}},
                            {"name": "Window Product", "id": "window_product", "type": "text"},
                            {"name": "Roof-U (W/m²K)", "id": "roof_u", "type": "numeric", "format": {"specifier": ".3f"}},
                            {"name": "Roof Product", "id": "roof_product", "type": "text"},
                            {"name": "Wall-U (W/m²K)", "id": "wall_u", "type": "numeric", "format": {"specifier": ".3f"}},
                            {"name": "Wall Product", "id": "wall_product", "type": "text"},
                            {"name": "Ideal Cooling (kWh)", "id": "cooling_load", "type": "numeric", "format": {"specifier": ".1f"}},
                            {"name": "Ideal Heating (kWh)", "id": "heating_load", "type": "numeric", "format": {"specifier": ".1f"}}
                        ],
                        data=[],
                        # Removed pagination settings
                        filter_action="none",
                        # Table styling remains the same
                        style_table={
                            'overflowX': 'auto',
                            'fontFamily': 'Poppins, sans-serif',
                            'backgroundColor': '#F5F5F5',
                            'borderRadius': '0',
                            'overflow': 'hidden',
                            'border': 'none',
                            'margin': '0',
                            'marginTop': '0',
                            'marginBottom': '0'
                        },
                        
                        style_header={
                            'backgroundColor': '#E3E3E3',
                            'fontWeight': '600',
                            'fontSize': '13px',
                            'color': '#666666',
                            'textAlign': 'center',
                            'border': 'none',
                            'borderTop': 'none',
                            'borderBottom': 'none',
                            'borderLeft': 'none', 
                            'borderRight': 'none',
                            'whiteSpace': 'normal',
                            'height': '40px',
                            'padding': '12px 8px',
                            'outline': 'none',
                            'boxShadow': 'none'
                        },
                        
                        style_header_conditional=[
                            {
                                'if': {'column_id': 'instance_name'},
                                'borderTopLeftRadius': '8px',
                                'backgroundColor': '#E3E3E3',
                                'border': 'none'
                            },
                            {
                                'if': {'column_id': 'heating_load'},
                                'borderTopRightRadius': '8px', 
                                'backgroundColor': '#E3E3E3',
                                'border': 'none'
                            }
                        ],
                        
                        style_cell={
                            'textAlign': 'center',
                            'fontSize': '12px',
                            'fontFamily': 'Poppins, sans-serif',
                            'color': '#333333',
                            'padding': '12px 8px',
                            'border': 'none',
                            'borderTop': 'none',
                            'borderLeft': 'none', 
                            'borderRight': 'none',
                            'borderBottom': '1px solid #E6E6E6',
                            'backgroundColor': '#F5F5F5',
                            'minWidth': '80px',
                            'maxWidth': '150px',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis'
                        },
                        
                        # Cell conditional styling for wider product columns
                        style_cell_conditional=[
                            # Make product columns wider to accommodate longer names with underline style
                            {
                                'if': {'column_id': 'window_product'},
                                'minWidth': '180px',
                                'maxWidth': '250px',
                                'whiteSpace': 'normal',
                                'height': 'auto',
                                'textOverflow': 'unset',
                                'overflow': 'visible',
                                'textDecoration': 'underline',
                                'cursor': 'pointer',
                                'position': 'relative'
                            },
                            {
                                'if': {'column_id': 'roof_product'},
                                'minWidth': '180px',
                                'maxWidth': '250px',
                                'whiteSpace': 'normal',
                                'height': 'auto',
                                'textOverflow': 'unset',
                                'overflow': 'visible',
                                'textDecoration': 'underline',
                                'cursor': 'pointer',
                                'position': 'relative'
                            },
                            {
                                'if': {'column_id': 'wall_product'},
                                'minWidth': '180px',
                                'maxWidth': '250px',
                                'whiteSpace': 'normal',
                                'height': 'auto',
                                'textOverflow': 'unset',
                                'overflow': 'visible',
                                'textDecoration': 'underline',
                                'cursor': 'pointer',
                                'position': 'relative'
                            }
                        ],
                        
                        # Data conditional styling
                        style_data_conditional=[
                            # Instance name için mavi renk
                            {
                                'if': {'column_id': 'instance_name'},
                                'fontWeight': '600',
                                'color': '#2AACFD',
                                'backgroundColor': '#F5F5F5'
                            },
                            # İlk satır (Selected Instance) için özel stil
                            {
                                'if': {'row_index': 0},
                                'color': '#063D5E',
                                'fontWeight': '600',
                                'backgroundColor': '#E3F2FD'
                            },
                            # Seçili satırlar
                            {
                                'if': {'state': 'selected'},
                                'backgroundColor': '#E3F2FD',
                                'border': '1px solid #2AACFD'
                            },
                            # Zebra striping
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': '#EEEEEE'
                            },
                            {
                                'if': {'row_index': 'even'},
                                'backgroundColor': '#F5F5F5'
                            }
                        ],
                        
                        sort_action="native",
                        row_selectable="multi",
                        selected_rows=[],
                        include_headers_on_copy_paste=False,
                        merge_duplicate_headers=True,
                        # CSS override
                        css=[
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th',
                                'rule': 'background-color: #E3E3E3 !important; color: #666666 !important; font-weight: 600 !important; border: none !important; box-shadow: none !important;'
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th:first-child',
                                'rule': 'border-top-left-radius: 8px !important; background-color: #E3E3E3 !important; border: none !important;'
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th:last-child', 
                                'rule': 'border-top-right-radius: 8px !important; background-color: #E3E3E3 !important; border: none !important;'
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th:hover', 
                                'rule': 'background-color: #E3E3E3 !important; cursor: default !important;'
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner thead',
                                'rule': 'border-bottom: none !important; box-shadow: none !important;'
                            },
                            {
                                'selector': '.dash-table-container',
                                'rule': 'border-radius: 0; overflow: visible; box-shadow: none; background-color: #F5F5F5; border: none;'
                            },
                            # Product hover effects remain for functionality
                            {
                                'selector': 'td[data-dash-column="window_product"]',
                                'rule': 'position: relative !important; overflow: visible !important;'
                            },
                            {
                                'selector': 'td[data-dash-column="roof_product"]',
                                'rule': 'position: relative !important; overflow: visible !important;'
                            },
                            {
                                'selector': 'td[data-dash-column="wall_product"]',
                                'rule': 'position: relative !important; overflow: visible !important;'
                            }
                        ]
                    ),
                    
                    # Simple Table Footer - removed pagination
                    dbc.Row([
                        dbc.Col([
                            html.Div(id="market-table-info", style={
                                "fontSize": "12px",
                                "color": "#6C757D",
                                "fontWeight": "normal",
                                "padding": "8px 0"
                            })
                        ], width=True),
                        dbc.Col([
                            dbc.Button(
                                "Export Selected",
                                id="export-market-button",
                                size="sm",
                                style={
                                    "backgroundColor": "#2AACFD",
                                    "border": "none",
                                    "borderRadius": "8px",
                                    "fontSize": "12px",
                                    "fontWeight": "600",
                                    "padding": "8px 16px"
                                }
                            )
                        ], width="auto")
                    ], align="center", className="mt-2")
                    
                ], style={
                    "paddingTop": "0px",
                    "paddingRight": "16px",
                    "paddingBottom": "16px",
                    "paddingLeft": "16px",
                    "overflow": "visible"
                })
            ], style=CARD_STYLE)
        ], width=12)
    ], className="mb-4"),
    
    # Back button
    dbc.Row([
        dbc.Col([
            dbc.Button(
                "← Back to All Solutions",
                href="/pilot_lux_explorer",
                external_link=True,
                color="primary",
                style={
                    "marginTop": "20px",
                    "backgroundColor": "#2AACFD",
                    "border": "none",
                    "borderRadius": "8px",
                    "fontFamily": "Poppins, sans-serif",
                    "fontWeight": "500"
                }
            )
        ], width=12, className="text-center")
    ]),
    
    # Hidden stores for data (simplified - removed filter stores)
    dcc.Store(id="selected-point-store", data=None),
    dcc.Store(id="market-instances-store", data=[]),
    
    # Store for table selection
    dcc.Store(id="market-table-selected-instances", data=[]),
    dcc.Download(id="market-download-instances"),
    
    # Store for layer descriptions data
    dcc.Store(id="market-layers-data", data={}),
    
    # Store for tracking hover state
    dcc.Store(id="market-hover-state", data={}),
    
], fluid=True, style={
    "backgroundColor": "#FFFFFF",
    "padding": "20px",
    "minHeight": "100vh"
})