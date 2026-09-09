# pages/explorer.py - Güncellenmiş versiyon başlangıcı
from dash import html, dcc, dash_table, register_page, callback
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dash_table.Format import Format, Scheme
import dash
from dash import html, dcc

# Page registration will be done in app.py after app creation


# ... geri kalan kodunuz


#dataset
df = pd.read_csv("data/LUX_2026_V6_Training.csv")

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
# Yeni sütun isimleri için labels güncelle
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

#last column for the color scale
color_col = df.columns[-1]

# Remove the first column (ID)
desired_columns = ['wall_u', 'window_u', 'window_shgc', 'roof_u', 
                  'transmittance', 'heating_load', 'cooling_load']
dimensions_to_plot = [col for col in desired_columns if col in df.columns]





# Özel renk paletinizi tanımlayın
custom_color_palette = ['#083D5E',  '#2AACFD', '#C8E9FE']

# Parallel coordinates plot'u güncelleyin
fig_parallel = px.parallel_coordinates(
    df,
    dimensions=dimensions_to_plot,
    color=df[color_col],
    labels=labels,
    color_continuous_scale=custom_color_palette,  # Özel renk paletiniz
)

# Alternatif olarak, daha detaylı kontrol için:
# Renkleri 0-1 arasında normalize edilmiş pozisyonlarla tanımlayabilirsiniz
custom_color_scale = [
    (0.0, '#083D5E'),
    (0.5, '#2AACFD'),  #
    (1.0, '#C8E9FE')    # En yüksek değer - en açık
]

fig_parallel = px.parallel_coordinates(
    df,
    dimensions=dimensions_to_plot,
    color=df[color_col],
    labels=labels,
    color_continuous_scale=custom_color_scale,
)


"""
fig_parallel = px.parallel_coordinates(
    df,
    dimensions=dimensions_to_plot,
    color=df[color_col],
    labels=labels,
    #color_continuous_scale=px.colors.diverging.Tealrose,
    color_continuous_scale=px.colors.sequential.ice,
)
"""
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

# explorer.py dosyasında create_scatter_figure fonksiyonunu şu şekilde güncelleyin:

# explorer.py dosyasında create_scatter_figure fonksiyonunu şu şekilde değiştirin:

def create_scatter_figure(option_key):
    option = scatter_options[option_key]
    x_col = option["x"]
    y_col = option["y"]
    
    # Ensure numeric columns.
    df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
    df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
    
    # ID sütunu için df_with_id kullan
    df_with_id = df.copy()
    df_with_id['ID'] = df_with_id.index + 1
    
    # Label sütunu ekle
    df_with_id['label'] = df_with_id['ID'].apply(lambda x: "Baseline" if x == 1 else f"S{x-1}")
    
    fig = px.scatter(
        df_with_id,
        x=x_col,
        y=y_col,
        hover_data={"ID": True, "label": False},  # label'ı hover_data'dan gizle
        custom_data=['label']  # label'ı custom_data olarak kullan
    )
    
    # Eksen başlıklarını ayarla
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
        # Düzeltilmiş hover template
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
        uirevision='scatter-plot'
    )
    return fig

# explorer.py dosyasındaki create_enhanced_modal fonksiyonunu bu kodla değiştirin:

# explorer.py dosyasındaki create_enhanced_modal fonksiyonunu bu kodla değiştirin:

def create_enhanced_modal():
    return html.Div([
        # Modal container
        html.Div(
            id="image-modal", 
            className="modal", 
            tabIndex=0, 
            style={"display": "none"},
            children=[
                html.Div([
                    # Close button
                    html.Button("×", id="modal-close", className="modal-close"),
                    
                    # Navigation container
                    html.Div([
                        # Left arrow
                        html.Button(
                            html.Div("❮", style={
                                "fontSize": "24px", 
                                "fontWeight": "bold",
                                "color": "#FFFFFF"
                            }), 
                            id="modal-prev", 
                            className="modal-nav-btn modal-prev"
                        ),
                        
                        # Image container - title yukarıda olacak
                        html.Div([
                            # Image title - ÖNCE TITLE
                            html.Div(
                                id="modal-title",
                                className="modal-title-text",
                                style={
                                    "textAlign": "center",
                                    "marginBottom": "15px",  # marginTop yerine marginBottom
                                    "fontSize": "18px",
                                    "fontWeight": "600",
                                    "color": "#2C3E50"
                                }
                            ),
                            # SONRA IMAGE
                            html.Img(
                                id="modal-image", 
                                className="modal-image",
                                style={"maxWidth": "80vw", "maxHeight": "70vh"}
                            )
                        ], className="modal-image-container"),
                        
                        # Right arrow
                        html.Button(
                            html.Div("❯", style={
                                "fontSize": "24px", 
                                "fontWeight": "bold",
                                "color": "#FFFFFF"
                            }), 
                            id="modal-next", 
                            className="modal-nav-btn modal-next"
                        )
                    ], className="modal-navigation")
                    
                ], className="modal-content-enhanced")
            ]
        ),
        
        # Store for current image index
        dcc.Store(id="current-image-index", data=0),
        
        # Hidden input for keyboard events
        dcc.Input(
            id="keyboard-listener",
            style={"position": "absolute", "left": "-9999px", "opacity": "0"},
            autoFocus=False
        )
    ])

initial_scatter_option = "Scatter 1"
fig_scatter = create_scatter_figure(initial_scatter_option)

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

# Add Filter Modal
filter_modal = dbc.Modal([
    dbc.ModalHeader(
        dbc.ModalTitle("Add Filter"),
        style={"backgroundColor": "#F8F9FA"}
    ),
    dbc.ModalBody(
        html.Div(id="filter-modal-body"),
        style={"padding": "20px"}
    ),
    dbc.ModalFooter([
        dbc.Button(
            "Cancel",
            id="add-filter-cancel",
            className="me-2",
            style={
                "backgroundColor": "transparent",
                "border": "1px solid #6C757D",
                "color": "#6C757D"
            }
        ),
        dbc.Button(
            "Add Filter",
            id="add-filter-confirm",
            style={
                "backgroundColor": "#2AACFD",
                "border": "none"
            }
        )
    ])
], id="add-filter-modal", size="md", is_open=False)

layout = dbc.Container([
    
    # Yeni Instance Comparison Bölümü
    dbc.Row([
        # Sol kart: Instance Seçimi
        dbc.Col([
            dbc.Card([
                # explorer.py dosyasında dbc.CardBody bölümünü şu şekilde düzelt:
                dbc.CardBody([
                    # UYARI ALANI KALDIRILDI - Artık üstte değil, dropdown'ın altında olacak
                    
                    # Virtual dropdown container
                    html.Div([
                        # Virtual dropdown trigger
                        html.Div(
                            id="virtual-dropdown-trigger",
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
                                "border": "none",
                            },
                            n_clicks=0
                        ),
                        
                        # Virtual dropdown menu - 8 ITEM İÇİN YÜKSEKLİK (320px)
                        html.Div(
                            id="virtual-scroll-container",
                            className="enhanced-dropdown-menu",
                            style={
                                "display": "none",
                                "position": "absolute",
                                "top": "100%",
                                "left": "0",
                                "right": "0",
                                "zIndex": "1000",
                                "height": "320px",        # 400px'den 360px'e düşürüldü (8 item)
                                "maxHeight": "320px",     # 400px'den 360px'e düşürüldü
                                "minHeight": "320px",     # 400px'den 360px'e düşürüldü
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
                        
                        # YENİ: UYARI OVERLAY - DROPDOWN'IN ALTINDA
                        html.Div(
                            id="warning-overlay",
                            className="warning-overlay",
                            style={
                                "display": "none",
                                "position": "absolute",
                                "top": "calc(100% + 8px)",  # Dropdown kapalıyken trigger'ın altında
                                "left": "0",
                                "right": "0",
                                "zIndex": "1001",  # Dropdown'dan daha üstte
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
                    
                    # Mevcut store'ların yanına ekleyin (comparison için ayrı)
                    dcc.Store(id="comparison-selected-instances-store", data=[]),
                    # Store'lar - Performance için optimize edildi
                    dcc.Store(id="selection-warning-state", data={"show": False, "message": ""}),
                    dcc.Store(id="virtual-scroll-position", data=0),
                    dcc.Store(id="virtual-item-height", data=40),
                    dcc.Store(id="virtual-container-height", data=320),  # 400'den 360'a güncellendi
                    dcc.Store(id="selected-instances-store", data=[]),
                    dcc.Store(id="dropdown-open-state", data=False),
                    
                    # Sort by ve Arama - Kompakt yerleşim (değişiklik yok)
                    dbc.Row([
                        dbc.Col(
                            html.Div([
                                dcc.Dropdown(
                                    id='sort-by-dropdown',
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
                            ], className="dropup"),  # Bu satırı ekleyin
                            width=7
                        ),
                        
                        # Hidden dummy outputs
                        html.Div(id="dummy-search-output", style={"display": "none"}),
                        html.Div(id="dummy-outside-click", style={"display": "none"}),
                        
                        dbc.Col(
                            dbc.Button(
                                "🔍",
                                id="search-toggle-button",
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

                    # Arama input alanı (değişiklik yok)
                    html.Div(
                        dbc.Input(
                            id="search-input",
                            type="number",
                            placeholder="Enter instance number (e.g., 33)...",
                            min=1,
                            max=4320,
                            style={
                                "marginBottom": "0px",
                                "fontSize": "14px",
                                "border": "2px solid #2AACFD",
                                "borderRadius": "10px"
                            }
                        ),
                        id="search-input-container",
                        className="search-input-container hidden"
                    ),

                    # Arama durumu store'u
                    dcc.Store(id="search-toggle-state", data=False),

                    # Sort Order (değişiklik yok)
                    html.Div([
                        html.Label("Sort Order:", style={
                            "fontFamily": "Poppins, sans-serif",
                            "fontWeight": "500",
                            "fontSize": "13px",
                            "marginBottom": "4px",
                            "color": "#4E5E66"
                        }),
                        dcc.RadioItems(
                            id='sort-order-radio',
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
                    
                    # Parametreler - İlk seçili instance için
                    html.Div(id='instance-parameters', style={"marginTop": "8px"})

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
        
        # Sağdaki "Instance Comparison" kartı
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardBody(
                        html.Div(id="instance-comparison-content"),
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
    
    # 2. SATIR: 3D Model ve Karşılaştırma Grafiği
    dbc.Row([
        # Sol Sütun: 3D Model
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(html.H5("3D Model", style={"fontWeight": "300", "fontSize": "20px"}), style=CARDHEADER_STYLE),
                dbc.CardBody(
                    html.Iframe(src="https://omurbugra.github.io/Graph3dv2",
                                style={"width": "100%", "height": "100%", "min-height": "400px", "border": "none"}),
                    id="model3d-card", style=CARDBODY_STYLE_NO_TOP_PADDING
                )
            ], style=CARD_STYLE, className="h-100"), # <--- ID BURAYA EKLENDİ
            width=4
        ),
        
        # Sağ Sütun: Comparison Graph
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Comparison Graph", style={"fontWeight": "300", "fontSize": "20px"}), style=CARDHEADER_STYLE),
                dbc.CardBody(
                    dcc.Graph(id='comparison-graph', style={"height": "100%", "min-height": "400px"}),
                    style=CARDBODY_STYLE_NO_TOP_PADDING
                )
            ], id="comparison-graph-card", style=CARD_STYLE, className="h-100")
        ], width=8)
    ], className="mb-4 align-items-stretch"),

    
    dbc.Row([
        # ── Parallel Coordinates Plot ──
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(html.H5("Parallel Coordinates Plot", style={"fontWeight": "300", "fontSize": "20px"}), style=CARDHEADER_STYLE),
                dbc.CardBody(
                    dcc.Graph(id="parallel-plot", figure=fig_parallel),
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
    
        # — Total Ideal Loads —
        dbc.Col(
            dbc.Card([
                # Güncellenmiş header - sol tarafta başlık, sağ tarafta buton
                dbc.CardHeader([
                    dbc.Row([
                        # Sol taraf: Başlık
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
                        
                        # Sağ taraf: Market Available Scenarios butonu
                        dbc.Col([
                            dbc.Button(
                                "Closest Market-Available Scenarios",
                                href="/market",
                                external_link=True,
                                style={
                                    "backgroundColor": "transparent",
                                    "border": "2px solid #2AACFD",
                                    "borderRadius": "8px",
                                    "color": "#2AACFD",
                                    "fontFamily": "Poppins, sans-serif",
                                    "fontWeight": "500",
                                    "fontSize": "12px",
                                    "padding": "6px 12px",
                                    "textDecoration": "none",
                                    "transition": "all 0.3s ease",
                                    "whiteSpace": "nowrap"
                                },
                                className="market-scenarios-btn"
                            )
                        ], width="auto", className="d-flex align-items-center justify-content-end")
                    ], align="center", justify="between", className="w-100")
                ], style=CARDHEADER_STYLE),
                
                dbc.CardBody(
                    dcc.Graph(id="scatter-plot", figure=fig_scatter),
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
    

    # Yöntem 2: CSS Grid kullanarak daha temiz bir yaklaşım
    html.Div([
        html.Div([
            html.Div([
                html.Div("Wall-U (W/m²K)", className="figure-label", style=CARDHEADER_STYLE),
                html.Img(
                    src="/assets/plot_wall_u.png",
                    className="figure-img",
                    id="plot-wall-u",
                    style={
                        "width": "90%",
                        "height": "auto",
                        "cursor": "pointer",
                        "borderRadius": "4px",
                        "marginTop": "25px",
                        "height": "160px"
                    }
                )
            ], className="figure-card", style=CARD_STYLE)
        ]),
        
        html.Div([
            html.Div([
                html.Div("Window-U (W/m²K)", className="figure-label", style=CARDHEADER_STYLE),
                html.Img(
                    src="/assets/plot_window_u.png",
                    className="figure-img",
                    id="plot-window-u",
                    style={
                        "width": "90%",
                        "height": "auto",
                        "cursor": "pointer",
                        "borderRadius": "4px",
                        "marginTop": "25px",
                        "height": "160px"
                    }
                )
            ], className="figure-card", style=CARD_STYLE)
        ]),
        
        html.Div([
            html.Div([
                html.Div("Window-SHGC", className="figure-label", style=CARDHEADER_STYLE),
                html.Img(
                    src="/assets/plot_window_shgc.png",
                    className="figure-img",
                    id="plot-window-shgc",
                    style={
                        "width": "90%",
                        "height": "auto",
                        "cursor": "pointer",
                        "borderRadius": "4px",
                        "marginTop": "25px",
                        "height": "160px"
                    }
                )
            ], className="figure-card", style=CARD_STYLE)
        ]),
        
        html.Div([
            html.Div([
                html.Div("Roof-U (W/m²K)", className="figure-label", style=CARDHEADER_STYLE),
                html.Img(
                    src="/assets/plot_roof_u.png",
                    className="figure-img",
                    id="plot-roof-u",
                    style={
                        "width": "90%",
                        "height": "auto",
                        "cursor": "pointer",
                        "borderRadius": "4px",
                        "marginTop": "25px",
                        "height": "160px"

                    }
                )
            ], className="figure-card", style=CARD_STYLE)
        ]),
        
        html.Div([
            html.Div([
                html.Div("Transmittance (%)", className="figure-label", style=CARDHEADER_STYLE),
                html.Img(
                    src="/assets/plot_transmittance.png",
                    className="figure-img",
                    id="plot-transmittance",
                    style={
                        "width": "90%",
                        "height": "auto",
                        "cursor": "pointer",
                        "borderRadius": "4px",
                        "marginTop": "25px",
                        "height": "160px"

                    }
                )
            ], className="figure-card", style=CARD_STYLE)
        ])
        
    ], id="figure-grid", style={
        "display": "grid",
        "gridTemplateColumns": "repeat(5, 1fr)",  # 5 eşit sütun
        "gap": "20px",
        "marginTop": "30px",
        "marginBottom": "2rem",
        "paddingLeft": "0px",
        "paddingRight": "0px"
    }),
    
    # explorer.py dosyasının sonuna, footer'dan önce bu satırı ekleyin:

    # YENİ: Instance Table Bölümü
    dbc.Row([
        dbc.Col([
            dbc.Card(id="instance-table-card", children=[
                # explorer.py'deki Instance Table header kısmını bu kodla değiştirin:

                # explorer.py dosyasındaki Instance Table header kısmını bu kodla değiştirin:

                # explorer.py dosyasındaki Instance Table header kısmını bu kodla değiştirin:

                dbc.CardHeader([
                    dbc.Row([
                        # Sol Taraf: Başlık + Filter Chips (inline)
                        dbc.Col([
                            html.Div([
                                # Instance Table başlığı
                                html.H5("Instance Table", style={
                                    "fontWeight": "300",
                                    "fontSize": "20px",
                                    "margin": "0",
                                    "color": "#7B7B7B",
                                    "display": "inline-block",
                                    "marginRight": "16px"
                                }),
                                
                                # Filter chips container - başlığın sağında
                                html.Div(id="filter-chips-container", children=[], style={
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

                        # Sağ Taraf: Butonlar, Arama ve Pagination
                        dbc.Col([
                            dbc.Row([
                                # ENHANCED Add Filter Button Container
                                dbc.Col([
                                    html.Div([
                                        # Add Filter Trigger Button
                                        html.Button(
                                            "Add Filter+",
                                            id="add-filter-trigger-btn",
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
                                        
                                        # Dropdown Menu Container
                                        html.Div([
                                            # Step 1: Parameter Selection
                                            html.Div([
                                                html.Div("Select Parameter:", style={
                                                    "fontSize": "14px",
                                                    "fontWeight": "600",
                                                    "color": "white",
                                                    "marginBottom": "12px",
                                                    "textAlign": "center"
                                                }),
                                                
                                                # Parameter List
                                                html.Div([
                                                    html.Div([
                                                        html.Span("Instance", style={"flex": "1"}),
                                                        html.Span("+", style={"fontSize": "18px", "fontWeight": "bold"})
                                                    ], className="filter-param-item", 
                                                    id={"type": "param-selector", "param": "instance_name"},
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
                                                    id={"type": "param-selector", "param": "transmittance"},
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
                                                    id={"type": "param-selector", "param": "window_shgc"},
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
                                                    id={"type": "param-selector", "param": "wall_u"},
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
                                                    id={"type": "param-selector", "param": "window_u"},
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
                                                    id={"type": "param-selector", "param": "roof_u"},
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
                                                    id={"type": "param-selector", "param": "heating_load"},
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
                                                    id={"type": "param-selector", "param": "cooling_load"},
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
                                            ], id="filter-step-1", style={"display": "block"}),
                                            
                                            # Step 2: Range Selection (Initially Hidden)
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
                                                        id="filter-min-input",
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
                                                        id="filter-max-input",
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
                                                    
                                                    # Action Buttons
                                                    html.Div([
                                                        html.Button("Back", 
                                                                id="filter-back-btn",
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
                                                                id="filter-apply-btn",
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
                                            ], id="filter-step-2", style={"display": "none"})
                                            
                                        ], id="filter-dropdown-menu", className="filter-dropdown-menu", style={
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
                                        
                                        # Stores
                                        dcc.Store(id="filter-dropdown-open", data=False),
                                        dcc.Store(id="filter-current-step", data=1),
                                        dcc.Store(id="filter-selected-param", data=None)
                                        
                                    ], style={"position": "relative", "display": "inline-block"})
                                ], width="auto"),
                                
                                # Search Input
                                dbc.Col(dbc.Input(
                                    id="table-search-input",
                                    placeholder="Search for instance, range etc.",
                                    size="sm",
                                    style={
                                        "borderRadius": "20px",
                                        "fontSize": "12px",
                                        "border": "1px solid #E0E0E0",
                                        "height": "30px",
                                        "color": "#2AACFD"
                                    }
                                ), width=True, style={"minWidth": "220px"}),
                                
                                # Pagination Container
                                dbc.Col([
                                    html.Div([
                                        # First Page Button
                                        html.Button("««", 
                                                id="table-first-page-btn",
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
                                        
                                        # Previous Page Button
                                        html.Button("‹", 
                                                id="table-prev-page-btn",
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
                                        
                                        # Current Page Display
                                        html.Div([
                                            html.Span(id="table-current-page",
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
                                            
                                            html.Span(id="table-total-pages",
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
                                        
                                        # Next Page Button
                                        html.Button("›", 
                                                id="table-next-page-btn",
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
                                        
                                        # Last Page Button
                                        html.Button("»»", 
                                                id="table-last-page-btn",
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
                    # Instance Table
                    dash_table.DataTable(
                        id="instance-table",
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
                        # Table genel stil
                        style_table={
                            'overflowX': 'auto',
                            'fontFamily': 'Poppins, sans-serif',
                            'backgroundColor': '#F5F5F5',
                            'borderRadius': '0',
                            'overflow': 'hidden',
                            'border': 'none',
                            'margin': '0',           # EKLENEN
                            'marginTop': '0',        # EKLENEN
                            'marginBottom': '0'      # EKLENEN
                        },
                        
                        # HEADER STİLİ - Temiz görünüm için
                        style_header={
                            'backgroundColor': '#E3E3E3',
                            'fontWeight': '600',
                            'fontSize': '13px',
                            'color': '#666666',
                            'textAlign': 'center',
                            'border': 'none',
                            'borderTop': 'none',
                            'borderBottom': 'none',  # Alt border kaldırıldı
                            'borderLeft': 'none', 
                            'borderRight': 'none',
                            'whiteSpace': 'normal',
                            'height': '40px',
                            'padding': '12px 8px',
                            'outline': 'none',
                            'boxShadow': 'none'  # Box shadow kaldırıldı
                        },
                        
                        # İlk ve son header için radius - ALT RADIUS YOK
                        style_header_conditional=[
                            {
                                'if': {'column_id': 'instance_name'},  # İlk sütun - sadece sol üst
                                'borderTopLeftRadius': '8px',
                                'backgroundColor': '#E3E3E3',
                                'border': 'none'
                            },
                            {
                                'if': {'column_id': 'heating_load'},  # Son sütun - sadece sağ üst  
                                'borderTopRightRadius': '8px', 
                                'backgroundColor': '#E3E3E3',
                                'border': 'none'
                            }
                        ],
                        
                        # Cell stilleri
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
                            'borderBottom': '1px solid #E6E6E6',  # Sadece data cell'lerde alt çizgi
                            'backgroundColor': '#F5F5F5',
                            'minWidth': '80px',
                            'maxWidth': '150px',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis'
                        },
                        
                        # Data conditional styling
                        # Data conditional styling - BASELINE VE INSTANCE NAME VURGUSU
                        style_data_conditional=[
                            # BASELINE ROW - TÜM HÜCRE İÇİN MAVİ ARKA PLAN
                            {
                                'if': {
                                    'filter_query': '{instance_name} = Baseline'
                                },
                                'backgroundColor': '#E3F2FD',
                                'fontWeight': 'bold',
                                'color': '#2AACFD'
                            },
                            # Instance name için özel mavi renk (baseline hariç)
                            {
                                'if': {
                                    'column_id': 'instance_name',
                                    'filter_query': '{instance_name} != Baseline'
                                },
                                'fontWeight': '600',
                                'color': '#2AACFD',
                                'backgroundColor': '#F5F5F5'
                            },
                            # Seçili satırlar (baseline olmayan)
                            {
                                'if': {
                                    'state': 'selected',
                                    'filter_query': '{instance_name} != Baseline'
                                },
                                'backgroundColor': '#E3F2FD',
                                'border': '1px solid #2AACFD'
                            },
                            # Zebra striping
                            {
                                'if': {
                                    'row_index': 'odd',
                                    'filter_query': '{instance_name} != Baseline'
                                },
                                'backgroundColor': '#EEEEEE'
                            },
                            {
                                'if': {
                                    'row_index': 'even', 
                                    'filter_query': '{instance_name} != Baseline'
                                },
                                'backgroundColor': '#F5F5F5'
                            }
                        ],
                        
                        sort_action="custom",
                        row_selectable="multi",
                        selected_rows=[],
                        include_headers_on_copy_paste=False,
                        merge_duplicate_headers=True,
                        # CSS override - EN GÜÇLÜ YÖNTEM
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
                                'rule': 'background-color: #E3E3E3 !important; cursor: default !important;'  # Hover efektini kaldır
                            },
                            {
                                'selector': '.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner thead',
                                'rule': 'border-bottom: none !important; box-shadow: none !important;'  # Header altındaki çizgiyi kaldır
                            },
                            {
                                'selector': '.dash-table-container',
                                'rule': 'border-radius: 0; overflow: hidden; box-shadow: none; background-color: #F5F5F5; border: none;'
                            }
                        ]
                    ),
                    
                    # Table Footer
                    dbc.Row([
                        dbc.Col([
                            html.Div(id="table-info", style={
                                "fontSize": "12px",
                                "color": "#6C757D",
                                "padding": "8px 0"
                            })
                        ], width=True),
                        dbc.Col([
                            dbc.Button(
                                "Export Selected",
                                id="export-selected-btn",
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
    dcc.Store(id="table-selected-instances", data=[]),
    dcc.Store(id="table-filters", data={}),
    dcc.Download(id="download-instances"),

    create_enhanced_modal(),


], fluid=True, style={"backgroundColor": "#FFFFFF", "padding": "5px 20px"})
