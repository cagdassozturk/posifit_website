from dash import html, dcc, dash_table
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import dash
from dash import html, dcc

# Türkiye market page for optimized pilot
# Note: This page is registered in dash_app.py, not here

from pages.turkiye_optimized import df as df_plot  # optimized Türkiye dataset

df_search = pd.read_excel(
    "data/turkiye/TUR_combinations_with_predictions_UPDATED.xlsx",
    engine="openpyxl"
)

# Products data for Türkiye - build lookup from search dataset (it contains product info)
try:
    # The search dataset already contains product information
    products_lookup = df_search.set_index('scenario')[
        ['wall_name_shorter', 'window_name_shorter', 'roof_name_shorter',
         'wall_id', 'window_id', 'roof_id']
    ].to_dict('index')
except Exception as e:
    print(f"Warning: Could not build products lookup from search dataset: {e}")
    products_lookup = {}

# Layers data for Türkiye (from Türkiye-specific Excel file)
try:
    layers_data = pd.read_excel(
        "data/turkiye/TR_Passive Solutions and Alternative Material List_new.xlsx",
        sheet_name=None,
        engine='openpyxl'
    )
    layers_lookup = {
        'wall': layers_data.get('External Wall', pd.DataFrame()),
        'roof': layers_data.get('Roof', pd.DataFrame()),
        'window': layers_data.get('Window', pd.DataFrame())
    }
except Exception as e:
    print(f"Warning: Could not load TR_Passive Solutions and Alternative Material List_new.xlsx: {e}")
    layers_lookup = {'wall': pd.DataFrame(), 'roof': pd.DataFrame(), 'window': pd.DataFrame()}


def get_product_names(scenario_id: str):
    if scenario_id in products_lookup:
        products = products_lookup[scenario_id]
        return {
            'wall_product': products.get('wall_name_shorter', '-'),
            'window_product': products.get('window_name_shorter', '-'),
            'roof_product': products.get('roof_name_shorter', '-'),
            'wall_id': products.get('wall_id', None),
            'window_id': products.get('window_id', None),
            'roof_id': products.get('roof_id', None),
        }
    return {
        'wall_product': '-',
        'window_product': '-',
        'roof_product': '-',
        'wall_id': None,
        'window_id': None,
        'roof_id': None,
    }


def get_layer_descriptions(product_type: str, product_id):
    """Get layer descriptions for a product type and ID from Türkiye Excel file
    
    In Türkiye Excel file, layers are stored differently than Luxembourg:
    - The ID appears only in the first row of a component
    - Subsequent rows with NaN ID belong to the same component
    - We need to collect all rows from the matching ID until the next non-NaN ID
    """
    if product_id is None or (isinstance(product_id, float) and pd.isna(product_id)):
        return []

    if product_type not in layers_lookup:
        return []

    df_layers = layers_lookup[product_type]
    if df_layers.empty or 'ID' not in df_layers.columns:
        return []

    # Handle column name differences: Window sheet has typo "Layer Desccription" (double 'c')
    layer_desc_col = None
    if 'Layer Description' in df_layers.columns:
        layer_desc_col = 'Layer Description'
    elif 'Layer Desccription' in df_layers.columns:  # Typo in Window sheet
        layer_desc_col = 'Layer Desccription'
    else:
        return []

    # Handle type mismatches: convert both to string for comparison
    # Some IDs are strings, some are integers (especially roof IDs like 20130003)
    product_id_str = str(product_id)
    df_layers_id_str = df_layers['ID'].astype(str)
    
    # Find the row index where the ID matches
    matching_indices = df_layers.index[df_layers_id_str == product_id_str].tolist()
    
    if not matching_indices:
        return []
    
    # Get the first matching row index
    start_idx = matching_indices[0]
    
    # Collect all rows from start_idx until the next non-NaN ID (or end of dataframe)
    layer_descriptions = []
    for idx in range(start_idx, len(df_layers)):
        row = df_layers.iloc[idx]
        
        # Stop if we hit the next component (non-NaN ID that's different from our product_id)
        if pd.notna(row['ID']) and str(row['ID']) != product_id_str:
            break
        
        # Extract layer description from this row
        layer_desc = row.get(layer_desc_col)
        if pd.notna(layer_desc) and layer_desc.strip():  # Only add non-empty descriptions
            layer_descriptions.append(str(layer_desc).strip())
    
    return layer_descriptions


def find_closest_instances(selected_idx, n_neighbors=5):
    if selected_idx is None or selected_idx >= len(df_plot):
        return []

    selected_row = df_plot.iloc[selected_idx]
    selected_heating = selected_row['heating_load']
    selected_cooling = selected_row['cooling_load']

    search_features = ['predicted_heating_load', 'predicted_cooling_load']
    if 'predicted_heating_load' not in df_search.columns or 'predicted_cooling_load' not in df_search.columns:
        heating_cols = [c for c in df_search.columns if 'heating' in c.lower()]
        cooling_cols = [c for c in df_search.columns if 'cooling' in c.lower()]
        if heating_cols and cooling_cols:
            search_features = [heating_cols[0], cooling_cols[0]]
        else:
            print("WARNING (TUR market opt): could not find heating/cooling cols in df_search")
            return []

    feature_matrix = df_search[search_features].values

    plot_heating = df_plot['heating_load']
    plot_cooling = df_plot['cooling_load']
    search_heating = df_search[search_features[0]]
    search_cooling = df_search[search_features[1]]

    norm_sel_heat = (selected_heating - plot_heating.min()) / (plot_heating.max() - plot_heating.min())
    norm_sel_cool = (selected_cooling - plot_cooling.min()) / (plot_cooling.max() - plot_cooling.min())

    norm_search_heat = (feature_matrix[:, 0] - search_heating.min()) / (search_heating.max() - search_heating.min())
    norm_search_cool = (feature_matrix[:, 1] - search_cooling.min()) / (search_cooling.max() - search_cooling.min())

    normalized_selected = np.array([[norm_sel_heat, norm_sel_cool]])
    normalized_search = np.column_stack([norm_search_heat, norm_search_cool])

    from sklearn.metrics.pairwise import euclidean_distances

    distances = euclidean_distances(normalized_selected, normalized_search)[0]
    closest_indices = np.argsort(distances)[:n_neighbors]
    return closest_indices.tolist()


def normalize_for_spider(value, param_name):
    ranges = {
        'Wall-U (W/m²K)': (0.1, 0.8),
        'Window-U (W/m²K)': (0.7, 2.5),
        'Roof-U (W/m²K)': (0.1, 0.5),
        'SHGC': (0.3, 0.9),
        'Ideal Heating (kWh)': (15000, 35000),
        'Ideal Cooling (kWh)': (100, 1000),
        'Transmittance (%)': (10, 90),
    }
    if param_name not in ranges:
        return 0.5
    min_val, max_val = ranges[param_name]
    clamped = max(min_val, min(value, max_val))
    norm = (clamped - min_val) / (max_val - min_val)
    return max(0.1, min(0.9, norm))


def create_spider_chart(selected_idx, closest_indices):
    if selected_idx is None:
        return go.Figure()

    parameters = [
        'Wall-U (W/m²K)', 'Roof-U (W/m²K)', 'SHGC',
        'Ideal Heating (kWh)', 'Ideal Cooling (kWh)', 'Transmittance (%)',
        'Window-U (W/m²K)',
    ]
    col_mapping = {
        'Wall-U (W/m²K)': 'wall_u',
        'Window-U (W/m²K)': 'window_u',
        'Roof-U (W/m²K)': 'roof_u',
        'SHGC': 'window_shgc',
        'Ideal Heating (kWh)': 'heating_load',
        'Ideal Cooling (kWh)': 'cooling_load',
        'Transmittance (%)': 'transmittance',
    }

    fig = go.Figure()

    base_colors = ['#011928', '#083D5E', '#107ABC', '#2AACFD', '#86D0FE']
    colors = [base_colors[0]]
    for i in range(1, 11):
        if i == 1:
            colors.append(base_colors[1])
        elif i <= 3:
            colors.append(base_colors[2])
        elif i == 4:
            colors.append(base_colors[3])
        else:
            colors.append(base_colors[4])

    selected_row = df_plot.iloc[selected_idx]
    r_vals = []
    for param in parameters:
        col = col_mapping[param]
        value = selected_row.get(col)
        if value is not None:
            if param == 'Transmittance (%)':
                value = value * 100
            r_vals.append(normalize_for_spider(value, param))
        else:
            r_vals.append(0.5)

    fig.add_trace(go.Scatterpolar(
        r=r_vals + [r_vals[0]],
        theta=parameters + [parameters[0]],
        fill='toself',
        name='Selected Instance',
        line_color='white',
        fillcolor=colors[0],
        opacity=1,
        line=dict(width=2, color='white'),
        showlegend=True,
    ))

    for i, idx in enumerate(closest_indices):
        neighbor = df_search.iloc[idx]
        r_vals = []
        for param in parameters:
            col = col_mapping[param]
            value = None
            if col == 'heating_load':
                value = neighbor.get('predicted_heating_load', neighbor.get('heating_load'))
            elif col == 'cooling_load':
                value = neighbor.get('predicted_cooling_load', neighbor.get('cooling_load'))
            else:
                value = neighbor.get(col)

            if value is not None:
                if param == 'Transmittance (%)':
                    value = value * 100
                r_vals.append(normalize_for_spider(value, param))
            else:
                r_vals.append(0.5)

        color_index = min(i + 1, len(colors) - 1)
        fig.add_trace(go.Scatterpolar(
            r=r_vals + [r_vals[0]],
            theta=parameters + [parameters[0]],
            fill='toself',
            name=f'P{i+1}',
            line_color='white',
            fillcolor=colors[color_index],
            opacity=0.6,
            line=dict(width=1.5, color='white'),
            showlegend=True,
        ))

    gradient_y = np.linspace(0, 1, 80)
    gradient_x = [1] * len(gradient_y)
    gradient_values = np.linspace(0, 1, len(gradient_y))
    fixed_colorscale = [
        [0, '#011928'],
        [0.25, '#083D5E'],
        [0.5, '#107ABC'],
        [0.75, '#2AACFD'],
        [1, '#86D0FE'],
    ]

    fig.add_trace(go.Scatter(
        x=gradient_x,
        y=gradient_y,
        mode='markers',
        marker=dict(
            size=18,
            color=gradient_values,
            colorscale=fixed_colorscale,
            showscale=False,
            symbol='square',
            line=dict(width=0),
        ),
        showlegend=False,
        hoverinfo='skip',
        xaxis='x2',
        yaxis='y2',
    ))

    legend_annotations = [
        dict(
            text="<b>Furthest</b>",
            x=0.99, y=0.95,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=12, color="#7B7B7B"),
            xanchor="center",
        ),
        dict(
            text="<b>Closest</b>",
            x=0.99, y=0.07,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=12, color="#7B7B7B"),
            xanchor="center",
        ),
    ]

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
                gridwidth=1,
            ),
            angularaxis=dict(
                tickfont_size=11,
                rotation=90,
                direction="clockwise",
                gridcolor="lightgrey",
                linecolor="grey",
            ),
        ),
        xaxis2=dict(domain=[0.98, 1.0], visible=False, range=[0.8, 1.2]),
        yaxis2=dict(domain=[0.15, 0.88], visible=False, range=[0, 1]),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="lightgrey",
            borderwidth=1,
        ),
        annotations=legend_annotations,
        font=dict(size=10),
        margin=dict(l=50, r=140, t=30, b=80),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        height=400,
        uirevision=True,
    )
    return fig


def create_initial_scatter():
    fig = px.scatter(
        df_plot,
        x="heating_load",
        y="cooling_load",
        labels={
            "heating_load": "Ideal Heating Load (kWh)",
            "cooling_load": "Ideal Cooling Load (kWh)",
        },
    )
    fig.update_traces(
        marker=dict(size=6, opacity=0.7, color="#2AACFD"),
        hovertemplate="Ideal Heating Load: %{x:.1f} kWh<br>"
                      "Ideal Cooling Load: %{y:.1f} kWh<extra></extra>",
    )
    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font_color="#2C3E50",
        showlegend=False,
        margin=dict(l=50, r=50, t=20, b=50),
        xaxis=dict(showgrid=True, gridcolor="lightgrey"),
        yaxis=dict(showgrid=True, gridcolor="lightgrey"),
        dragmode=False,
    )
    return fig


def create_initial_spider():
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[], theta=[], mode='lines+markers', name='Select a point'))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1]),
            angularaxis=dict(tickfont_size=10, rotation=90, direction="clockwise"),
        ),
        showlegend=True,
        font=dict(size=10),
        margin=dict(l=50, r=50, t=20, b=50),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
    )
    return fig


CARDHEADER_STYLE = {
    "backgroundColor": "#F5F5F5",
    "color": "#7B7B7B",
    "borderRadius": "8px 8px 0 0",
    "borderBottom": "none",
    "padding": "8px 16px",
    "fontSize": "20px",
    "paddingBottom": "0px",
    "fontWeight": "200",
    "margin": "0px",
}

CARD_STYLE = {
    "backgroundColor": "#F5F5F5",
    "borderRadius": "8px",
    "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.15)",
    "border": "none",
    "paddingTop": "12px",
    "padding": "0px",
    "overflow": "visible",
}

CARDBODY_STYLE = {
    "paddingTop": "2px",
    "paddingRight": "16px",
    "paddingBottom": "16px",
    "paddingLeft": "16px",
}

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1(
                "Closest Market-Available Scenarios – Türkiye (Optimized)",
                style={
                    "fontFamily": "Poppins, sans-serif",
                    "fontWeight": "600",
                    "fontSize": "32px",
                    "color": "#2C3E50",
                    "textAlign": "center",
                    "marginTop": "30px",
                    "marginBottom": "30px",
                },
            )
        ], width=12),
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("Ideal Loads", style={
                        "fontWeight": "300",
                        "fontSize": "20px",
                        "margin": "0",
                        "color": "#7B7B7B",
                    })
                ], style=CARDHEADER_STYLE),
                dbc.CardBody([
                    dcc.Graph(
                        id="tur-market-optimized-scatter-plot",
                        figure=create_initial_scatter(),
                        style={"height": "400px"},
                        config={
                            'displayModeBar': False,
                            'staticPlot': False,
                            'scrollZoom': False,
                            'doubleClick': False,
                            'showTips': False,
                            'displaylogo': False,
                        },
                    )
                ], style=CARDBODY_STYLE),
            ], style=CARD_STYLE, className="h-100")
        ], width=6),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("Building Parameters", style={
                        "fontWeight": "300",
                        "fontSize": "20px",
                        "margin": "0",
                        "color": "#7B7B7B",
                    })
                ], style=CARDHEADER_STYLE),
                dbc.CardBody([
                    dcc.Graph(
                        id="tur-market-optimized-spider-chart",
                        figure=create_initial_spider(),
                        style={"height": "400px"},
                        config={
                            'displayModeBar': False,
                            'staticPlot': False,
                            'scrollZoom': False,
                            'doubleClick': False,
                            'showTips': False,
                            'displaylogo': False,
                        },
                    )
                ], style=CARDBODY_STYLE),
            ], style=CARD_STYLE, className="h-100")
        ], width=6),
    ], className="mb-4"),

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
                        "marginBottom": "15px",
                    },
                ),
                dcc.Slider(
                    id="tur-market-optimized-neighbors-slider",
                    min=1,
                    max=10,
                    step=1,
                    value=5,
                    marks={i: str(i) for i in range(1, 11)},
                    tooltip={
                        "placement": "top",
                        "always_visible": True,
                        "style": {"fontSize": "14px", "fontWeight": "600"},
                    },
                    className="market-slider",
                ),
            ], style={
                "textAlign": "center",
                "padding": "20px",
                "backgroundColor": "#F8F9FA",
                "borderRadius": "8px",
                "margin": "0 auto",
                "maxWidth": "500px",
            })
        ], width=12),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card(id="tur-market-optimized-instance-table-card", children=[
                dbc.CardHeader([
                    html.H5("Closest Market-Available Instance Table", style={
                        "fontWeight": "300",
                        "fontSize": "20px",
                        "margin": "0",
                        "color": "#7B7B7B",
                        "display": "inline-block",
                        "marginRight": "16px",
                    })
                ], style={
                    "backgroundColor": "#F5F5F5",
                    "borderRadius": "8px 8px 0 0",
                    "padding": "12px 16px",
                    "borderBottom": "none",
                    "position": "relative",
                    "minHeight": "50px",
                }),
                dbc.CardBody([
                    dash_table.DataTable(
                        id="tur-market-optimized-instance-table",
                        columns=[
                            {"name": "Instance Name", "id": "instance_name", "type": "text"},
                            {"name": "Transmittance (%)", "id": "transmittance", "type": "numeric",
                             "format": {"specifier": ".1f"}},
                            {"name": "SHGC", "id": "window_shgc", "type": "numeric",
                             "format": {"specifier": ".3f"}},
                            {"name": "Window-U (W/m²K)", "id": "window_u", "type": "numeric",
                             "format": {"specifier": ".3f"}},
                            {"name": "Window Product", "id": "window_product", "type": "text"},
                            {"name": "Roof-U (W/m²K)", "id": "roof_u", "type": "numeric",
                             "format": {"specifier": ".3f"}},
                            {"name": "Roof Product", "id": "roof_product", "type": "text"},
                            {"name": "Wall-U (W/m²K)", "id": "wall_u", "type": "numeric",
                             "format": {"specifier": ".3f"}},
                            {"name": "Wall Product", "id": "wall_product", "type": "text"},
                            {"name": "Ideal Cooling (kWh)", "id": "cooling_load", "type": "numeric",
                             "format": {"specifier": ".1f"}},
                            {"name": "Ideal Heating (kWh)", "id": "heating_load", "type": "numeric",
                             "format": {"specifier": ".1f"}},
                        ],
                        data=[],
                        filter_action="none",
                        style_table={
                            'overflowX': 'auto',
                            'fontFamily': 'Poppins, sans-serif',
                            'backgroundColor': '#F5F5F5',
                            'borderRadius': '0',
                            'overflow': 'hidden',
                            'border': 'none',
                            'margin': '0',
                        },
                        style_header={
                            'backgroundColor': '#E3E3E3',
                            'fontWeight': '600',
                            'fontSize': '13px',
                            'color': '#666666',
                            'textAlign': 'center',
                            'border': 'none',
                            'whiteSpace': 'normal',
                            'height': '40px',
                            'padding': '12px 8px',
                            'outline': 'none',
                            'boxShadow': 'none',
                        },
                        style_header_conditional=[
                            {
                                'if': {'column_id': 'instance_name'},
                                'borderTopLeftRadius': '8px',
                                'backgroundColor': '#E3E3E3',
                                'border': 'none',
                            },
                            {
                                'if': {'column_id': 'heating_load'},
                                'borderTopRightRadius': '8px',
                                'backgroundColor': '#E3E3E3',
                                'border': 'none',
                            },
                        ],
                        style_cell={
                            'textAlign': 'center',
                            'fontSize': '12px',
                            'fontFamily': 'Poppins, sans-serif',
                            'color': '#333333',
                            'padding': '12px 8px',
                            'border': 'none',
                            'borderBottom': '1px solid #E6E6E6',
                            'backgroundColor': '#F5F5F5',
                            'minWidth': '80px',
                            'maxWidth': '150px',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                        },
                        style_cell_conditional=[
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
                                'position': 'relative',
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
                                'position': 'relative',
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
                                'position': 'relative',
                            },
                        ],
                        style_data_conditional=[
                            {
                                'if': {'column_id': 'instance_name'},
                                'fontWeight': '600',
                                'color': '#2AACFD',
                                'backgroundColor': '#F5F5F5',
                            },
                            {
                                'if': {'row_index': 0},
                                'color': '#063D5E',
                                'fontWeight': '600',
                                'backgroundColor': '#E3F2FD',
                            },
                            {
                                'if': {'state': 'selected'},
                                'backgroundColor': '#E3F2FD',
                                'border': '1px solid #2AACFD',
                            },
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': '#EEEEEE',
                            },
                            {
                                'if': {'row_index': 'even'},
                                'backgroundColor': '#F5F5F5',
                            },
                        ],
                        sort_action="native",
                        row_selectable="multi",
                        selected_rows=[],
                        include_headers_on_copy_paste=False,
                        merge_duplicate_headers=True,
                        css=[
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th',
                                'rule': 'background-color: #E3E3E3 !important; color: #666666 !important; '
                                        'font-weight: 600 !important; border: none !important; box-shadow: none !important;',
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th:first-child',
                                'rule': 'border-top-left-radius: 8px !important; background-color: #E3E3E3 !important; border: none !important;',
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th:last-child',
                                'rule': 'border-top-right-radius: 8px !important; background-color: #E3E3E3 !important; border: none !important;',
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner thead',
                                'rule': 'border-bottom: none !important; box-shadow: none !important;',
                            },
                            {
                                'selector': '.dash-table-container',
                                'rule': 'border-radius: 0; overflow: visible; box-shadow: none; background-color: #F5F5F5; border: none;',
                            },
                            {
                                'selector': 'td[data-dash-column="window_product"]',
                                'rule': 'position: relative !important; overflow: visible !important;',
                            },
                            {
                                'selector': 'td[data-dash-column="roof_product"]',
                                'rule': 'position: relative !important; overflow: visible !important;',
                            },
                            {
                                'selector': 'td[data-dash-column="wall_product"]',
                                'rule': 'position: relative !important; overflow: visible !important;',
                            },
                        ],
                    ),

                    dbc.Row([
                        dbc.Col([
                            html.Div(id="tur-market-optimized-table-info", style={
                                "fontSize": "12px",
                                "color": "#6C757D",
                                "padding": "8px 0",
                            })
                        ], width=True),
                        dbc.Col([
                            dbc.Button(
                                "Export Selected",
                                id="tur-export-market-optimized-button",
                                size="sm",
                                style={
                                    "backgroundColor": "#2AACFD",
                                    "border": "none",
                                    "borderRadius": "8px",
                                    "fontSize": "12px",
                                    "fontWeight": "600",
                                    "padding": "8px 16px",
                                },
                            )
                        ], width="auto"),
                    ], align="center", className="mt-2"),

                ], style={
                    "paddingTop": "0px",
                    "paddingRight": "16px",
                    "paddingBottom": "16px",
                    "paddingLeft": "16px",
                    "overflow": "visible",
                }),
            ], style=CARD_STYLE)
        ], width=12),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Button(
                "← Back to Türkiye Optimized",
                href="/pilot_tur_optimized",
                external_link=True,
                color="primary",
                style={
                    "marginTop": "20px",
                    "backgroundColor": "#2AACFD",
                    "border": "none",
                    "borderRadius": "8px",
                    "fontFamily": "Poppins, sans-serif",
                    "fontWeight": "500",
                },
            )
        ], width=12, className="text-center"),
    ]),

    dcc.Store(id="tur-market-optimized-selected-point-store", data=None),
    dcc.Store(id="tur-market-optimized-instances-store", data=[]),
    dcc.Store(id="tur-market-optimized-table-selected-instances", data=[]),
    dcc.Download(id="tur-market-optimized-download-instances"),
    dcc.Store(id="tur-market-optimized-layers-data", data={}),
    dcc.Store(id="tur-market-optimized-hover-state", data={}),

], fluid=True, style={
    "backgroundColor": "#FFFFFF",
    "padding": "20px",
    "minHeight": "100vh",
})


