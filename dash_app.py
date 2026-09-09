# dash_app.py - Updated with fixed spacing
# dash_app.py - UPDATED
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import os

# Production mode kontrolü
PRODUCTION = os.getenv('PRODUCTION', 'false').lower() == 'true'
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8051')

# Create separate Dash app for data pages only
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://renovation.posifit.eu/style.css"
    ],
    use_pages=True,
    assets_folder='assets',
    assets_url_path='/assets/',
    suppress_callback_exceptions=True,
    prevent_initial_callbacks=True,
    # KRITIK: URL prefix ekleyin
    requests_pathname_prefix='/pilot_lux_explorer/' if not PRODUCTION else '/',
    routes_pathname_prefix='/pilot_lux_explorer/' if not PRODUCTION else '/',
    # Production ayarları
    serve_locally=True
)

# Server'ı export edin
server = app.server

# Create your friend's navbar in Dash components
friend_navbar = html.Header([
    html.Div([
        html.Img(src="https://renovation.posifit.eu/header/logos/logo1.png", alt="Main Logo", className="logo1"),
        html.Div(className="separator"),
        html.Img(src="https://renovation.posifit.eu/header/logos/POSIFIT_logo-06.png", alt="Third Logo", className="logo3")
    ], className="navbar-left"),
    
    html.Nav([
        html.A("Home", href="https://renovation.posifit.eu/"),
        html.A("About POSIFIT", href="https://renovation.posifit.eu/about"),
        
        html.Div([
            html.A([
                "Pilots ",
                html.Img(src="https://renovation.posifit.eu/logo/dropdown.svg", alt="▼", className="arrow-icon")
            ], href="#", className="pilot-btn"),
            
            html.Div([
                html.Div([
                    html.A("Luxembourg", href="#"),
                    html.Div([
                        html.A("All results", href="/pilot_lux_explorer"),
                        html.A("Pilot details", href="https://renovation.posifit.eu/pilot_lux")
                    ], className="pilot-submenu")
                ], className="pilot-name"),
                
                html.Div([
                    html.A("Turkiye", href="#"),
                    html.Div([
                        html.A("All results", href="/pilot_tur_explorer"),
                        html.A("Pilot details", href="https://renovation.posifit.eu/pilot_tur")
                    ], className="pilot-submenu")
                ], className="pilot-name"),
                
                html.Div([
                    html.A("Hungary", href="#"),
                    html.Div([
                        html.A("All results", href="/pilot_hun_explorer"),
                        html.A("Pilot details", href="https://renovation.posifit.eu/pilot_hun")
                    ], className="pilot-submenu")
                ], className="pilot-name"),
                
                html.Div([
                    html.A("Spain", href="#"),
                    html.Div([
                        html.A("All results", href="/pilot_spa_explorer"),
                        html.A("Pilot details", href="https://renovation.posifit.eu/pilot_spa")
                    ], className="pilot-submenu")
                ], className="pilot-name"),
                
                html.Div([
                    html.A("Netherlands", href="#"),
                    html.Div([
                        html.A("All results", href="/pilot_net_explorer"),
                        html.A("Pilot details", href="https://renovation.posifit.eu/pilot_net")
                    ], className="pilot-submenu")
                ], className="pilot-name")
            ], className="dropdown-menu")
        ], className="nav-item dropdown"),
        
        html.A("Contributors", href="https://renovation.posifit.eu/contributors"),
        html.A("Contact", href="https://renovation.posifit.eu/contact")
    ], className="navbar-links")
], className="navbar")

# Luxembourg header with tabs and help button - DÜZELTILMIŞ BOŞLUKLAR
tabs_container = html.Div(
    dbc.Nav(
        [
            dbc.NavLink(
                "All Solutions",
                id="main-tab-all",
                href="/pilot_lux_explorer",
                active="exact",
                className="grouped-nav-link",
            ),
            dbc.NavLink(
                "Optimized",
                id="main-tab-opt",
                href="/pilot_lux_optimized",
                active="exact",
                className="grouped-nav-link",
            ),
        ],
        pills=True,
        className="tabs-group"
    ),
    style={
        "overflowX": "auto",
        "whiteSpace": "nowrap",
        "marginTop": "0px",
        "padding": "0 20px"
    }
)

luxembourg_with_tabs = html.Div(
    dbc.Container(
        dbc.Row([
            dbc.Col(
                html.H1(
                    id="main-title",
                    children="LUXEMBOURG",
                    style={
                        "fontFamily": "Silkscreen, monospace",
                        "fontWeight": "400",
                        "fontSize": "36px",
                        "lineHeight": "100%",
                        "letterSpacing": "0%",
                        "textAlign": "left",
                        "verticalAlign": "middle",
                        "color": "#2AACFD",
                        "margin": "0",
                        "textShadow": "2px 2px 4px rgba(0,0,0,0.3)"
                    }
                ),
                className="d-flex align-items-center",
                width="auto"
            ),
            dbc.Col(
                tabs_container,
                width="auto",
                className="d-flex align-items-center",
                style={"marginLeft": "20px"}
            ),
            dbc.Col(
                html.Button(
                    "Help",
                    id="help-button",
                    n_clicks=0,
                    style={
                        "backgroundColor": "#2AACFD",
                        "color": "white",
                        "border": "1px solid #2AACFD",
                        "borderRadius": "21px",
                        "padding": "12px 32px",
                        "fontSize": "12px",
                        "fontWeight": "400",
                        "fontFamily": "Poppins, sans-serif",
                        "cursor": "pointer",
                        "boxShadow": "0 4px 12px rgba(42, 172, 253, 0.3)",
                        "transition": "all 0.3s ease",
                        "minWidth": "100px",
                        "outline": "none",
                        "zIndex": "1000"
                    }
                ),
                className="d-flex align-items-center justify-content-end",
                width=True
            ),
        ], align="center", className="g-0", justify="between"),
        fluid=True,
        style={"padding": "0 80px"}
    ),
    style={
        "padding": "8px 0",        # 15px'den 8px'e düşürüldü
        "marginBottom": "5px",     # 10px'den 5px'e düşürüldü
        "backgroundColor": "#FFFFFF",
        "position": "relative",
        "zIndex": "999",
        "marginTop": "0px"
    }
)

# Tour system (from app.py)
tour_system = html.Div([
    html.Div([
        html.Div([
            html.H3(id="tour-title", children="Welcome to POSIFIT!"),
            html.P(id="tour-description", children="This guided tour will show you how to use all the features of the platform."),
            html.Div([
                html.Div([
                    html.Button("Previous", id="tour-prev", className="tour-btn tour-btn-prev"),
                    html.Button("Next", id="tour-next", className="tour-btn tour-btn-next"),
                ], className="tour-navigation"),
                html.Div([
                    html.Span(id="tour-step", children="1 / 5", className="tour-step-indicator"),
                    html.Button("✕", id="tour-close", className="tour-btn tour-btn-close"),
                ], style={"display": "flex", "alignItems": "center", "gap": "15px"})
            ], className="tour-controls")
        ], id="tour-tooltip", className="tour-tooltip")
    ], id="tour-overlay", className="tour-overlay"),
    
    dcc.Store(id="tour-active", data=False),
    dcc.Store(id="tour-current-step", data=0),
], id="tour-system")

# Loading container (from app.py)
loading_container = html.Div(
    id="loading-container",
    children=[
        dcc.Loading(
            id="loading",
            type="circle",
            children=html.Div(id="loading-output")
        )
    ],
    style={"display": "none"}
)

# Combined header - DÜZELTILMIŞ BOŞLUKLAR
combined_header = html.Div(
    [friend_navbar, luxembourg_with_tabs],
    style={"marginBottom": "10px", 
        "paddingLeft": "35px", 
        "paddingRight": "35px"}  # 20px'den 10px'e düşürüldü
)

# Footer component for dash_app.py

# Footer bileşeni - Düzeltilmiş boşluklar ve newsletter genişliği
dash_footer = html.Footer([
    # Top section: EU funding + logo
    html.Div([
        html.P([
            "This project has received funding from the European Union's Horizon Europe research and innovation programme under Grant Agreement No 101104058"
        ], style={
            "flex": "1 1 60%",
            "fontSize": "14px",
            "lineHeight": "1.5",
            "color": "white",
            "fontWeight": "normal",
            "margin": "0"
        }),
        html.Img(src="https://renovation.posifit.eu/logo/europe_footer.png", alt="EU Logo", style={
            "height": "75px",
            "width": "auto",
            "flexShrink": "0",
            "objectFit": "contain"
        })
    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "center",
        "padding": "40px 80px 20px 80px"  # Alt padding artırıldı
    }),

    # White line separator
    html.Hr(style={
        "height": "1px",
        "backgroundColor": "white",
        "opacity": "0.3",
        "border": "none",
        "margin": "0 80px 30px 80px"  # Yan margin eklendi, alt margin artırıldı
    }),

    # Main footer content - DÜZELTILMIŞ BOŞLUKLAR VE NEWSLETTER GENİŞLİĞİ
    html.Div([
        # Column 1: Reach us
        html.Div([
            html.H3("Reach us", style={
                "color": "white",
                "fontSize": "18px",
                "fontWeight": "600",
                "marginBottom": "20px",  # 16px'den 20px'e artırıldı
                "fontFamily": "Poppins, sans-serif"
            }),
            html.Div([
                html.Img(src="https://renovation.posifit.eu/logo/phone.svg", style={
                    "width": "16px",
                    "height": "16px",
                    "marginRight": "8px"
                }),
                "+90 312 210 2262"
            ], style={
                "display": "flex",
                "alignItems": "center",
                "color": "white",
                "fontSize": "14px",
                "marginBottom": "12px",  # 8px'den 12px'e artırıldı
                "fontFamily": "Poppins, sans-serif"
            }),
            html.Div([
                html.Img(src="https://renovation.posifit.eu/logo/mail.svg", style={
                    "width": "16px", 
                    "height": "16px",
                    "marginRight": "8px"
                }),
                html.Div([
                    "ipekg@metu.edu.tr",
                    html.Br(),
                    "ataberky@metu.edu.tr"
                ])
            ], style={
                "display": "flex",
                "alignItems": "flex-start",
                "color": "white",
                "fontSize": "14px",
                "marginBottom": "12px",  # 8px'den 12px'e artırıldı
                "fontFamily": "Poppins, sans-serif"
            }),
            html.Div([
                html.Img(src="https://renovation.posifit.eu/logo/pin.svg", style={
                    "width": "16px",
                    "height": "16px", 
                    "marginRight": "8px"
                }),
                html.Div([
                    "Orta Doğu Teknik Üniversitesi,",
                    html.Br(),
                    "Dumlupınar Blv. No: 1",
                    html.Br(),
                    "Ankara/ Turkiye"
                ])
            ], style={
                "display": "flex",
                "alignItems": "flex-start",
                "color": "white",
                "fontSize": "14px",
                "fontFamily": "Poppins, sans-serif"
            })
        ], style={
            "flex": "1",
            "marginRight": "40px"  # Sağ margin eklendi
        }),

        # Column 2: Navigation
        html.Div([
            html.H3("Navigation", style={
                "color": "white",
                "fontSize": "18px",
                "fontWeight": "600",
                "marginBottom": "20px",  # 16px'den 20px'e artırıldı
                "fontFamily": "Poppins, sans-serif"
            }),
            html.Ul([
                html.Li(html.A("Home", href="https://renovation.posifit.eu/", style={
                    "color": "white",
                    "textDecoration": "none",
                    "fontSize": "14px",
                    "fontFamily": "Poppins, sans-serif"
                }), style={"marginBottom": "8px"}),  # Li'lere margin eklendi
                html.Li(html.A("About POSIFIT", href="https://renovation.posifit.eu/about", style={
                    "color": "white",
                    "textDecoration": "none", 
                    "fontSize": "14px",
                    "fontFamily": "Poppins, sans-serif"
                }), style={"marginBottom": "8px"}),
                html.Li(html.A("Contributors", href="https://renovation.posifit.eu/contributors", style={
                    "color": "white",
                    "textDecoration": "none",
                    "fontSize": "14px", 
                    "fontFamily": "Poppins, sans-serif"
                }), style={"marginBottom": "8px"}),
                html.Li(html.A("Contact", href="https://renovation.posifit.eu/contact", style={
                    "color": "white",
                    "textDecoration": "none",
                    "fontSize": "14px",
                    "fontFamily": "Poppins, sans-serif"
                }), style={"marginBottom": "8px"})
            ], style={
                "listStyle": "none",
                "padding": "0",
                "margin": "0"
            })
        ], style={
            "flex": "1",
            "marginRight": "40px"  # Sağ margin eklendi
        }),

        # Column 3: Pilots  
        html.Div([
            html.H3("Pilots", style={
                "color": "white",
                "fontSize": "18px",
                "fontWeight": "600",
                "marginBottom": "20px",  # 16px'den 20px'e artırıldı
                "fontFamily": "Poppins, sans-serif"
            }),
            html.Ul([
                html.Li(html.A("Luxembourg", href="https://renovation.posifit.eu/pilot_lux", style={
                    "color": "white",
                    "textDecoration": "none",
                    "fontSize": "14px",
                    "fontFamily": "Poppins, sans-serif"
                }), style={"marginBottom": "8px"}),  # Li'lere margin eklendi
                html.Li(html.A("Turkiye", href="https://renovation.posifit.eu/pilot_tur", style={
                    "color": "white",
                    "textDecoration": "none",
                    "fontSize": "14px",
                    "fontFamily": "Poppins, sans-serif"
                }), style={"marginBottom": "8px"}),
                html.Li(html.A("Hungary", href="https://renovation.posifit.eu/pilot_hun", style={
                    "color": "white",
                    "textDecoration": "none",
                    "fontSize": "14px",
                    "fontFamily": "Poppins, sans-serif"
                }), style={"marginBottom": "8px"}),
                html.Li(html.A("Spain", href="https://renovation.posifit.eu/pilot_spa", style={
                    "color": "white",
                    "textDecoration": "none",
                    "fontSize": "14px",
                    "fontFamily": "Poppins, sans-serif"
                }), style={"marginBottom": "8px"}),
                html.Li(html.A("Netherlands", href="https://renovation.posifit.eu/pilot_net", style={
                    "color": "white",
                    "textDecoration": "none",
                    "fontSize": "14px",
                    "fontFamily": "Poppins, sans-serif"
                }), style={"marginBottom": "8px"})
            ], style={
                "listStyle": "none",
                "padding": "0",
                "margin": "0"
            })
        ], style={
            "flex": "1",
            "marginRight": "40px"  # Sağ margin eklendi
        }),

        # Column 4: Quick Links
        html.Div([
            html.H3("Quick Links", style={
                "color": "white",
                "fontSize": "18px",
                "fontWeight": "600",
                "marginBottom": "20px",  # 16px'den 20px'e artırıldı
                "fontFamily": "Poppins, sans-serif"
            }),
            html.Ul([
                html.Li(html.A("METU Urban Energy Transition and Sustainability Lab.", 
                              href="https://metu-urbanenergy.github.io/sustainability-lab./", style={
                    "color": "white",
                    "textDecoration": "none",
                    "fontSize": "14px",
                    "fontFamily": "Poppins, sans-serif"
                }), style={"marginBottom": "8px"})
            ], style={
                "listStyle": "none",
                "padding": "0",
                "margin": "0"
            })
        ], style={
            "flex": "1",
            "marginRight": "60px"  # Newsletter'dan önce daha büyük margin
        })
        
    ], style={
        "display": "flex",
        "alignItems": "flex-start",  # Üstten hizalama
        "gap": "0px",  # Gap kaldırıldı, margin'lerle kontrol ediliyor
        "padding": "0px 80px 40px 80px"
    }),

    # Bottom banner
    html.Div([
        html.Span("POSIFIT 2025", style={
            "color": "#2AACFD",
            "fontSize": "12px",
            "fontWeight": "500"
        }),
        html.Span("Designed by Ataberk Yılmaz, Ömür Buğra Gündüz | Developed by Çağdaş Öztürk, Ataberk Yılmaz", style={
            "color": "#2AACFD",
            "fontSize": "12px"
        })
    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "center",
        "padding": "12px 80px",
        "backgroundColor": "rgba(255,255,255,1)",
        "fontFamily": "Poppins, sans-serif"
    })
    
], style={
    "backgroundColor": "#2AACFD",
    "marginTop": "40px"
})

# Layout with Luxembourg header - WITH DASH CONTENT PADDING
# Layout with Luxembourg header and footer - GÜNCELLENMIŞ
app.layout = html.Div([
    dcc.Location(id="page-location"),
    combined_header,
    tour_system,
    loading_container,
    html.Div([
        dash.page_container
    ], className="dash-content-wrapper", style={
        "paddingLeft": "20px", 
        "paddingRight": "20px",
        "paddingTop": "20px",  # Navbar için üst boşluk
        "minHeight": "calc(100vh - 200px)"  # Footer için alan bırak
    }),
    dash_footer  # Footer'ı ekle
], id="main-dash-layout", style={
    "paddingTop": "72px"  # Fixed navbar için padding
})

# Import and register pages
from pages import explorer, optimized, market, market_optimized
from pages import turkiye_explorer, turkiye_optimized, turkiye_market, turkiye_market_optimized
from pages import hungary_explorer, hungary_optimized
from pages import spain_explorer, spain_optimized
from pages import netherlands_explorer, netherlands_optimized

# Register the pages
dash.register_page(
    "explorer",
    path='/pilot_lux_explorer',
    layout=explorer.layout,
    name='Luxembourg Explorer'
)

dash.register_page(
    "optimized", 
    path='/pilot_lux_optimized',
    layout=optimized.layout,
    name='Luxembourg Optimized'
)

dash.register_page(
    "turkiye_explorer",
    path='/pilot_tur_explorer',
    layout=turkiye_explorer.layout,
    name='Turkiye Explorer'
)

dash.register_page(
    "turkiye_optimized", 
    path='/pilot_tur_optimized',
    layout=turkiye_optimized.layout,
    name='Turkiye Optimized'
)

dash.register_page(
    "turkiye_market",
    path="/pilot_tur_market",
    layout=turkiye_market.layout,
    name="Turkiye Market Solutions (All)",
)

dash.register_page(
    "turkiye_market_optimized",
    path="/pilot_tur_market_optimized",
    layout=turkiye_market_optimized.layout,
    name="Turkiye Market Solutions (Optimized)",
)

dash.register_page(
    "hungary_explorer",
    path='/pilot_hun_explorer',
    layout=hungary_explorer.layout,
    name='Hungary Explorer'
)

dash.register_page(
    "hungary_optimized", 
    path='/pilot_hun_optimized',
    layout=hungary_optimized.layout,
    name='Hungary Optimized'
)

dash.register_page(
    "spain_explorer",
    path='/pilot_spa_explorer',
    layout=spain_explorer.layout,
    name='Spain Explorer'
)

dash.register_page(
    "spain_optimized", 
    path='/pilot_spa_optimized',
    layout=spain_optimized.layout,
    name='Spain Optimized'
)

dash.register_page(
    "netherlands_explorer",
    path='/pilot_net_explorer',
    layout=netherlands_explorer.layout,
    name='Netherlands Explorer'
)

dash.register_page(
    "netherlands_optimized", 
    path='/pilot_net_optimized',
    layout=netherlands_optimized.layout,
    name='Netherlands Optimized'
)

# Import callbacks
from callbacks import explorer_callbacks, optimized_callbacks
from callbacks import comparison_callbacks, optimized_comparison_callbacks
from callbacks import turkiye_explorer_callbacks, turkiye_optimized_callbacks
from callbacks import turkiye_comparison_callbacks, turkiye_optimized_comparison_callbacks
from callbacks import hungary_explorer_callbacks, hungary_optimized_callbacks
from callbacks import hungary_comparison_callbacks, hungary_optimized_comparison_callbacks
from callbacks import spain_explorer_callbacks, spain_optimized_callbacks
from callbacks import spain_comparison_callbacks, spain_optimized_comparison_callbacks
from callbacks import netherlands_explorer_callbacks, netherlands_optimized_callbacks
from callbacks import netherlands_comparison_callbacks, netherlands_optimized_comparison_callbacks
from callbacks import market_callbacks, market_optimized_callbacks
from callbacks import turkiye_market_callbacks, turkiye_market_optimized_callbacks

# Dynamic header for country-specific branding and links
@app.callback(
    [
        dash.Output("main-title", "children"),
        dash.Output("main-tab-all", "href"),
        dash.Output("main-tab-opt", "href"),
        dash.Output("main-tab-all", "active"),
        dash.Output("main-tab-opt", "active"),
    ],
    dash.Input("page-location", "pathname"),
)
def update_main_header(pathname):
    """Update header title and tab hrefs based on current pathname."""
    if pathname and pathname.startswith("/pilot_tur_"):
        return (
            "TURKIYE",
            "/pilot_tur_explorer",
            "/pilot_tur_optimized",
            pathname.startswith("/pilot_tur_explorer"),
            pathname.startswith("/pilot_tur_optimized"),
        )
    elif pathname and pathname.startswith("/pilot_hun_"):
        return (
            "HUNGARY",
            "/pilot_hun_explorer",
            "/pilot_hun_optimized",
            pathname.startswith("/pilot_hun_explorer"),
            pathname.startswith("/pilot_hun_optimized"),
        )
    elif pathname and pathname.startswith("/pilot_spa_"):
        return (
            "SPAIN",
            "/pilot_spa_explorer",
            "/pilot_spa_optimized",
            pathname.startswith("/pilot_spa_explorer"),
            pathname.startswith("/pilot_spa_optimized"),
        )
    elif pathname and pathname.startswith("/pilot_net_"):
        return (
            "NETHERLANDS",
            "/pilot_net_explorer",
            "/pilot_net_optimized",
            pathname.startswith("/pilot_net_explorer"),
            pathname.startswith("/pilot_net_optimized"),
        )
    # Default to Luxembourg
    return (
        "LUXEMBOURG",
        "/pilot_lux_explorer",
        "/pilot_lux_optimized",
        pathname.startswith("/pilot_lux_explorer") if pathname else False,
        pathname.startswith("/pilot_lux_optimized") if pathname else False,
    )

if __name__ == '__main__':
    app.run(debug=False, port=8051)
