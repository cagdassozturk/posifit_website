from dash import callback, Output, Input, State, html, ctx, clientside_callback, ClientsideFunction, dcc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from sklearn.metrics.pairwise import euclidean_distances
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash


def interpolate_color(color1, color2, factor):
    """Interpolate between two hex colors"""
    # Convert hex to RGB
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Convert RGB to hex
    def rgb_to_hex(rgb):
        return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
    
    # Get RGB values
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    
    # Interpolate
    interpolated_rgb = tuple(
        rgb1[i] + factor * (rgb2[i] - rgb1[i]) for i in range(3)
    )
    
    return rgb_to_hex(interpolated_rgb)

# Load the datasets
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
    distances = euclidean_distances(normalized_selected, normalized_search)[0]
    
    # Get indices of closest instances
    closest_indices = np.argsort(distances)[:n_neighbors]
    
    return closest_indices.tolist()

def normalize_for_spider(value, param_name):
    """Normalize values for spider chart (0-1 range) using combined datasets"""
    # Define reasonable ranges for each parameter
    param_ranges = {
        'Wall-U (W/mÂ²K)': (0.1, 0.8),
        'Window-U (W/mÂ²K)': (0.7, 2.5), 
        'Roof-U (W/mÂ²K)': (0.1, 0.5),
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
        'Wall-U (W/mÂ²K)', 'Roof-U (W/mÂ²K)', 'SHGC',  
         'Ideal Heating (kWh)', 'Ideal Cooling (kWh)', 'Transmittance (%)', 'Window-U (W/mÂ²K)', 
    ]
    
    # Map to DataFrame columns
    col_mapping = {
        'Wall-U (W/mÂ²K)': 'wall_u',
        'Window-U (W/mÂ²K)': 'window_u', 
        'Roof-U (W/mÂ²K)': 'roof_u',
        'SHGC': 'window_shgc',
        'Ideal Heating (kWh)': 'heating_load',
        'Ideal Cooling (kWh)': 'cooling_load',
        'Transmittance (%)': 'transmittance'
    }
    
    fig = go.Figure()
    
    # Colors: Selected Instance (darkest) -> Neighbors (progressively brighter)
    # These colors match exactly with the gradient bar colorscale
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
            value = selected_row['window_shgc']  # Plot dataset uses 'shgc'
        elif col == 'wall_u':
            value = selected_row['wall_u']  # Plot dataset uses 'wall_u'
        elif col == 'transmittance':
            value = selected_row['transmittance']  # Plot dataset uses capital 'T'
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
                value = neighbor_row['predicted_heating_load']  # Search dataset uses 'predicted_heating_load'
            elif col == 'cooling_load':
                value = neighbor_row['predicted_cooling_load']  # Search dataset uses 'predicted_cooling_load'
            elif col == 'window_shgc':
                value = neighbor_row['window_shgc']  # Search dataset uses 'window_shgc'
            elif col == 'wall_u':
                value = neighbor_row['wall_u']  # Search dataset uses 'wall_u'
            elif col == 'transmittance':
                value = neighbor_row['transmittance']  # Search dataset uses lowercase 'transmittance'
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
    # Create gradient bar as a scatter trace with fixed colorscale
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

@callback(
    [Output('selected-point-store', 'data'),
     Output('market-scatter-plot', 'figure')],
    Input('market-scatter-plot', 'clickData'),
    State('market-scatter-plot', 'figure'),
    prevent_initial_call=True
)
def update_selected_point(clickData, current_fig):
    """Handle point selection in scatter plot"""
    if not clickData:
        raise PreventUpdate
    
    # Get the clicked point index
    point_index = clickData['points'][0]['pointIndex']
    
    # Update scatter plot to highlight selected point
    fig = px.scatter(
        df_plot, 
        x="heating_load", 
        y="cooling_load",
        labels={
            "heating_load": "Ideal Heating Load (kWh)",
            "cooling_load": "Ideal Cooling Load (kWh)"
        }
    )
    
    # Update all points
    fig.update_traces(
        marker=dict(size=6, opacity=0.4, color="#2AACFD"),
        hovertemplate="Ideal Heating Load: %{x:.1f} kWh<br>" +
                     "Ideal Cooling Load: %{y:.1f} kWh<extra></extra>"
    )
    
    # Highlight selected point
    selected_row = df_plot.iloc[point_index]
    fig.add_trace(go.Scatter(
        x=[selected_row['heating_load']],
        y=[selected_row['cooling_load']],
        mode='markers',
        marker=dict(size=12, color='#063D5E', line=dict(width=3, color='white')),
        name=f'Selected (S{point_index})',
        hovertemplate=f"<b>Selected Point</b><br>" +
                     f"Ideal Heating Load: {selected_row['heating_load']:.1f} kWh<br>" +
                     f"Ideal Cooling Load: {selected_row['cooling_load']:.1f} kWh<extra></extra>"
    ))
    
    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font_color="#2C3E50",
        showlegend=False,  # Hide legend completely
        margin=dict(l=50, r=50, t=20, b=50),
        xaxis=dict(showgrid=True, gridcolor="lightgrey"),
        yaxis=dict(showgrid=True, gridcolor="lightgrey"),
        dragmode=False  # Disable zooming and panning
    )
    
    return point_index, fig

@callback(
    [Output('market-spider-chart', 'figure'),
     Output('market-instances-store', 'data')],
    [Input('selected-point-store', 'data'),
     Input('neighbors-slider', 'value')]
)
def update_spider_chart(selected_idx, n_neighbors):
    """Update spider chart based on selected point and number of neighbors"""
    if selected_idx is None:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            annotations=[{
                'text': 'Click a point on the scatter plot to see neighbors',
                'xref': 'paper', 'yref': 'paper',
                'x': 0.5, 'y': 0.5, 'xanchor': 'center', 'yanchor': 'middle',
                'showarrow': False, 'font': {'size': 16, 'color': 'grey'}
            }],
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF"
        )
        return empty_fig, []
    
    # Ensure n_neighbors is valid
    if n_neighbors is None:
        n_neighbors = 5
    
    # Find closest instances once and use for both spider chart and table
    closest_indices = find_closest_instances(selected_idx, n_neighbors)
    
    # Create spider chart with neighbors
    spider_fig = create_spider_chart(selected_idx, closest_indices)
    
    # Prepare all indices for table (selected + neighbors)
    all_indices = [selected_idx] + closest_indices
    
    return spider_fig, all_indices

# Simplified Market Table Callback (removed filters and pagination)
@callback(
    [Output('market-instance-table', 'data'),
     Output('market-table-info', 'children'),
     Output('market-layers-data', 'data')],
    [Input('market-instances-store', 'data'),
     Input('selected-point-store', 'data'),
     Input('neighbors-slider', 'value')],
    prevent_initial_call=False
)
def update_simplified_market_table(instance_indices, selected_idx, n_neighbors):
    """Simplified market table without filtering and pagination"""
    
    if not instance_indices or selected_idx is None:
        return [], "No instances selected", {}
    
    # Create table data
    table_data = []
    
    for i, idx in enumerate(instance_indices):
        print(f"Processing instance {i}: idx={idx}")
        
        if i == 0:
            # Selected instance from plot dataset
            row = df_plot.iloc[idx]
            instance_name = f"Selected Instance (S{idx})"
            instance_type = "selected"
        else:
            # Market instances from search dataset
            row = df_search.iloc[idx]
            instance_name = f"P{i}"
            instance_type = "market"
        
        # Get product names and layer descriptions based on instance type and index
        if instance_type == "selected":
            # For selected instance: always show blank values
            window_product = "-"
            roof_product = "-"
            wall_product = "-"
            window_layers = []
            roof_layers = []
            wall_layers = []
        else:
            # For market instances: use P{i} -> p{idx} (where idx is the actual index from search dataset)
            scenario_id = f"p{idx}"
            products = get_product_names(scenario_id)
            window_product = products['window_product']
            roof_product = products['roof_product']
            wall_product = products['wall_product']
            
            print(f"DEBUG: Scenario {scenario_id} - Window ID: {products['window_id']}, Roof ID: {products['roof_id']}, Wall ID: {products['wall_id']}")
            
            # Get layer descriptions for each product type
            window_layers = get_layer_descriptions('window', products['window_id'])
            roof_layers = get_layer_descriptions('roof', products['roof_id'])
            wall_layers = get_layer_descriptions('wall', products['wall_id'])
            
            print(f"DEBUG: Final layers - Window: {len(window_layers)}, Roof: {len(roof_layers)}, Wall: {len(wall_layers)}")
        
        # Handle different column names between datasets
        def get_value(row, col_name, alternative_names=None):
            if col_name in row.index:
                return float(row[col_name])
            if alternative_names:
                if isinstance(alternative_names, str):
                    alternative_names = [alternative_names]
                for alt_name in alternative_names:
                    if alt_name in row.index:
                        return float(row[alt_name])
            return 0.0
        
        # Use correct column names based on dataset type
        if instance_type == "selected":
            # Plot dataset columns
            row_data = {
                'instance_name': instance_name,
                'transmittance': get_value(row, 'transmittance') * 100,
                'window_shgc': get_value(row, 'window_shgc'),
                'window_u': get_value(row, 'window_u'),
                'window_product': window_product,
                'roof_u': get_value(row, 'roof_u'),
                'roof_product': roof_product,
                'wall_u': get_value(row, 'wall_u'),
                'wall_product': wall_product,
                'cooling_load': get_value(row, 'cooling_load'),
                'heating_load': get_value(row, 'heating_load'),
                'instance_idx': idx
            }
        else:
            # Search dataset columns
            row_data = {
                'instance_name': instance_name,
                'transmittance': get_value(row, 'transmittance') * 100,
                'window_shgc': get_value(row, 'window_shgc'),
                'window_u': get_value(row, 'window_u'),
                'window_product': window_product,
                'roof_u': get_value(row, 'roof_u'),
                'roof_product': roof_product,
                'wall_u': get_value(row, 'wall_u'),
                'wall_product': wall_product,
                'cooling_load': get_value(row, 'predicted_cooling_load'),
                'heating_load': get_value(row, 'predicted_heating_load'),
                'instance_idx': idx
            }
        
        table_data.append(row_data)
    
    # Table info (simplified)
    total_rows = len(table_data)
    if total_rows == 0:
        table_info = "No instances found"
    else:
        n_market_instances = max(0, total_rows - 1)  # Exclude selected instance
        table_info = f"{n_market_instances} market instances shown"
    
    # Create layers data for JavaScript (indexed by actual array position)
    layers_data = {}
    print(f"DEBUG: Creating layers_data for {len(table_data)} table rows")
    
    # We need to recalculate layers for each instance since we removed them from table_data
    for i, idx in enumerate(instance_indices):
        if i == 0:
            # Selected instance: always show blank values
            window_layers = []
            roof_layers = []
            wall_layers = []
        else:
            # Market instances: use P{i} -> p{idx} (where idx is the actual index from search dataset)
            scenario_id = f"p{idx}"
            products = get_product_names(scenario_id)
            
            # Get layer descriptions for each product type
            window_layers = get_layer_descriptions('window', products['window_id'])
            roof_layers = get_layer_descriptions('roof', products['roof_id'])
            wall_layers = get_layer_descriptions('wall', products['wall_id'])
        
        instance_name = f"Selected Instance (S{idx})" if i == 0 else f"P{i}"
        layers_data[i] = {
            'window_layers': window_layers,
            'roof_layers': roof_layers,
            'wall_layers': wall_layers
        }
        print(f"DEBUG: Table row {i} ({instance_name}) - Window layers: {len(window_layers)}, Roof layers: {len(roof_layers)}, Wall layers: {len(wall_layers)}")

    print(f"DEBUG: Final layers_data keys being sent to JavaScript: {list(layers_data.keys())}")
    
    return table_data, table_info, layers_data

# CSV EXPORT CALLBACK - TEK VE DOĞRU CALLBACK
@callback(
    Output('market-download-instances', 'data'),
    Input('export-market-button', 'n_clicks'),
    [State('market-instance-table', 'selected_rows'),
     State('market-instance-table', 'data')],
    prevent_initial_call=True
)
def export_market_selected_instances(n_clicks, selected_rows, table_data):
    """Export selected market instances to CSV"""
    
    if not n_clicks or not table_data:
        raise PreventUpdate
    
    try:
        # Seçili satırları belirle - eğer hiç seçim yoksa tüm satırları al
        if selected_rows:
            selected_data = [table_data[i] for i in selected_rows if i < len(table_data)]
        else:
            selected_data = table_data  # Hiç seçim yoksa tüm veriyi al
        
        if not selected_data:
            raise PreventUpdate
        
        print(f"MARKET CSV EXPORT: Processing {len(selected_data)} instances for CSV export")
        
        # DataFrame'e dönüştür
        export_df = pd.DataFrame(selected_data)
        
        # Export için sütunları yeniden düzenle ve temizle
        export_columns = {
            'instance_name': 'Instance',
            'transmittance': 'Transmittance (%)',
            'window_shgc': 'SHGC',
            'window_u': 'Window-U (W/m²K)',
            'window_product': 'Window Product',
            'roof_u': 'Roof-U (W/m²K)',
            'roof_product': 'Roof Product', 
            'wall_u': 'Wall-U (W/m²K)',
            'wall_product': 'Wall Product',
            'cooling_load': 'Ideal Cooling (kWh)',
            'heating_load': 'Ideal Heating (kWh)'
        }
        
        # Sadece mevcut sütunları seç
        available_columns = [col for col in export_columns.keys() if col in export_df.columns]
        export_df = export_df[available_columns]
        
        # Sütun adlarını değiştir
        export_df = export_df.rename(columns={col: export_columns[col] for col in available_columns})
        
        # Sayısal sütunları formatla
        numeric_columns = ['Transmittance (%)', 'SHGC', 'Window-U (W/m²K)', 
                          'Roof-U (W/m²K)', 'Wall-U (W/m²K)', 
                          'Ideal Cooling (kWh)', 'Ideal Heating (kWh)']
        
        for col in numeric_columns:
            if col in export_df.columns:
                export_df[col] = pd.to_numeric(export_df[col], errors='coerce').round(3)
        
        # Timestamp ile dosya adı oluştur
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"LUX_MarketAvailableScenarios_{timestamp}.csv"
        
        print(f"MARKET CSV EXPORT: Sending CSV file {filename} with {len(export_df)} rows and {len(export_df.columns)} columns")
        
        # CSV olarak indir
        return dcc.send_data_frame(export_df.to_csv, filename, index=False)
        
    except Exception as e:
        print(f"MARKET CSV EXPORT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return dash.no_update


# Manage selected rows for market table
@callback(
    Output('market-instance-table', 'selected_rows'),
    Input('market-instance-table', 'data'),
    prevent_initial_call=False
)
def update_market_table_selection(table_data):
    """Pre-select market instances (all except the first selected instance)"""
    if table_data and len(table_data) > 1:
        # Select all rows except the first one (which is the selected instance)
        return list(range(1, len(table_data)))
    return []


# Client-side callback for hover functionality
clientside_callback(
    """
    function(layersData) {
        console.log('DEBUG: Client-side callback triggered with layers data:', layersData);
        
        // Wait for DOM to be ready
        setTimeout(function() {
            console.log('DEBUG: Setting up hover listeners');
            
            // Remove existing listeners
            document.querySelectorAll('td[data-dash-column="window_product"], td[data-dash-column="roof_product"], td[data-dash-column="wall_product"]').forEach(cell => {
                if (cell.hasAttribute('data-hover-initialized')) {
                    cell.removeAttribute('data-hover-initialized');
                }
            });
            
            // Add new listeners
            document.querySelectorAll('td[data-dash-column="window_product"], td[data-dash-column="roof_product"], td[data-dash-column="wall_product"]').forEach(cell => {
                if (!cell.hasAttribute('data-hover-initialized')) {
                    cell.setAttribute('data-hover-initialized', 'true');
                    
                    cell.addEventListener('mouseenter', function() {
                        const columnType = this.getAttribute('data-dash-column').replace('_product', '');
                        
                        // Get row index using DOM-based calculation only
                        const cellElement = this;
                        const rowElement = cellElement.closest('tr');
                        const tbody = cellElement.closest('tbody');
                        const allDataRows = Array.from(tbody.querySelectorAll('tr'));
                        let actualRowIndex = allDataRows.indexOf(rowElement);

                        // CRITICAL FIX: Account for header row in table structure
                        if (actualRowIndex > 0) {
                            actualRowIndex = actualRowIndex - 1;
                        }

                        console.log('DEBUG: Raw DOM index:', allDataRows.indexOf(rowElement));
                        console.log('DEBUG: Adjusted actualRowIndex after header compensation:', actualRowIndex);
                        
                        const layers = layersData && layersData[actualRowIndex] && layersData[actualRowIndex][columnType + '_layers'] || [];
                        console.log('DEBUG: Looking for layers at index', actualRowIndex, 'for column', columnType);
                        console.log('DEBUG: Found layers:', layers);
                        
                        // Create bubble
                        createProductBubble(cellElement, layers, columnType);
                    });
                    
                    cell.addEventListener('mouseleave', function() {
                        removeProductBubble();
                    });
                }
            });
        }, 500);
        
        return null;
    }
    """,
    Output('market-hover-state', 'data'),
    Input('market-layers-data', 'data')
)

# JavaScript functions for bubble creation
clientside_callback(
    """
    function() {
        // Define the bubble creation function
        window.createProductBubble = function(element, layers, productType) {
            console.log('DEBUG: createProductBubble called with layers:', layers, 'productType:', productType);
            
            // Remove existing bubble
            const existingBubble = document.querySelector('.product-hover-bubble');
            if (existingBubble) {
                existingBubble.remove();
            }
            
            // Dynamic height calculation
            const minHeight = 160;
            const maxHeight = 400;
            let bubbleHeight = minHeight;
            
            if (layers && layers.length > 0) {
                const calculatedHeight = 40 + (layers.length * 25);
                bubbleHeight = Math.min(maxHeight, Math.max(minHeight, calculatedHeight));
                console.log('DEBUG: Calculated height for', layers.length, 'layers:', calculatedHeight, '-> final:', bubbleHeight);
            }
            
            // Create bubble container
            const bubble = document.createElement('div');
            bubble.className = 'product-hover-bubble';
            bubble.style.cssText = `
                position: fixed;
                width: 320px;
                height: ${bubbleHeight}px;
                background-color: #FFFFFF;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
                z-index: 10000;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.3s ease;
                padding: 0;
                box-sizing: border-box;
                display: flex;
                overflow: hidden;
            `;
            
            // Create left side for image
            const leftSide = document.createElement('div');
            leftSide.style.cssText = `
                width: 160px;
                height: ${bubbleHeight}px;
                background-image: url('/assets/${productType}_product.png');
                background-size: 154px 138px;
                background-position: center top 10px;
                background-repeat: no-repeat;
                border-radius: 12px 0 0 12px;
                flex-shrink: 0;
            `;
            
            // Create right side for layers
            const rightSide = document.createElement('div');
            rightSide.style.cssText = `
                width: 160px;
                height: ${bubbleHeight}px;
                overflow-y: auto;
                padding: 10px;
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
                scrollbar-width: thin;
            `;
            
            // Add layer descriptions
            if (layers && layers.length > 0) {
                console.log('DEBUG: Adding', layers.length, 'layers to bubble');
                
                // Add title
                const title = document.createElement('div');
                title.textContent = 'Layers (Outside to Inside):';
                title.style.cssText = `
                    font-family: 'Poppins', sans-serif;
                    font-size: 11px;
                    font-weight: 600;
                    color: #2AACFD;
                    margin-bottom: 8px;
                    border-bottom: 1px solid #E0E0E0;
                    padding-bottom: 4px;
                `;
                rightSide.appendChild(title);
                
                // Add layers
                layers.forEach((layer, index) => {
                    console.log('DEBUG: Adding layer', index, ':', layer);
                    const layerDiv = document.createElement('div');
                    layerDiv.textContent = layer;
                    layerDiv.style.cssText = `
                        font-family: 'Poppins', sans-serif;
                        font-size: 8px;
                        line-height: 1.4;
                        color: #333;
                        margin-bottom: 3px;
                        padding: 4px 6px;
                        background-color: rgba(42, 172, 253, 0.08);
                        border-radius: 4px;
                        border-left: 2px solid #2AACFD;
                        word-wrap: break-word;
                        overflow-wrap: break-word;
                        white-space: normal;
                        min-height: 18px;
                        box-sizing: border-box;
                    `;
                    rightSide.appendChild(layerDiv);
                });
            } else {
                console.log('DEBUG: No layers found, showing "No layer information"');
                const noLayersDiv = document.createElement('div');
                noLayersDiv.textContent = 'No layer information available';
                noLayersDiv.style.cssText = `
                    font-family: 'Poppins', sans-serif;
                    font-size: 10px;
                    color: #999;
                    font-style: italic;
                    text-align: center;
                    padding-top: 50px;
                `;
                rightSide.appendChild(noLayersDiv);
            }
            
            // Assemble bubble
            bubble.appendChild(leftSide);
            bubble.appendChild(rightSide);
            
            // Position bubble
            const rect = element.getBoundingClientRect();
            const tbody = element.closest('tbody');
            const allDataRows = Array.from(tbody.querySelectorAll('tr'));
            const rowIndex = allDataRows.indexOf(element.closest('tr'));
            const totalRows = allDataRows.length;
            const isBottomRows = rowIndex >= Math.max(0, totalRows - 3);
            
            // Calculate position
            let top, left;
            
            if (isBottomRows) {
                top = rect.top - bubbleHeight - 10;
            } else {
                top = rect.bottom + 10;
            }
            
            // Center horizontally on the cell
            left = rect.left + (rect.width / 2) - 160;
            
            // Ensure bubble stays within viewport
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;
            
            if (left + 320 > viewportWidth) {
                left = viewportWidth - 320 - 10;
            }
            if (left < 10) {
                left = 10;
            }
            if (top < 10) {
                top = rect.bottom + 10;
            }
            if (top + bubbleHeight > viewportHeight) {
                top = rect.top - bubbleHeight - 10;
            }
            
            bubble.style.top = top + 'px';
            bubble.style.left = left + 'px';
            
            // Add to document
            document.body.appendChild(bubble);
            
            // Fade in
            setTimeout(() => {
                bubble.style.opacity = '1';
            }, 10);
            
            return bubble;
        };
        
        // Define the bubble removal function
        window.removeProductBubble = function() {
            const bubble = document.querySelector('.product-hover-bubble');
            if (bubble) {
                bubble.style.opacity = '0';
                setTimeout(() => {
                    if (bubble.parentNode) {
                        bubble.parentNode.removeChild(bubble);
                    }
                }, 300);
            }
        };
        
        console.log('DEBUG: JavaScript functions defined');
        return null;
    }
    """,
    Output('market-hover-state', 'data', allow_duplicate=True),
    Input('market-instance-table', 'data'),
    prevent_initial_call=True
)