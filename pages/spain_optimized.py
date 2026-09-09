# pages/spain_optimized.py - Spain Optimized Page
from dash import html, dcc, dash_table, register_page, callback
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dash_table.Format import Format, Scheme
from dash import html
import dash
from dash import html, dcc

# Dataset - Spain optimized data (comma-separated)
df = pd.read_csv("data/spain/pareto_front_predicted_100_spa.csv")

# Insert baseline as first row for Spain
baseline_spain = {
    'window_u': 2.16,
    'shgc': 0.71,
    'roof_u': 1.13,
    'extWall_u': 1.55,
    'transmittance': None,
    'total_idealHeating': 279129.3437,
    'total_idealCooling': 144108.8554
}
# Add any other columns with default values
for col in df.columns:
    if col not in baseline_spain:
        baseline_spain[col] = None

baseline_df = pd.DataFrame([baseline_spain])
df = pd.concat([baseline_df, df], ignore_index=True)

# Rename columns to match the expected format
column_mapping = {
    'extWall_u': 'wall_u',
    'shgc': 'window_shgc',
    'total_idealHeating': 'heating_load',
    'total_idealCooling': 'cooling_load'
}
df = df.rename(columns=column_mapping)

# Add co2 column if it doesn't exist
if 'co2' not in df.columns:
    df['co2'] = 0

#ID column
id_column = None
for col in df.columns:
    if col.strip().lower() == "version":
        id_column = col
        break
if id_column is None:
    df.insert(0, "ID", df.index)
    id_column = "ID"

# labels for the parallel coordinates plot
labels = {
    'scenario': 'Scenario',
    'wall_u': 'Wall-U',
    'window_u': 'Window-U', 
    'window_shgc': 'Window-SHGC',
    'roof_u': 'Roof-U',
    'transmittance': 'Transmittance',
    'heating_load': 'Heating Load',
    'cooling_load': 'Cooling Load'
}

# Choose a meaningful color column (heating_load preferred)
preferred_color_columns = ["heating_load", "cooling_load"]
color_col = None
for c in preferred_color_columns:
    if c in df.columns:
        color_col = c
        break
if color_col is None:
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if len(numeric_cols) > 0:
        color_col = numeric_cols[-1]
    else:
        color_col = "heating_load" if "heating_load" in df.columns else df.columns[-1]
        df[color_col] = pd.to_numeric(df[color_col], errors='coerce')

# Remove the first column (ID)
desired_columns = ['wall_u', 'window_u', 'window_shgc', 'roof_u', 
                  'transmittance', 'heating_load', 'cooling_load']
dimensions_to_plot = [col for col in desired_columns if col in df.columns]

# Custom color palette
custom_color_palette = ['#083D5E',  '#2AACFD', '#C8E9FE']

custom_color_scale = [
    (0.0, '#083D5E'),
    (0.5, '#2AACFD'),
    (1.0, '#C8E9FE')
]

fig_parallel = px.parallel_coordinates(
    df,
    dimensions=dimensions_to_plot,
    color=color_col,
    labels=labels,
    color_continuous_scale=custom_color_scale,
)

fig_parallel.update_layout(
    coloraxis_colorbar=dict(title="Qheating"),
    margin=dict(l=35, r=50, t=50, b=60),
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    font_color="#2C3E50"
)
fig_parallel.update_traces(unselected=dict(line=dict(opacity=0)))

# Scatter plot
scatter_options = {
    "Scatter 1": {"x": "heating_load", "y": "cooling_load"}
}

def create_scatter_figure_spain_opt(option_key):
    option = scatter_options[option_key]
    x_col = option["x"]
    y_col = option["y"]
    
    df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
    df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
    
    df_with_id = df.copy()
    df_with_id['ID'] = df_with_id.index + 1
    
    df_with_id['label'] = df_with_id['ID'].apply(lambda x: "Baseline" if x == 1 else f"S{x}")
    
    fig = px.scatter(
        df_with_id,
        x=x_col,
        y=y_col,
        hover_data={"ID": True, "label": False},
        custom_data=['label']
    )
    
    axis_labels = {
        "cooling_load": "Ideal Cooling Load (kWh)",
        "heating_load": "Ideal Heating Load (kWh)",
        "Pareto_TIC (kWh)": "Pareto TIC (kWh)",
        "Simulation_TIC (kWh)": "Simulation TIC (kWh)",
        "Simulation_TIH (kWh)": "Simulation TIH (kWh)",
        "MAPE_cooling": "MAPE Cooling (%)",
        "MAPE_heating": "MAPE Heating (%)"
    }
    
    x_title = axis_labels.get(x_col, x_col)
    y_title = axis_labels.get(y_col, y_col)
    
    fig.update_traces(
        marker=dict(size=4, opacity=0.7, color='#2AACFD'),
        selected=dict(marker=dict(color='#083D5E', opacity=1, size=6)),
        unselected=dict(marker=dict(opacity=0.3)),
        hovertemplate='<b>%{customdata[0]}</b><br>' +
                     f'{x_title}: %{{x}}<br>' +
                     f'{y_title}: %{{y}}<br>' +
                     '<extra></extra>'
    )
    
    fig.update_layout(
        clickmode='event+select',
        dragmode='select',
        margin=dict(l=30, r=20, t=20, b=60),
        xaxis=dict(
            title=x_title,
            showgrid=True,
            gridcolor="lightgrey",
            zeroline=True,
            zerolinecolor="black"
        ),
        yaxis=dict(
            title=y_title,
            showgrid=True,
            gridcolor="lightgrey",
            zeroline=True,
            zerolinecolor="black"
        ),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font_color="#2C3E50",
        uirevision='spa-opt-scatter-plot'
    )
    return fig

def create_enhanced_modal_spain_opt():
    return html.Div([
        html.Div(
            id="spa-opt-image-modal", 
            className="modal", 
            tabIndex=0, 
            style={"display": "none"},
            children=[
                html.Div([
                    html.Button("×", id="spa-opt-modal-close", className="modal-close"),
                    
                    html.Div([
                        html.Button(
                            html.Div("❮", style={
                                "fontSize": "24px", 
                                "fontWeight": "bold",
                                "color": "#FFFFFF"
                            }), 
                            id="spa-opt-modal-prev", 
                            className="modal-nav-btn modal-prev"
                        ),
                        
                        html.Div([
                            html.Div(
                                id="spa-opt-modal-title",
                                className="modal-title-text",
                                style={
                                    "textAlign": "center",
                                    "marginBottom": "15px",
                                    "fontSize": "18px",
                                    "fontWeight": "600",
                                    "color": "#2C3E50"
                                }
                            ),
                            html.Img(
                                id="spa-opt-modal-image", 
                                className="modal-image",
                                style={"maxWidth": "80vw", "maxHeight": "70vh"}
                            )
                        ], className="modal-image-container"),
                        
                        html.Button(
                            html.Div("❯", style={
                                "fontSize": "24px", 
                                "fontWeight": "bold",
                                "color": "#FFFFFF"
                            }), 
                            id="spa-opt-modal-next", 
                            className="modal-nav-btn modal-next"
                        )
                    ], className="modal-navigation")
                    
                ], className="modal-content-enhanced")
            ]
        ),
        
        dcc.Store(id="spa-opt-current-image-index", data=0),
        
        dcc.Input(
            id="spa-opt-keyboard-listener",
            style={"position": "absolute", "left": "-9999px", "opacity": "0"},
            autoFocus=False
        )
    ])

initial_scatter_option = "Scatter 1"
fig_scatter = create_scatter_figure_spain_opt(initial_scatter_option)

# custom styles
CARDHEADER_STYLE = {
    "backgroundColor": "#F5F5F5",
    "color": "#7B7B7B",
    "borderRadius": "8px 8px 0 0",
    "borderBottom": "none",
    "boxShadow": "none",
    "padding": "8px 16px",
    "fontSize": "20px",
    "paddingBottom": "3px",
    "fontWeight": "200",
    "margin": "0px"
}
CARD_STYLE = {
    "backgroundColor": "#F5F5F5",
    "borderRadius": "16px",
    "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.15)",
    "border": "none",
    "paddingTop": "12px",
    "padding": "0px"
}

DROPDOWN_STYLE = {"position": "absolute", "top": "480px", "left": "10px",
                  "width": "200px", "zIndex": "2000", "backgroundColor": "rgba(236, 240, 241, 0)",
                  "padding": "2px", "borderRadius": "0px", "border": "1px solid #bdc3c7"}
CHECKBOX_STYLE = {"position": "absolute", "zIndex": "1000", "backgroundColor": "rgba(236, 240, 241, 0)",
                  "padding": "5px", "borderRadius": "5px"}
                  
CARDBODY_STYLE_NO_TOP_PADDING = {
    "paddingTop": "0px",
    "paddingRight": "16px",
    "paddingBottom": "16px",
    "paddingLeft": "16px"
}

layout = dbc.Container([
    
    # Instance Comparison Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Div(
                            id="spa-opt-virtual-dropdown-trigger",
                            children="Select instances...",
                            className="main-instance-dropdown-enhanced",
                            style={
                                "backgroundColor": "#2AACFD",
                                "color": "white",
                                "padding": "12px 16px",
                                "borderRadius": "12px",
                                "cursor": "pointer",
                                "fontFamily": "Poppins, sans-serif",
                                "fontWeight": "600",
                                "fontSize": "16px",
                                "minHeight": "48px",
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "space-between",
                                "boxShadow": "0 4px 12px rgba(0,0,0,0.2)",
                                "transition": "all 0.3s ease",
                                "border": "none"
                            },
                            n_clicks=0
                        ),
                        
                        html.Div(
                            id="spa-opt-virtual-scroll-container",
                            className="enhanced-dropdown-menu",
                            style={
                                "display": "none",
                                "position": "absolute",
                                "top": "100%",
                                "left": "0",
                                "right": "0",
                                "zIndex": "1000",
                                "height": "320px",
                                "maxHeight": "320px",
                                "minHeight": "320px",
                                "overflowY": "auto",
                                "overflowX": "hidden",
                                "border": "1px solid #E0E0E0",
                                "borderRadius": "8px",
                                "backgroundColor": "white",
                                "boxShadow": "0 4px 12px rgba(0,0,0,0.15)",
                                "flexDirection": "column",
                                "boxSizing": "border-box",
                                "willChange": "scroll-position",
                                "transform": "translateZ(0)",
                                "backfaceVisibility": "hidden",
                                "perspective": "1000px"
                            },
                            children=[]
                        ),
                        
                        html.Div(
                            id="spa-opt-warning-overlay",
                            className="warning-overlay",
                            style={
                                "display": "none",
                                "position": "absolute",
                                "top": "calc(100% + 8px)",
                                "left": "0",
                                "right": "0",
                                "zIndex": "1001",
                                "backgroundColor": "rgba(248, 249, 250, 0.98)",
                                "backdropFilter": "blur(10px)",
                                "border": "2px solid #DC3545",
                                "borderRadius": "8px",
                                "boxShadow": "0 8px 25px rgba(220, 53, 69, 0.4)",
                                "padding": "12px 16px",
                                "minHeight": "44px",
                                "transition": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                                "transform": "translateY(-5px)",
                                "opacity": "0"
                            },
                            children=[]
                        )
                        
                    ], className="enhanced-dropdown-container", style={"marginBottom": "16px", "position": "relative"}),
                    
                    dcc.Store(id="spa-opt-comparison-selected-instances-store", data=[]),
                    dcc.Store(id="spa-opt-selection-warning-state", data={"show": False, "message": ""}),
                    dcc.Store(id="spa-opt-virtual-scroll-position", data=0),
                    dcc.Store(id="spa-opt-virtual-item-height", data=40),
                    dcc.Store(id="spa-opt-virtual-container-height", data=320),
                    dcc.Store(id="spa-opt-selected-instances-store", data=[]),
                    dcc.Store(id="spa-opt-dropdown-open-state", data=False),
                    
                    dbc.Row([
                        dbc.Col(
                            html.Div([
                                dcc.Dropdown(
                                    id='spa-opt-sort-by-dropdown',
                                    options=[
                                        {'label': 'Instance ID (S1, S2...)', 'value': 'ID'},
                                        {'label': 'Heating Ideal Load', 'value': 'heating_load'},
                                        {'label': 'Cooling Ideal Load', 'value': 'cooling_load'},
                                        {'label': 'CO₂ Emission', 'value': 'co2'},
                                    ],
                                    value='ID',
                                    clearable=False,
                                    className='sort-by-blue-dropdown',
                                    placeholder="Sort by"
                                )
                            ], className="dropup"),
                            width=7
                        ),
                        
                        html.Div(id="spa-opt-dummy-search-output", style={"display": "none"}),
                        html.Div(id="spa-opt-dummy-outside-click", style={"display": "none"}),
                        
                        dbc.Col(
                            dbc.Button(
                                "🔍",
                                id="spa-opt-search-toggle-button",
                                className="search-toggle-button",
                                n_clicks=0,
                                style={
                                    "fontSize": "16px",
                                    "backgroundColor": "#F8F9FA",
                                    "border": "2px solid #E9ECEF",
                                    "borderRadius": "50%",
                                    "width": "40px",
                                    "height": "40px",
                                    "padding": "0",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center"
                                }
                            ),
                            width="auto"
                        ),
                    ], className="sort-and-search-container g-0", align="center",
                       style={"marginTop": "8px", "marginBottom": "8px"}),

                    html.Div(
                        dbc.Input(
                            id="spa-opt-search-input",
                            type="number",
                            placeholder="Enter instance number (e.g., 33)...",
                            min=1,
                            max=100,
                            style={
                                "marginBottom": "0px",
                                "fontSize": "14px",
                                "border": "2px solid #2AACFD",
                                "borderRadius": "10px"
                            }
                        ),
                        id="spa-opt-search-input-container",
                        className="search-input-container hidden"
                    ),

                    dcc.Store(id="spa-opt-search-toggle-state", data=False),

                    html.Div([
                        html.Label("Sort Order:", style={
                            "fontFamily": "Poppins, sans-serif",
                            "fontWeight": "500",
                            "fontSize": "13px",
                            "marginBottom": "4px",
                            "color": "#4E5E66"
                        }),
                        dcc.RadioItems(
                            id='spa-opt-sort-order-radio',
                            options=[
                                {'label': ' Ascending', 'value': 'asc'},
                                {'label': ' Descending', 'value': 'desc'},
                            ],
                            value='asc',
                            inline=True,
                            style={
                                "display": "flex",
                                "gap": "20px",
                                "fontSize": "13px"
                            }
                        )
                    ], className="sort-order-section", style={"margin": "8px 10px"}),
                    
                    html.Div(id='spa-opt-instance-parameters', style={"marginTop": "8px"})

                ], style={
                    "paddingTop": "12px",
                    "paddingRight": "16px",
                    "paddingBottom": "12px",
                    "paddingLeft": "16px",
                    "backgroundColor": "#FFFFFF"
                })

                
            ], style={
                "backgroundColor": "#FFFFFF",
                "borderRadius": "8px",
                "border": "none",
                "paddingTop": "12px",
                "padding": "0px"
            },
            className="chosen-instance-card")
        ], width=3),
        
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardBody(
                        html.Div(id="spa-opt-instance-comparison-content"),
                        style={
                            "paddingTop": "0px",
                            "paddingRight": "16px",
                            "paddingBottom": "16px",
                            "paddingLeft": "16px",
                        },
                    ),
                ],
                style=CARD_STYLE,
                className="chosen-instance-card",
            ),
            width=9,
        ),
    ], className="mb-4 align-items-stretch"
    ),
    
    # 3D Model and Comparison Graph Row
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(html.H5("3D Model", style={"fontWeight": "300", "fontSize": "20px"}), style=CARDHEADER_STYLE),
                dbc.CardBody(
                    html.Iframe(src="https://omurbugra.github.io/Graph3dv4",
                                style={"width": "100%", "height": "100%", "min-height": "400px", "border": "none"}),
                    id="spa-opt-model3d-card", style=CARDBODY_STYLE_NO_TOP_PADDING
                )
            ], style=CARD_STYLE, className="h-100"),
            width=4
        ),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Comparison Graph", style={"fontWeight": "300", "fontSize": "20px"}), style=CARDHEADER_STYLE),
                dbc.CardBody(
                    dcc.Graph(id='spa-opt-comparison-graph', style={"height": "100%", "min-height": "400px"}),
                    style=CARDBODY_STYLE_NO_TOP_PADDING
                )
            ], id="spa-opt-comparison-graph-card", style=CARD_STYLE, className="h-100")
        ], width=8)
    ], className="mb-4 align-items-stretch"),

    
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(html.H5("Parallel Coordinates Plot", style={"fontWeight": "300", "fontSize": "20px"}), style=CARDHEADER_STYLE),
                dbc.CardBody(
                    dcc.Graph(id="spa-opt-parallel-plot", figure=fig_parallel),
                    style={
                        "paddingTop": "0px",
                        "paddingRight": "16px",
                        "paddingBottom": "16px",
                        "paddingLeft": "16px"
                    }
                )
            ], style=CARD_STYLE),
            width=8
        ),
    
        dbc.Col(
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H5(
                                "Ideal Loads", 
                                style={
                                    "fontWeight": "300", 
                                    "fontSize": "20px",
                                    "margin": "0",
                                    "color": "#7B7B7B"
                                }
                            )
                        ], width="auto", className="d-flex align-items-center"),
                    ], align="center", justify="between", className="w-100")
                ], style=CARDHEADER_STYLE),
                
                dbc.CardBody(
                    dcc.Graph(id="spa-opt-scatter-plot", figure=fig_scatter),
                    style={
                        "paddingTop": "0px",
                        "paddingRight": "16px",
                        "paddingBottom": "16px",
                        "paddingLeft": "16px"
                    }
                )
            ],
            style=CARD_STYLE),
            width=4
        )
    ], className="mb-4 align-items-stretch"),
    

    # Instance Table Section
    dbc.Row([
        dbc.Col([
            dbc.Card(id="spa-opt-instance-table-card", children=[
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.H5("Instance Table", style={
                                    "fontWeight": "300",
                                    "fontSize": "20px",
                                    "margin": "0",
                                    "color": "#7B7B7B",
                                    "display": "inline-block",
                                    "marginRight": "16px"
                                }),
                                
                                html.Div(id="spa-opt-filter-chips-container", children=[], style={
                                    "display": "inline-flex",
                                    "gap": "8px",
                                    "alignItems": "center",
                                    "flexWrap": "wrap",
                                    "marginTop": "0px",
                                    "marginBottom": "0px"
                                })
                                
                            ], style={
                                "display": "flex",
                                "alignItems": "center",
                                "flexWrap": "wrap",
                                "gap": "8px"
                            })
                        ], width=True),

                        dbc.Col([
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.Button(
                                            "Add Filter+",
                                            id="spa-opt-add-filter-trigger-btn",
                                            className="add-filter-trigger",
                                            style={
                                                "backgroundColor": "transparent",
                                                "border": "1px solid #2AACFD",
                                                "color": "#2AACFD",
                                                "borderRadius": "20px",
                                                "fontSize": "12px",
                                                "padding": "6px 16px",
                                                "height": "30px",
                                                "cursor": "pointer",
                                                "transition": "all 0.3s ease",
                                                "position": "relative",
                                                "zIndex": "1000"
                                            }
                                        ),
                                        
                                        html.Div([
                                            html.Div([
                                                html.Div("Select Parameter:", style={
                                                    "fontSize": "14px",
                                                    "fontWeight": "600",
                                                    "color": "white",
                                                    "marginBottom": "12px",
                                                    "textAlign": "center"
                                                }),
                                                
                                                html.Div([
                                                    html.Div([
                                                        html.Span("Instance", style={"flex": "1"}),
                                                        html.Span("+", style={"fontSize": "18px", "fontWeight": "bold"})
                                                    ], className="filter-param-item", 
                                                    id={"type": "spa-opt-param-selector", "param": "instance_name"},
                                                    style={
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "justifyContent": "space-between",
                                                        "padding": "4px 16px",
                                                        "backgroundColor": "#2AACFD",
                                                        "color": "white",
                                                        "borderRadius": "16px",
                                                        "marginBottom": "8px",
                                                        "cursor": "pointer",
                                                        "fontSize": "14px",
                                                        "fontWeight": "500",
                                                        "transition": "all 0.2s ease"
                                                    }),
                                                    
                                                    html.Div([
                                                        html.Span("Transmittance", style={"flex": "1"}),
                                                        html.Span("+", style={"fontSize": "18px", "fontWeight": "bold"})
                                                    ], className="filter-param-item",
                                                    id={"type": "spa-opt-param-selector", "param": "transmittance"},
                                                    style={
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "justifyContent": "space-between",
                                                        "padding": "4px 16px",
                                                        "backgroundColor": "#2AACFD",
                                                        "color": "white",
                                                        "borderRadius": "16px",
                                                        "marginBottom": "8px",
                                                        "cursor": "pointer",
                                                        "fontSize": "14px",
                                                        "fontWeight": "500",
                                                        "transition": "all 0.2s ease"
                                                    }),
                                                    
                                                    html.Div([
                                                        html.Span("SHGC", style={"flex": "1"}),
                                                        html.Span("+", style={"fontSize": "18px", "fontWeight": "bold"})
                                                    ], className="filter-param-item",
                                                    id={"type": "spa-opt-param-selector", "param": "window_shgc"},
                                                    style={
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "justifyContent": "space-between",
                                                        "padding": "4px 16px",
                                                        "backgroundColor": "#2AACFD",
                                                        "color": "white",
                                                        "borderRadius": "16px",
                                                        "marginBottom": "8px",
                                                        "cursor": "pointer",
                                                        "fontSize": "14px",
                                                        "fontWeight": "500",
                                                        "transition": "all 0.2s ease"
                                                    }),
                                                    
                                                    html.Div([
                                                        html.Span("Wall-U", style={"flex": "1"}),
                                                        html.Span("+", style={"fontSize": "18px", "fontWeight": "bold"})
                                                    ], className="filter-param-item",
                                                    id={"type": "spa-opt-param-selector", "param": "wall_u"},
                                                    style={
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "justifyContent": "space-between",
                                                        "padding": "4px 16px",
                                                        "backgroundColor": "#2AACFD",
                                                        "color": "white",
                                                        "borderRadius": "16px",
                                                        "marginBottom": "8px",
                                                        "cursor": "pointer",
                                                        "fontSize": "14px",
                                                        "fontWeight": "500",
                                                        "transition": "all 0.2s ease"
                                                    }),
                                                    
                                                    html.Div([
                                                        html.Span("Window-U", style={"flex": "1"}),
                                                        html.Span("+", style={"fontSize": "18px", "fontWeight": "bold"})
                                                    ], className="filter-param-item",
                                                    id={"type": "spa-opt-param-selector", "param": "window_u"},
                                                    style={
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "justifyContent": "space-between",
                                                        "padding": "4px 16px",
                                                        "backgroundColor": "#2AACFD",
                                                        "color": "white",
                                                        "borderRadius": "16px",
                                                        "marginBottom": "8px",
                                                        "cursor": "pointer",
                                                        "fontSize": "14px",
                                                        "fontWeight": "500",
                                                        "transition": "all 0.2s ease"
                                                    }),
                                                    
                                                    html.Div([
                                                        html.Span("Roof-U", style={"flex": "1"}),
                                                        html.Span("+", style={"fontSize": "18px", "fontWeight": "bold"})
                                                    ], className="filter-param-item",
                                                    id={"type": "spa-opt-param-selector", "param": "roof_u"},
                                                    style={
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "justifyContent": "space-between",
                                                        "padding": "4px 16px",
                                                        "backgroundColor": "#2AACFD",
                                                        "color": "white",
                                                        "borderRadius": "8px",
                                                        "marginBottom": "8px",
                                                        "cursor": "pointer",
                                                        "fontSize": "14px",
                                                        "fontWeight": "500",
                                                        "transition": "all 0.2s ease"
                                                    }),
                                                    
                                                    html.Div([
                                                        html.Span("Ideal Heating", style={"flex": "1"}),
                                                        html.Span("+", style={"fontSize": "18px", "fontWeight": "bold"})
                                                    ], className="filter-param-item",
                                                    id={"type": "spa-opt-param-selector", "param": "heating_load"},
                                                    style={
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "justifyContent": "space-between",
                                                        "padding": "4px 16px",
                                                        "backgroundColor": "#2AACFD",
                                                        "color": "white",
                                                        "borderRadius": "8px",
                                                        "marginBottom": "8px",
                                                        "cursor": "pointer",
                                                        "fontSize": "14px",
                                                        "fontWeight": "500",
                                                        "transition": "all 0.2s ease"
                                                    }),
                                                    
                                                    html.Div([
                                                        html.Span("Ideal Cooling", style={"flex": "1"}),
                                                        html.Span("+", style={"fontSize": "18px", "fontWeight": "bold"})
                                                    ], className="filter-param-item",
                                                    id={"type": "spa-opt-param-selector", "param": "cooling_load"},
                                                    style={
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "justifyContent": "space-between",
                                                        "padding": "4px 16px",
                                                        "backgroundColor": "#2AACFD",
                                                        "color": "white",
                                                        "borderRadius": "8px",
                                                        "marginBottom": "8px",
                                                        "cursor": "pointer",
                                                        "fontSize": "14px",
                                                        "fontWeight": "500",
                                                        "transition": "all 0.2s ease"
                                                    })
                                                ])
                                            ], id="spa-opt-filter-step-1", style={"display": "block"}),
                                            
                                            html.Div([
                                                html.Div("Set Range:", style={
                                                    "fontSize": "14px",
                                                    "fontWeight": "600",
                                                    "color": "white",
                                                    "marginBottom": "16px",
                                                    "textAlign": "center"
                                                }),
                                                
                                                html.Div([
                                                    html.Div("Minimum:", style={
                                                        "color": "white",
                                                        "fontSize": "13px",
                                                        "fontWeight": "500",
                                                        "marginBottom": "8px"
                                                    }),
                                                    dcc.Input(
                                                        id="spa-opt-filter-min-input",
                                                        type="number",
                                                        placeholder="0.10",
                                                        style={
                                                            "width": "100%",
                                                            "padding": "10px",
                                                            "borderRadius": "8px",
                                                            "border": "none",
                                                            "fontSize": "14px",
                                                            "marginBottom": "16px"
                                                        }
                                                    ),
                                                    
                                                    html.Div("Maximum:", style={
                                                        "color": "white",
                                                        "fontSize": "13px",
                                                        "fontWeight": "500",
                                                        "marginBottom": "8px"
                                                    }),
                                                    dcc.Input(
                                                        id="spa-opt-filter-max-input",
                                                        type="number",
                                                        placeholder="Enter Value (e.g. 0.15)",
                                                        style={
                                                            "width": "100%",
                                                            "padding": "10px",
                                                            "borderRadius": "8px",
                                                            "border": "none",
                                                            "fontSize": "14px",
                                                            "marginBottom": "16px"
                                                        }
                                                    ),
                                                    
                                                    html.Div([
                                                        html.Button("Back", 
                                                                id="spa-opt-filter-back-btn",
                                                                style={
                                                                    "backgroundColor": "transparent",
                                                                    "border": "1px solid white",
                                                                    "color": "white",
                                                                    "borderRadius": "6px",
                                                                    "padding": "8px 16px",
                                                                    "fontSize": "12px",
                                                                    "marginRight": "8px",
                                                                    "cursor": "pointer"
                                                                }),
                                                        html.Button("Apply Filter", 
                                                                id="spa-opt-filter-apply-btn",
                                                                style={
                                                                    "backgroundColor": "white",
                                                                    "border": "none",
                                                                    "color": "#2AACFD",
                                                                    "borderRadius": "6px",
                                                                    "padding": "8px 16px",
                                                                    "fontSize": "12px",
                                                                    "fontWeight": "600",
                                                                    "cursor": "pointer"
                                                                })
                                                    ], style={"display": "flex", "justifyContent": "flex-end"})
                                                ])
                                            ], id="spa-opt-filter-step-2", style={"display": "none"})
                                            
                                        ], id="spa-opt-filter-dropdown-menu", className="filter-dropdown-menu", style={
                                            "display": "none",
                                            "position": "absolute",
                                            "top": "100%",
                                            "left": "0",
                                            "backgroundColor": "#2AACFD",
                                            "borderRadius": "12px",
                                            "padding": "16px",
                                            "minWidth": "280px",
                                            "maxWidth": "320px",
                                            "boxShadow": "0 8px 25px rgba(42, 172, 253, 0.4)",
                                            "zIndex": "1001",
                                            "marginTop": "8px",
                                            "border": "1px solid rgba(255,255,255,0.2)"
                                        }),
                                        
                                        dcc.Store(id="spa-opt-filter-dropdown-open", data=False),
                                        dcc.Store(id="spa-opt-filter-current-step", data=1),
                                        dcc.Store(id="spa-opt-filter-selected-param", data=None)
                                        
                                    ], style={"position": "relative", "display": "inline-block"})
                                ], width="auto"),
                                
                                dbc.Col(dbc.Input(
                                    id="spa-opt-table-search-input",
                                    placeholder="Search for instance, range etc.",
                                    size="sm",
                                    style={
                                        "borderRadius": "20px",
                                        "fontSize": "12px",
                                        "border": "1px solid #2AACFD",
                                        "height": "30px",
                                        "color": "#2AACFD"
                                    }
                                ), width=True, style={"minWidth": "220px"}),
                                
                                dbc.Col([
                                    html.Div([
                                        html.Button("««", 
                                                id="spa-opt-table-first-page-btn",
                                                className="pagination-btn first-page",
                                                style={
                                                    "background": "transparent",
                                                    "border": "none",
                                                    "color": "#2AACFD",
                                                    "fontFamily": "Poppins, sans-serif",
                                                    "fontSize": "14px",
                                                    "fontWeight": "600",
                                                    "height": "30px",
                                                    "minWidth": "30px",
                                                    "padding": "8px",
                                                    "margin": "0 1px",
                                                    "cursor": "pointer",
                                                    "display": "flex",
                                                    "alignItems": "center",
                                                    "justifyContent": "center"
                                                }),
                                        
                                        html.Button("‹", 
                                                id="spa-opt-table-prev-page-btn",
                                                className="pagination-btn previous-page",
                                                style={
                                                    "background": "transparent",
                                                    "border": "none",
                                                    "color": "#2AACFD",
                                                    "fontFamily": "Poppins, sans-serif",
                                                    "fontSize": "14px",
                                                    "fontWeight": "600",
                                                    "height": "30px",
                                                    "minWidth": "30px",
                                                    "padding": "8px",
                                                    "margin": "0 1px",
                                                    "cursor": "pointer",
                                                    "display": "flex",
                                                    "alignItems": "center",
                                                    "justifyContent": "center"
                                                }),
                                        
                                        html.Div([
                                            html.Span(id="spa-opt-table-current-page",
                                                    children="1",
                                                    style={
                                                        "fontFamily": "Poppins, sans-serif",
                                                        "fontSize": "14px",
                                                        "fontWeight": "600",
                                                        "color": "#2AACFD",
                                                        "padding": "6px 6px",
                                                        "border": "1.5px solid #2AACFD",
                                                        "borderRadius": "8px",
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "justifyContent": "center",
                                                        "height": "30px",
                                                        "boxSizing": "border-box",
                                                        "minWidth": "36px"
                                                    }),
                                            
                                            html.Span("/", 
                                                    style={
                                                        "fontFamily": "Poppins, sans-serif",
                                                        "fontSize": "14px",
                                                        "fontWeight": "600",
                                                        "color": "#2AACFD",
                                                        "padding": "0 8px",
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "justifyContent": "center",
                                                        "height": "30px"
                                                    }),
                                            
                                            html.Span(id="spa-opt-table-total-pages",
                                                    children="17",
                                                    style={
                                                        "fontFamily": "Poppins, sans-serif",
                                                        "fontSize": "14px",
                                                        "fontWeight": "600",
                                                        "color": "#2AACFD",
                                                        "display": "flex",
                                                        "alignItems": "center",
                                                        "justifyContent": "center",
                                                        "height": "30px",
                                                        "minWidth": "24px"
                                                    })
                                        ], style={
                                            "display": "flex",
                                            "alignItems": "center",
                                            "justifyContent": "center",
                                            "margin": "0 4px",
                                            "height": "36px"
                                        }),
                                        
                                        html.Button("›", 
                                                id="spa-opt-table-next-page-btn",
                                                className="pagination-btn next-page",
                                                style={
                                                    "background": "transparent",
                                                    "border": "none",
                                                    "color": "#2AACFD",
                                                    "fontFamily": "Poppins, sans-serif",
                                                    "fontSize": "14px",
                                                    "fontWeight": "600",
                                                    "height": "30px",
                                                    "minWidth": "30px",
                                                    "padding": "8px",
                                                    "margin": "0 1px",
                                                    "cursor": "pointer",
                                                    "display": "flex",
                                                    "alignItems": "center",
                                                    "justifyContent": "center"
                                                }),
                                        
                                        html.Button("»»", 
                                                id="spa-opt-table-last-page-btn",
                                                className="pagination-btn last-page",
                                                style={
                                                    "background": "transparent",
                                                    "border": "none",
                                                    "color": "#2AACFD",
                                                    "fontFamily": "Poppins, sans-serif",
                                                    "fontSize": "14px",
                                                    "fontWeight": "600",
                                                    "height": "30px",
                                                    "minWidth": "30px",
                                                    "padding": "8px",
                                                    "margin": "0 1px",
                                                    "cursor": "pointer",
                                                    "display": "flex",
                                                    "alignItems": "center",
                                                    "justifyContent": "center"
                                                })
                                    ], style={
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "flex-end",
                                        "gap": "0px",
                                        "height": "36px"
                                    })
                                ], width="auto", style={
                                    "minWidth": "200px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "flex-end",
                                    "height": "30px"
                                })
                            ], align="center", justify="end", className="g-2", style={
                                "display": "flex",
                                "alignItems": "center", 
                                "height": "30px",
                                "margin": "0"
                            })
                        ], width="auto")
                    ], align="center", justify="between", style={
                        "display": "flex",
                        "alignItems": "center",
                        "margin": "0"
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
                    dash_table.DataTable(
                        id="spa-opt-instance-table",
                        columns=[
                            {"name": "Instance Name", "id": "instance_name", "type": "text"},
                            {"name": "Transmittance (%)", "id": "transmittance", "type": "numeric"},
                            {"name": "SHGC", "id": "window_shgc", "type": "numeric"},
                            {"name": "Window-U (W/m²K)", "id": "window_u", "type": "numeric"},
                            {"name": "Roof-U (W/m²K)", "id": "roof_u", "type": "numeric"},
                            {"name": "Wall-U (W/m²K)", "id": "wall_u", "type": "numeric"},
                            {"name": "Ideal Cooling (kWh)", "id": "cooling_load", "type": "numeric"},
                            {"name": "Ideal Heating (kWh)", "id": "heating_load", "type": "numeric"}
                        ],
                        data=[],
                        page_size=10,
                        page_current=0,
                        filter_action="none",
                        page_action="none",
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
                        
                        style_data_conditional=[
                            {
                                'if': {
                                    'filter_query': '{instance_name} = Baseline'
                                },
                                'backgroundColor': '#E3F2FD',
                                'fontWeight': 'bold',
                                'color': '#2AACFD'
                            },
                            {
                                'if': {
                                    'column_id': 'instance_name',
                                    'filter_query': '{instance_name} != Baseline'
                                },
                                'fontWeight': '600',
                                'color': '#2AACFD',
                                'backgroundColor': '#F5F5F5'
                            },
                            {
                                'if': {'state': 'selected'},
                                'backgroundColor': '#E3F2FD',
                                'border': '1px solid #2AACFD'
                            },
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': '#EEEEEE'
                            },
                            {
                                'if': {'row_index': 'even'},
                                'backgroundColor': '#F5F5F5'
                            }
                        ],
                        
                        sort_action="custom",
                        row_selectable="multi",
                        selected_rows=[],
                        include_headers_on_copy_paste=False,
                        merge_duplicate_headers=True,
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
                                'rule': 'border-radius: 0; overflow: hidden; box-shadow: none; background-color: #F5F5F5; border: none;'
                            }
                        ]
                    ),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Div(id="spa-opt-table-info", style={
                                "fontSize": "12px",
                                "color": "#6C757D",
                                "padding": "8px 0"
                            })
                        ], width=True),
                        dbc.Col([
                            dbc.Button(
                                "Export Selected",
                                id="spa-opt-export-selected-btn",
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
                    "paddingLeft": "16px"
                })
            ], style=CARD_STYLE)
        ], width=12)
    ], className="mb-4"),

    # Stores for table functionality
    dcc.Store(id="spa-opt-table-selected-instances", data=[]),
    dcc.Store(id="spa-opt-table-filters", data={}),
    dcc.Download(id="spa-opt-download-instances"),

    create_enhanced_modal_spain_opt(),

], fluid=True, style={"backgroundColor": "#FFFFFF", "padding": "5px 20px"})

