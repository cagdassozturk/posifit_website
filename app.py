# app.py - Güncellenmiş versiyon
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc
import os

def make_nav_link(label, href, extra_classes=""):
    letters = [ html.Span(ch, className="nav-letter") for ch in label ]
    return dbc.NavLink(
        html.Span(letters, className="nav-link-inner"),
        href=href,
        className=f"nav-link-styled {extra_classes}",
        active="exact"
    )

# TEK UYGULAMA TANMLAMA
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    use_pages=True,
    assets_folder='assets',
    suppress_callback_exceptions=True,
    prevent_initial_callbacks=True,
    url_base_pathname='/'  # Root'tan başlasın ki hem /dashboard hem de /pilot_lux_* çalışsın
)

NAVBAR_STYLE = {
    "backgroundColor": "#2AACFD",
    "boxShadow": "0 2px 4px rgba(0, 0, 0, 0.8)",
    "borderRadius": "0px",
    "padding": "15px 20px",
    "maxHeight": "72px"
}

# Header
header = dbc.Navbar(
    dbc.Container(
        dbc.Row([
            dbc.Col([
                dbc.Row([
                    dbc.Col(
                        html.Img(src="/header/logos/logo1.png", height="133px"),
                        width="auto"
                    ),
                    dbc.Col(
                        html.Div(
                            style={
                                "width": "2px",
                                "height": "60px",
                                "backgroundColor": "white",
                                "margin": "0 7px 0 -30px"
                            }
                        ),
                        width="auto"
                    ),
                ], align="center", className="g-0")
            ], width="auto"),
            
            dbc.Col(
                dbc.Nav(
                    [
                        dbc.NavLink("Ana Sayfa", href="/", className="nav-link-styled", active="exact"),
                        dbc.NavLink("About POSIFIT", href="/about", className="nav-link-styled", active="exact"),
                        dbc.NavLink("Pilots", href="/pilot_lux", className="nav-link-styled", active="exact"),
                        dbc.NavLink("Contributors", href="/contributors", className="nav-link-styled", active="exact"),
                        dbc.NavLink("Contact", href="/contact", className="nav-link-styled", active="exact"),
                    ],
                    className="d-flex align-items-center",
                    style={"gap": "10px", "marginLeft": "10px"}
                ),
                width="auto"
            )

        ], align="center", className="w-100", justify="between"),
        fluid=True
    ),
    style=NAVBAR_STYLE,
    color="#2AACFD",
    className="mb-2"
)

tabs_container = html.Div(
    dbc.Nav(
        [
            dbc.NavLink(
                "All Solutions",
                href="/pilot_lux_explorer",  # Burayı değiştirdik
                active="exact",
                className="grouped-nav-link",
                id="all-solutions-tab"
            ),
            dbc.NavLink(
                "Optimized",
                href="/pilot_lux_optimized",  # Burayı değiştirdik
                active="exact",
                className="grouped-nav-link",
                id="optimized-tab"
            ),
        ],
        pills=True,
        className="tabs-group"
    ),
    style={
        "overflowX": "auto",
        "whiteSpace": "nowrap",
        "marginTop": "10px",
        "padding": "0 20px"
    }
)

luxembourg_with_tabs = html.Div(
    dbc.Container(
        dbc.Row([
            dbc.Col(
                html.H1(
                    "LUXEMBOURG",
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
                        "outline": "none"
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
        "padding": "0px 0",
        "marginBottom": "10px"
    }
)

combined_header = html.Div(
    [header, luxembourg_with_tabs],
    style={"marginBottom": "20px"}
)

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

# Ana layout - Dash'ın built-in page system'ini kullan
app.layout = html.Div([
    combined_header,
    tour_system,
    loading_container,
    dash.page_container
])

# Import pages first (without registration)
from pages import explorer, optimized, market, market_optimized
from pages import turkiye_explorer, turkiye_optimized, turkiye_market, turkiye_market_optimized
from pages import hungary_explorer, hungary_optimized
from pages import spain_explorer, spain_optimized
from pages import netherlands_explorer, netherlands_optimized

# Now register the pages after app creation
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

# Import callbacks after app initialization
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

if __name__ == '__main__':
    app.run(debug=True)