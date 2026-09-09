from dash import callback, callback_context, Input, Output, State
import pandas as pd
from dash.exceptions import PreventUpdate
from dash import Input, Output, State, callback, clientside_callback
from dash.exceptions import PreventUpdate

# Import from hungary_explorer page
from pages.hungary_explorer import df, labels

# Modal data - Hungary image paths
MODAL_IMAGES_HUNKIYE = [
    {
        "id": "hun-plot-wall-u",
        "title": "Ideal Heating vs Ideal Cooling Load (Colored by Wall-U)",
        "thumbnail": "/assets/hungary/plot_extWall_u.png",
        "fullsize": "/assets/hungary/fullPlot_wall_u.png"
    },
    {
        "id": "hun-plot-window-u", 
        "title": "Ideal Heating vs Ideal Cooling Load (Colored by Window-U)",
        "thumbnail": "/assets/hungary/plot_window_u.png",
        "fullsize": "/assets/hungary/fullPlot_window_u.png"
    },
    {
        "id": "hun-plot-window-shgc",
        "title": "Ideal Heating vs Ideal Cooling Load (Colored by Window-SHGC)",
        "thumbnail": "/assets/hungary/plot_shgc.png",
        "fullsize": "/assets/hungary/fullPlot_shgc.png"
    },
    {
        "id": "hun-plot-roof-u",
        "title": "Ideal Heating vs Ideal Cooling Load (Colored by Roof-U)",
        "thumbnail": "/assets/hungary/plot_roof_u.png",
        "fullsize": "/assets/hungary/fullPlot_roof_u.png"
    },
    {
        "id": "hun-plot-transmittance",
        "title": "Ideal Heating vs Ideal Cooling Load (Colored by Transmittance)",
        "thumbnail": "/assets/hungary/plot_transmittance.png",
        "fullsize": "/assets/hungary/fullPlot_transmittance.png"
    }
]

@callback(
    [Output("hun-parallel-plot", "figure"),
     Output("hun-scatter-plot", "figure")],
    [Input("hun-scatter-plot", "clickData"),
     Input("hun-scatter-plot", "selectedData"),
     Input("hun-parallel-plot", "restyleData")],
    [State("hun-parallel-plot", "figure"),
     State("hun-scatter-plot", "figure")],
    prevent_initial_call=True
)
def update_linked_graphs_hungary(scatter_click, scatter_selected, parallel_restyle, parallel_fig, scatter_fig):
    """Link scatter and parallel coordinates plots for Hungary explorer"""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_prop = ctx.triggered[0]["prop_id"]
    selected_indices = []

    # Handle parallel coordinates filtering
    if "hun-parallel-plot.restyleData" in triggered_prop:
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
    elif "hun-scatter-plot.selectedData" in triggered_prop and scatter_selected and scatter_selected.get("points"):
        selected_indices = [pt["pointIndex"] for pt in scatter_selected.get("points")]
    
    elif "hun-scatter-plot.clickData" in triggered_prop and scatter_click and scatter_click.get("points"):
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
    [Output("hun-image-modal", "style"),
     Output("hun-modal-image", "src"),
     Output("hun-modal-title", "children"),
     Output("hun-current-image-index", "data"),
     Output("hun-modal-prev", "disabled"),
     Output("hun-modal-next", "disabled")],
    [Input("hun-plot-wall-u", "n_clicks"),
     Input("hun-plot-window-u", "n_clicks"),
     Input("hun-plot-window-shgc", "n_clicks"),
     Input("hun-plot-roof-u", "n_clicks"),
     Input("hun-plot-transmittance", "n_clicks"),
     Input("hun-modal-close", "n_clicks"),
     Input("hun-modal-prev", "n_clicks"),
     Input("hun-modal-next", "n_clicks")],
    [State("hun-current-image-index", "data")],
    prevent_initial_call=True
)
def handle_modal_interactions_hungary(wall_clicks, window_u_clicks, shgc_clicks, roof_clicks, 
                            trans_clicks, close_clicks, prev_clicks, next_clicks, 
                            current_index):
    """Handle all modal interactions for Hungary explorer"""
    
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    triggered_prop = ctx.triggered[0]["prop_id"]
    
    # Close modal
    if "hun-modal-close" in triggered_prop:
        return {"display": "none"}, "", "", 0, False, False
    
    # Navigation - Previous
    if "hun-modal-prev" in triggered_prop and prev_clicks:
        if current_index > 0:
            new_index = current_index - 1
            image_data = MODAL_IMAGES_HUNKIYE[new_index]
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
    if "hun-modal-next" in triggered_prop and next_clicks:
        if current_index < len(MODAL_IMAGES_HUNKIYE) - 1:
            new_index = current_index + 1
            image_data = MODAL_IMAGES_HUNKIYE[new_index]
            prev_disabled = False
            next_disabled = (new_index == len(MODAL_IMAGES_HUNKIYE) - 1)
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
    for i, image_data in enumerate(MODAL_IMAGES_HUNKIYE):
        if image_data["id"] in triggered_prop:
            prev_disabled = (i == 0)
            next_disabled = (i == len(MODAL_IMAGES_HUNKIYE) - 1)
            
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
            if (window.turModalKeyListener) {
                document.removeEventListener('keydown', window.turModalKeyListener);
            }
            
            window.turModalKeyListener = function(e) {
                const modal = document.getElementById('hun-image-modal');
                if (modal && modal.style.display === 'flex') {
                    if (e.key === 'Escape') {
                        document.getElementById('hun-modal-close').click();
                    } else if (e.key === 'ArrowLeft') {
                        document.getElementById('hun-modal-prev').click();
                        e.preventDefault();
                    } else if (e.key === 'ArrowRight') {
                        document.getElementById('hun-modal-next').click();
                        e.preventDefault();
                    }
                }
            };
            
            document.addEventListener('keydown', window.turModalKeyListener);
            
            setTimeout(function() {
                const modal = document.getElementById('hun-image-modal');
                if (modal) {
                    modal.focus();
                }
            }, 100);
        } else {
            if (window.turModalKeyListener) {
                document.removeEventListener('keydown', window.turModalKeyListener);
                window.turModalKeyListener = null;
            }
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('hun-keyboard-listener', 'value'),
    Input('hun-image-modal', 'style'),
    prevent_initial_call=True
)

