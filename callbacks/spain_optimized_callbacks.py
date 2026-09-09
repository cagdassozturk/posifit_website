from dash import callback, callback_context, Input, Output, State
import pandas as pd
from dash.exceptions import PreventUpdate
from dash import Input, Output, State, callback, clientside_callback
from dash.exceptions import PreventUpdate

# Import from spain_optimized page
from pages.spain_optimized import df, labels

# Modal data - Spain image paths
MODAL_IMAGES_SPAKIYE_OPT = [
    {
        "id": "spa-opt-plot-wall-u",
        "title": "Ideal Heating vs Ideal Cooling Load (Colored by Wall-U)",
        "thumbnail": "/assets/spain/plot_extWall_u.png",
        "fullsize": "/assets/spain/fullPlot_wall_u.png"
    },
    {
        "id": "spa-opt-plot-window-u", 
        "title": "Ideal Heating vs Ideal Cooling Load (Colored by Window-U)",
        "thumbnail": "/assets/spain/plot_window_u.png",
        "fullsize": "/assets/spain/fullPlot_window_u.png"
    },
    {
        "id": "spa-opt-plot-window-shgc",
        "title": "Ideal Heating vs Ideal Cooling Load (Colored by Window-SHGC)",
        "thumbnail": "/assets/spain/plot_shgc.png",
        "fullsize": "/assets/spain/fullPlot_shgc.png"
    },
    {
        "id": "spa-opt-plot-roof-u",
        "title": "Ideal Heating vs Ideal Cooling Load (Colored by Roof-U)",
        "thumbnail": "/assets/spain/plot_roof_u.png",
        "fullsize": "/assets/spain/fullPlot_roof_u.png"
    },
    {
        "id": "spa-opt-plot-transmittance",
        "title": "Ideal Heating vs Ideal Cooling Load (Colored by Transmittance)",
        "thumbnail": "/assets/spain/plot_transmittance.png",
        "fullsize": "/assets/spain/fullPlot_transmittance.png"
    }
]

@callback(
    [Output("spa-opt-parallel-plot", "figure"),
     Output("spa-opt-scatter-plot", "figure")],
    [Input("spa-opt-scatter-plot", "clickData"),
     Input("spa-opt-scatter-plot", "selectedData"),
     Input("spa-opt-parallel-plot", "restyleData")],
    [State("spa-opt-parallel-plot", "figure"),
     State("spa-opt-scatter-plot", "figure")],
    prevent_initial_call=True
)
def update_linked_graphs_spain_opt(scatter_click, scatter_selected, parallel_restyle, parallel_fig, scatter_fig):
    """Link scatter and parallel coordinates plots for Spain optimized"""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_prop = ctx.triggered[0]["prop_id"]
    selected_indices = []

    # Handle parallel coordinates filtering
    if "spa-opt-parallel-plot.restyleData" in triggered_prop:
        label_to_col = {v: k for k, v in labels.items()}
        dimensions = parallel_fig["data"][0]["dimensions"]
        selected_bool = pd.Series(True, index=df.index)
        
        for dim in dimensions:
            if "constraintrange" in dim and dim["constraintrange"]:
                orig_col = label_to_col.get(dim["label"])
                if orig_col is None:
                    continue
                cons = dim["constraintrange"]
                if isinstance(cons[0], list):
                    cons = cons[0]
                lower, upper = cons[0], cons[1]
                selected_bool &= df[orig_col].between(lower, upper)
        
        selected_indices = df.index[selected_bool].tolist()
        scatter_fig["data"][0]["selectedpoints"] = selected_indices
        return parallel_fig, scatter_fig

    # Handle scatter plot selection
    elif "spa-opt-scatter-plot.selectedData" in triggered_prop and scatter_selected and scatter_selected.get("points"):
        selected_indices = [pt["pointIndex"] for pt in scatter_selected.get("points")]
    
    elif "spa-opt-scatter-plot.clickData" in triggered_prop and scatter_click and scatter_click.get("points"):
        selected_indices = [scatter_click["points"][0]["pointIndex"]]

    scatter_fig["data"][0]["selectedpoints"] = selected_indices

    # Update parallel coordinates dimensions
    label_to_col = {v: k for k, v in labels.items()}
    dimensions = parallel_fig["data"][0]["dimensions"]
    for i, dim in enumerate(dimensions):
        if not selected_indices:
            dim["constraintrange"] = None
            continue
            
        orig_col = label_to_col.get(dim["label"])
        if orig_col is None:
            continue

        values = df.iloc[selected_indices][orig_col]
        if pd.api.types.is_numeric_dtype(df[orig_col]):
            numeric_values = pd.to_numeric(values, errors='coerce').dropna()
            if numeric_values.empty:
                dim["constraintrange"] = None
                continue
            
            min_val, max_val = numeric_values.min(), numeric_values.max()
            
            if min_val == max_val:
                if min_val == 0:
                    delta = 1e-7
                else:
                    delta = max(abs(min_val) * 0.0001, 1e-7)
                
                dim['constraintrange'] = [min_val - delta, max_val + delta]
            else:
                dim['constraintrange'] = [min_val, max_val]
        else:
            if not values.empty:
                dim["constraintrange"] = [values.iloc[0], values.iloc[0]]
            else:
                dim["constraintrange"] = None

    return parallel_fig, scatter_fig


@callback(
    [Output("spa-opt-image-modal", "style"),
     Output("spa-opt-modal-image", "src"),
     Output("spa-opt-modal-title", "children"),
     Output("spa-opt-current-image-index", "data"),
     Output("spa-opt-modal-prev", "disabled"),
     Output("spa-opt-modal-next", "disabled")],
    [Input("spa-opt-plot-wall-u", "n_clicks"),
     Input("spa-opt-plot-window-u", "n_clicks"),
     Input("spa-opt-plot-window-shgc", "n_clicks"),
     Input("spa-opt-plot-roof-u", "n_clicks"),
     Input("spa-opt-plot-transmittance", "n_clicks"),
     Input("spa-opt-modal-close", "n_clicks"),
     Input("spa-opt-modal-prev", "n_clicks"),
     Input("spa-opt-modal-next", "n_clicks")],
    [State("spa-opt-current-image-index", "data")],
    prevent_initial_call=True
)
def handle_modal_interactions_spain_opt(wall_clicks, window_u_clicks, shgc_clicks, roof_clicks, 
                            trans_clicks, close_clicks, prev_clicks, next_clicks, 
                            current_index):
    """Handle all modal interactions for Spain optimized"""
    
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    triggered_prop = ctx.triggered[0]["prop_id"]
    
    # Close modal
    if "spa-opt-modal-close" in triggered_prop:
        return {"display": "none"}, "", "", 0, False, False
    
    # Navigation - Previous
    if "spa-opt-modal-prev" in triggered_prop and prev_clicks:
        if current_index > 0:
            new_index = current_index - 1
            image_data = MODAL_IMAGES_SPAKIYE_OPT[new_index]
            prev_disabled = (new_index == 0)
            next_disabled = False
            return (
                {"display": "flex"}, 
                image_data["fullsize"], 
                image_data["title"],
                new_index,
                prev_disabled,
                next_disabled
            )
        else:
            raise PreventUpdate
    
    # Navigation - Next
    if "spa-opt-modal-next" in triggered_prop and next_clicks:
        if current_index < len(MODAL_IMAGES_SPAKIYE_OPT) - 1:
            new_index = current_index + 1
            image_data = MODAL_IMAGES_SPAKIYE_OPT[new_index]
            prev_disabled = False
            next_disabled = (new_index == len(MODAL_IMAGES_SPAKIYE_OPT) - 1)
            return (
                {"display": "flex"}, 
                image_data["fullsize"], 
                image_data["title"],
                new_index,
                prev_disabled,
                next_disabled
            )
        else:
            raise PreventUpdate
    
    # Open modal with specific image
    for i, image_data in enumerate(MODAL_IMAGES_SPAKIYE_OPT):
        if image_data["id"] in triggered_prop:
            prev_disabled = (i == 0)
            next_disabled = (i == len(MODAL_IMAGES_SPAKIYE_OPT) - 1)
            
            return (
                {"display": "flex"}, 
                image_data["fullsize"], 
                image_data["title"],
                i,
                prev_disabled,
                next_disabled
            )
    
    raise PreventUpdate


# Keyboard control for modal
clientside_callback(
    """
    function(modal_style) {
        if (modal_style && modal_style.display === 'flex') {
            if (window.spaOptModalKeyListener) {
                document.removeEventListener('keydown', window.spaOptModalKeyListener);
            }
            
            window.spaOptModalKeyListener = function(e) {
                const modal = document.getElementById('spa-opt-image-modal');
                if (modal && modal.style.display === 'flex') {
                    if (e.key === 'Escape') {
                        document.getElementById('spa-opt-modal-close').click();
                    } else if (e.key === 'ArrowLeft') {
                        document.getElementById('spa-opt-modal-prev').click();
                        e.preventDefault();
                    } else if (e.key === 'ArrowRight') {
                        document.getElementById('spa-opt-modal-next').click();
                        e.preventDefault();
                    }
                }
            };
            
            document.addEventListener('keydown', window.spaOptModalKeyListener);
            
            setTimeout(function() {
                const modal = document.getElementById('spa-opt-image-modal');
                if (modal) {
                    modal.focus();
                }
            }, 100);
        } else {
            if (window.spaOptModalKeyListener) {
                document.removeEventListener('keydown', window.spaOptModalKeyListener);
                window.spaOptModalKeyListener = null;
            }
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('spa-opt-keyboard-listener', 'value'),
    Input('spa-opt-image-modal', 'style'),
    prevent_initial_call=True
)

