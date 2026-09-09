import dash
import pandas as pd
from utils.spain_plots import load_all_data_spain
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate
import time
import threading
import re
from pages.spain_explorer import df
from dash import callback, Output, Input, ctx, html, dcc, State, clientside_callback, callback_context

# ==========================================
# PERFORMANCE OPTIMIZATIONS - SPAKIYE
# ==========================================

# Cache the data - separate cache for Spain
_cached_data_spain = None
_cached_df_with_id_spain = None

def get_cached_data_spain():
    """Load Spain data once and cache it"""
    global _cached_data_spain, _cached_df_with_id_spain
    if _cached_data_spain is None:
        _cached_data_spain = load_all_data_spain()
        _cached_df_with_id_spain = _cached_data_spain.copy()
        _cached_df_with_id_spain['ID'] = _cached_df_with_id_spain.index + 1
    return _cached_data_spain, _cached_df_with_id_spain

def get_selectable_data_spain():
    """Get data excluding baseline for user selection"""
    df, df_with_id = get_cached_data_spain()
    selectable_df = df_with_id[df_with_id.index > 0].copy()
    return selectable_df

# ==========================================
# CACHE DICTIONARIES - SPAKIYE
# ==========================================

_dropdown_cache_spain = {}
_param_cache_spain = {}
_comparison_cache_spain = {}
_graph_cache_spain = {}

def format_co2_value_spain(co2_value):
    """Format CO2 value"""
    try:
        if co2_value is None or co2_value == 0 or pd.isna(co2_value):
            return "N/A"
        else:
            return f"{co2_value:,.0f}"
    except:
        return "N/A"

# ==========================================
# VIRTUAL CONTENT UPDATE - SPAKIYE
# ==========================================

@callback(
    [Output('spa-virtual-scroll-container', 'children'),
     Output('spa-virtual-scroll-position', 'data')],
    [Input('spa-virtual-scroll-container', 'scrollTop'),
     Input('spa-comparison-selected-instances-store', 'data'),
     Input('spa-sort-by-dropdown', 'value'),
     Input('spa-sort-order-radio', 'value'),
     Input('spa-virtual-scroll-position', 'data')],
    [State('spa-virtual-item-height', 'data'),
     State('spa-virtual-container-height', 'data')],
    prevent_initial_call=False
)
def update_virtual_content_combined_spain(scroll_top_prop, selected_instances, sort_by, sort_order, scroll_position_data, item_height, container_height):
    """Virtual scrolling for Spain explorer"""
    
    try:
        scroll_top = scroll_position_data if scroll_position_data is not None else (scroll_top_prop if scroll_top_prop is not None else 0)
        
        if item_height is None:
            item_height = 40
        if container_height is None:
            container_height = 320
        
        df, df_with_id = get_cached_data_spain()
        selectable_df = get_selectable_data_spain()
        
        selected_set = set(selected_instances) if selected_instances else set()
        
        selected_key = "_".join(map(str, sorted(selected_set))) if selected_set else "none"
        scroll_group = int(scroll_top / (item_height * 5))
        cache_key = f"spa_{scroll_group}_{selected_key}_{sort_by}_{sort_order}"
        
        triggered_id = ctx.triggered_id
        
        if cache_key in _dropdown_cache_spain and triggered_id != 'spa-selected-instances-store':
            print(f"SPA CACHE HIT: Using cached content for scroll_group={scroll_group}")
            return _dropdown_cache_spain[cache_key], scroll_top
        
        # Sorting
        is_ascending = (sort_order == 'asc')
        if sort_by == 'ID':
            sorted_df = selectable_df.sort_values('ID', ascending=True)
        else:
            sorted_df = selectable_df.sort_values(by=sort_by, ascending=is_ascending)
        
        total_items = len(sorted_df)
        
        buffer = 20
        items_per_view = max(1, int(container_height / item_height))
        first_visible_index = max(0, int(scroll_top / item_height))
        
        visible_start = max(0, first_visible_index - buffer)
        visible_end = min(total_items, first_visible_index + items_per_view + buffer)
        
        min_items = items_per_view + (buffer * 2)
        if (visible_end - visible_start) < min_items:
            visible_end = min(total_items, visible_start + min_items)
        
        print(f"SPA VIRTUAL RENDER: Scroll={scroll_top}, Range={visible_start}-{visible_end}/{total_items}")
        
        visible_items = []
        
        # Top spacer
        if visible_start > 0:
            top_spacer_height = visible_start * item_height
            visible_items.append(
                html.Div(
                    style={
                        "height": f"{top_spacer_height}px",
                        "backgroundColor": "transparent",
                        "width": "100%",
                        "flexShrink": "0"
                    },
                    className="virtual-spacer-top"
                )
            )
        
        # Visible items
        items_rendered = 0
        for i in range(visible_start, visible_end):
            if i >= len(sorted_df):
                break
                
            row = sorted_df.iloc[i]
            instance_id = int(row['ID'])
            
            is_selected = instance_id in selected_set
            
            extra_info = ""
            if sort_by != 'ID' and sort_by in row:
                try:
                    extra_val = row.get(sort_by, 0)
                    if isinstance(extra_val, (int, float)):
                        extra_info = f" ({extra_val:.1f})"
                except:
                    pass
            
            checkbox_value = [instance_id] if is_selected else []
            unique_checkbox_id = f"spa-virtual-checkbox-{instance_id}-{scroll_group}"
            
            visible_items.append(
                html.Div([
                    html.Div(
                        f"S{instance_id - 1}{extra_info}",
                        className="option-label",
                        style={
                            "flex": "1",
                            "display": "flex",
                            "alignItems": "center",
                            "padding": "8px 12px",
                            "fontWeight": "600" if is_selected else "400",
                            "color": "#2AACFD" if is_selected else "#333"
                        }
                    ),
                    html.Div([
                        dcc.Checklist(
                            id={"type": "spa-virtual-checkbox", "index": instance_id, "unique": unique_checkbox_id},
                            options=[{"label": "", "value": instance_id}],
                            value=checkbox_value,
                            className="instance-checkbox",
                            style={"margin": "0"},
                            persistence=False,
                            persisted_props=[]
                        )
                    ], className="option-checkbox", style={
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "padding": "0 12px",
                        "height": "100%"
                    })
                ],
                id=f"spa-virtual-item-{instance_id}",
                className="virtual-dropdown-item selected" if is_selected else "virtual-dropdown-item",
                style={
                    "height": f"{item_height}px",
                    "minHeight": f"{item_height}px",
                    "maxHeight": f"{item_height}px",
                    "display": "flex",
                    "alignItems": "center",
                    "borderBottom": "1px solid #f0f0f0",
                    "backgroundColor": "#E3F2FD" if is_selected else "white",
                    "cursor": "pointer",
                    "width": "100%",
                    "flexShrink": "0",
                    "overflow": "hidden"
                }
                )
            )
            items_rendered += 1
        
        # Bottom spacer
        remaining_items = total_items - visible_end
        if remaining_items > 0:
            bottom_spacer_height = remaining_items * item_height
            visible_items.append(
                html.Div(
                    style={
                        "height": f"{bottom_spacer_height}px",
                        "backgroundColor": "transparent",
                        "width": "100%",
                        "flexShrink": "0"
                    },
                    className="virtual-spacer-bottom"
                )
            )
        
        if not visible_items:
            visible_items = [html.Div("No items found", style={
                "padding": "20px",
                "textAlign": "center",
                "color": "#666"
            })]
        
        print(f"SPA VIRTUAL: Successfully rendered {items_rendered} items")
        
        if len(_dropdown_cache_spain) > 50:
            old_keys = list(_dropdown_cache_spain.keys())[:25]
            for key in old_keys:
                del _dropdown_cache_spain[key]
            print("SPA Cache cleaned")
        
        _dropdown_cache_spain[cache_key] = visible_items
        
        return visible_items, scroll_top
        
    except Exception as e:
        print(f"SPA Virtual content error: {e}")
        import traceback
        traceback.print_exc()
        return [html.Div(f"Loading error: {str(e)}", style={"padding": "20px", "textAlign": "center", "color": "red"})], scroll_top or 0


# ==========================================
# WARNING OVERLAY - SPAKIYE
# ==========================================

@callback(
    [Output('spa-warning-overlay', 'children'),
     Output('spa-warning-overlay', 'style')],
    Input('spa-selection-warning-state', 'data'),
    [State('spa-dropdown-open-state', 'data')],
    prevent_initial_call=False
)
def update_warning_overlay_spain(warning_state, dropdown_is_open):
    """Warning overlay management for Spain"""
    
    if not warning_state or not warning_state.get('show', False):
        return [], {
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
        }
    
    warning_content = html.Div([
        html.Div([
            html.Span("⚠️", className="warning-icon", style={
                "fontSize": "18px",
                "marginRight": "8px",
                "color": "#DC3545",
                "animation": "pulse 1.5s ease-in-out infinite"
            }),
            html.Div([
                html.Div(
                    "Maximum 4 instances can be",
                    className="warning-text-line",
                    style={
                        "color": "#DC3545",
                        "fontWeight": "600",
                        "fontSize": "14px",
                        "lineHeight": "18px",
                        "margin": "0",
                        "padding": "0",
                        "fontFamily": "Poppins, sans-serif",
                        "whiteSpace": "nowrap"
                    }
                ),
                html.Div(
                    "selected for comparison",
                    className="warning-text-line",
                    style={
                        "color": "#DC3545",
                        "fontWeight": "600",
                        "fontSize": "14px",
                        "lineHeight": "18px",
                        "margin": "0",
                        "padding": "0",
                        "fontFamily": "Poppins, sans-serif",
                        "whiteSpace": "nowrap"
                    }
                )
            ], className="warning-text-container", style={
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "center",
                "alignItems": "flex-start"
            })
        ], className="warning-content", style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "gap": "8px",
            "width": "100%",
            "height": "100%"
        })
    ])
    
    if dropdown_is_open:
        top_position = "calc(100% + 320px + 12px)"
    else:
        top_position = "calc(100% + 8px)"
    
    visible_style = {
        "display": "flex",
        "position": "absolute",
        "top": top_position,
        "left": "0",
        "right": "0",
        "zIndex": "1001",
        "backgroundColor": "rgba(248, 249, 250, 0.98)",
        "backdropFilter": "blur(10px)",
        "webkitBackdropFilter": "blur(10px)",
        "border": "2px solid #DC3545",
        "borderRadius": "8px",
        "boxShadow": "0 8px 25px rgba(220, 53, 69, 0.4)",
        "padding": "12px 16px",
        "minHeight": "44px",
        "maxHeight": "80px",
        "alignItems": "center",
        "justifyContent": "center",
        "overflow": "hidden",
        "transition": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        "transform": "translateY(0)",
        "opacity": "1",
        "animation": "fadeInWarning 0.3s ease-out"
    }
    
    return warning_content, visible_style


@callback(
    Output('spa-warning-overlay', 'style', allow_duplicate=True),
    Input('spa-dropdown-open-state', 'data'),
    [State('spa-selection-warning-state', 'data'),
     State('spa-warning-overlay', 'style')],
    prevent_initial_call=True
)
def update_warning_position_on_dropdown_toggle_spain(dropdown_is_open, warning_state, current_style):
    """Update warning position when dropdown toggles"""
    
    if not warning_state or not warning_state.get('show', False):
        raise PreventUpdate
    
    if current_style is None:
        current_style = {}
    
    if dropdown_is_open:
        current_style["top"] = "calc(100% + 320px + 12px)"
    else:
        current_style["top"] = "calc(100% + 8px)"
    
    return current_style

# ==========================================
# SELECTION HANDLING - SPAKIYE
# ==========================================

@callback(
    [Output('spa-comparison-selected-instances-store', 'data'),
     Output('spa-selection-warning-state', 'data')],
    [Input({"type": "spa-virtual-checkbox", "index": dash.ALL, "unique": dash.ALL}, 'value'),
     Input('spa-search-input', 'n_submit')],
    [State({"type": "spa-virtual-checkbox", "index": dash.ALL, "unique": dash.ALL}, 'id'),
     State('spa-comparison-selected-instances-store', 'data'),
     State('spa-search-input', 'value')],
    prevent_initial_call=True
)
def handle_selection_and_search_with_warning_spain(all_values, n_submit, all_ids, current_selected, search_value):
    """Selection handling for Spain explorer"""
    
    if current_selected is None:
        current_selected = []
    
    triggered_id = ctx.triggered_id
    warning_state = {"show": False, "message": ""}
    
    # Handle search input
    if triggered_id == 'spa-search-input' and n_submit and search_value is not None:
        try:
            display_id = int(search_value)
            instance_id = display_id + 1
            
            if 1 <= display_id <= 5184:
                new_selected = current_selected.copy()
                if instance_id not in new_selected:
                    if len(new_selected) >= 4:
                        warning_state = {
                            "show": True,
                            "message": "⚠️ Maximum 4 instances can be selected for comparison"
                        }
                        return current_selected, warning_state
                    
                    new_selected.append(instance_id)
                    print(f"SPA SEARCH: Added S{display_id} (ID:{instance_id}), total: {len(new_selected)}")
                
                def delayed_cache_clear():
                    time.sleep(0.1)
                    global _dropdown_cache_spain
                    _dropdown_cache_spain.clear()
                    print("SPA SEARCH: Cache cleared")
                
                threading.Thread(target=delayed_cache_clear, daemon=True).start()
                
                return new_selected, warning_state
        except (ValueError, TypeError):
            pass
        return current_selected, warning_state
    
    # Handle checkbox selection
    if all_values and all_ids:
        try:
            triggered_info = ctx.triggered[0] if ctx.triggered else None
            if not triggered_info:
                raise PreventUpdate
                
            prop_id = triggered_info.get('prop_id', '')
            if 'spa-virtual-checkbox' not in prop_id:
                raise PreventUpdate
            
            match = re.search(r'"index":(\d+)', prop_id)
            if not match:
                raise PreventUpdate
                
            changed_instance_id = int(match.group(1))
            print(f"SPA SELECTION: Processing change for S{changed_instance_id}")
            
            is_now_checked = False
            for i, values in enumerate(all_values):
                if all_ids[i]["index"] == changed_instance_id:
                    is_now_checked = bool(values and len(values) > 0)
                    break
            
            new_selected = current_selected.copy()
            
            if is_now_checked and changed_instance_id not in new_selected:
                if len(new_selected) >= 4:
                    warning_state = {
                        "show": True,
                        "message": "⚠️ Maximum 4 instances can be selected for comparison"
                    }
                    return current_selected, warning_state
                
                new_selected.append(changed_instance_id)
                print(f"SPA SELECTION: Added S{changed_instance_id} (Total: {len(new_selected)})")
                    
            elif not is_now_checked and changed_instance_id in new_selected:
                new_selected.remove(changed_instance_id)
                print(f"SPA SELECTION: Removed S{changed_instance_id} (Total: {len(new_selected)})")
            
            if set(new_selected) != set(current_selected):
                print(f"SPA SELECTION: Updated from {current_selected} to {new_selected}")
                
                def delayed_cache_clear():
                    time.sleep(0.1)
                    global _dropdown_cache_spain
                    _dropdown_cache_spain.clear()
                    print("SPA SELECTION: Cache cleared")
                
                threading.Thread(target=delayed_cache_clear, daemon=True).start()
                
                return new_selected, warning_state
        
        except Exception as e:
            print(f"SPA Selection error: {e}")
            import traceback
            traceback.print_exc()
    
    return current_selected, warning_state


# ==========================================
# DROPDOWN STATE MANAGEMENT - SPAKIYE
# ==========================================

@callback(
    [Output('spa-virtual-scroll-container', 'style'),
     Output('spa-dropdown-open-state', 'data'),
     Output('spa-virtual-dropdown-trigger', 'children')],
    [Input('spa-virtual-dropdown-trigger', 'n_clicks'),
     Input('spa-comparison-selected-instances-store', 'data')],
    [State('spa-dropdown-open-state', 'data')],
    prevent_initial_call=True
)
def handle_dropdown_state_combined_spain(n_clicks, selected_instances, is_open):
    """Dropdown toggle for Spain explorer"""
    
    triggered_id = ctx.triggered_id
    
    if triggered_id == 'spa-virtual-dropdown-trigger' and n_clicks:
        new_state = not is_open if is_open is not None else True
        
        if new_state:
            style = {
                "display": "block",
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
                "boxSizing": "border-box"
            }
        else:
            style = {"display": "none"}
        
        if new_state:
            global _dropdown_cache_spain
            _dropdown_cache_spain.clear()
            print("SPA DROPDOWN: Opened, cleared cache")
        
        trigger_text = get_trigger_text_spain(selected_instances)
        return style, new_state, trigger_text
    
    if triggered_id == 'spa-selected-instances-store':
        current_style = {
            "display": "block" if is_open else "none",
            "height": "320px",
            "maxHeight": "320px",
            "minHeight": "320px"
        } if is_open else {"display": "none"}
        trigger_text = get_trigger_text_spain(selected_instances)
        return current_style, is_open, trigger_text
    
    raise PreventUpdate


def get_trigger_text_spain(selected_instances):
    """Display text for dropdown trigger"""
    if not selected_instances or len(selected_instances) == 0:
        return "Select instances..."
    
    display_ids = [instance_id - 1 for instance_id in selected_instances]
    
    if len(selected_instances) == 1:
        return f"S{display_ids[0]} selected"
    
    if len(selected_instances) == 2:
        return f"S{display_ids[0]} & S{display_ids[1]} selected"
    
    if len(selected_instances) == 3:
        return f"S{display_ids[0]}, S{display_ids[1]} & S{display_ids[2]} selected"
    
    if len(selected_instances) == 4:
        first_two = f"S{display_ids[0]} & S{display_ids[1]}"
        last_two = f"S{display_ids[2]} & S{display_ids[3]}"
        return f"{first_two}, {last_two} selected"
    
    return f"S{display_ids[0]}, S{display_ids[1]} & {len(selected_instances)-2} more selected"


# ==========================================
# SEARCH TOGGLE - SPAKIYE
# ==========================================

@callback(
    [Output('spa-search-input-container', 'className'),
     Output('spa-search-toggle-state', 'data'),
     Output('spa-search-input', 'value'),
     Output('spa-search-toggle-button', 'className')],
    [Input('spa-search-toggle-button', 'n_clicks'),
     Input('spa-search-input', 'n_submit')],
    [State('spa-search-toggle-state', 'data'),
     State('spa-search-input', 'value')],
    prevent_initial_call=True
)
def handle_search_toggle_combined_spain(toggle_clicks, submit_count, is_open, search_value):
    """Handle search visibility and button styling"""
    
    triggered_id = ctx.triggered_id
    
    if triggered_id == 'spa-search-toggle-button':
        current_state = is_open if is_open is not None else False
        new_state = not current_state
        
        container_class = "search-input-container" if new_state else "search-input-container hidden"
        button_class = "search-toggle-button search-open" if new_state else "search-toggle-button"
        
        return container_class, new_state, dash.no_update, button_class

    if triggered_id == 'spa-search-input' and search_value:
        return "search-input-container hidden", False, "", "search-toggle-button"
            
    raise PreventUpdate


# ==========================================
# PARAMETER UPDATE - SPAKIYE
# ==========================================

@callback(
    Output('spa-instance-parameters', 'children'),
    Input('spa-comparison-selected-instances-store', 'data'),
    prevent_initial_call=False
)
def update_instance_parameters_optimized_spain(selected_instances):
    """Parameter updates with caching for Spain"""
    
    df, _ = get_cached_data_spain()
    
    if not selected_instances or len(selected_instances) == 0:
        selected_id = 1
        baseline_mode = True
    else:
        selected_id = selected_instances[0]
        baseline_mode = False
    
    cache_key = f"spa_{selected_id}_baseline_{baseline_mode}"
    
    if cache_key in _param_cache_spain:
        return _param_cache_spain[cache_key]
    
    if selected_id > len(df):
        return "Invalid instance."
    
    row = df.iloc[selected_id - 1]

    def param_card(label, val, min_val, max_val, unit="", is_baseline=False, param_name=""):
        if is_baseline and param_name == "transmittance":
            value_text = "N/A"
            percent = 0
        else:
            value_text = f"{round(val, 3)}{unit}"
            percent = max(0, min(100, int((val - min_val) / (max_val - min_val) * 100)))
        
        return html.Div([
            html.Div([
                html.Div([
                    html.Div(label, className="parameter-name", style={
                        "fontSize": "12px", "fontWeight": "400", "color": "#333",
                        "marginBottom": "2px", "whiteSpace": "pre-line"
                    }),
                    html.Div(value_text, className="parameter-value-text", style={
                        "fontSize": "12px", "fontWeight": "600", 
                        "color": "#6C757D" if value_text == "N/A" else "#333",
                        "fontStyle": "italic" if value_text == "N/A" else "normal"
                    })
                ], style={"flex": "0 0 auto", "marginRight": "15px", "minWidth": "80px"}),
                
                html.Div([
                    html.Div(f"{min_val}", className="min-max-value", style={
                        "fontSize": "10px", "color": "#666", "marginRight": "6px",
                        "minWidth": "25px", "textAlign": "center"
                    }),
                    html.Div([
                        html.Div(className="progress-fill", style={'width': f'{percent}%'})
                    ], className="progress-bar-container", style={
                        "flex": "1", "height": "8px", "backgroundColor": "#e8ecef",
                        "borderRadius": "4px", "overflow": "hidden", "position": "relative",
                        "maxWidth": "120px"
                    }),
                    html.Div(f"{max_val}", className="min-max-value", style={
                        "fontSize": "10px", "color": "#666", "marginLeft": "6px",
                        "minWidth": "25px", "textAlign": "center"
                    })
                ], className="progress-bar-section", style={
                    "display": "flex", "alignItems": "center", "flex": "1", "maxWidth": "120px"
                })
            ], style={"display": "flex", "alignItems": "center", "width": "100%"})
        ], style={
            "backgroundColor": "#FFFFFF",
            "padding": "6px 14px",
            "marginBottom": "3.8px",
            "borderRadius": "8px",
            "border": "none"
        })

    if baseline_mode:
        title_text = f"Parameters for Baseline:"
        title_color = "#4E5E66"
    else:
        display_id = selected_id - 1
        title_text = f"Parameters for S{display_id}:"
        title_color = "#4E5E66"

    result = html.Div([
        html.Div(title_text, style={
            "fontSize": "13px", "fontWeight": "600", "color": title_color, "marginBottom": "8px"
        }),
        param_card("Wall-U", row["wall_u"], 0.1, 0.5, "", baseline_mode, "wall_u"),
        param_card("Roof-U", row["roof_u"], 0.1, 0.6, "", baseline_mode, "roof_u"),
        param_card("Window-U", row["window_u"], 0.3, 3, "", baseline_mode, "window_u"),
        param_card("Window-SHGC", row["window_shgc"], 0.1, 0.75, "", baseline_mode, "window_shgc"),
        param_card("Shutter\nTransmittance", row["transmittance"]*100, 20, 80, "%", baseline_mode, "transmittance")
    ])
    
    _param_cache_spain[cache_key] = result
    return result


# ==========================================
# COMPARISON UPDATE - SPAKIYE
# ==========================================

@callback(
    Output('spa-instance-comparison-content', 'children'),
    Input('spa-comparison-selected-instances-store', 'data'),
    prevent_initial_call=False
)
def update_instance_comparison_optimized_spain(selected_instances):
    """Instance comparison table for Spain"""
    df, _ = get_cached_data_spain()
    n = len(df)
    
    baseline_idx = 0
    baseline_row = df.iloc[baseline_idx]
    
    metrics = [
        ("Heating Ideal Load", "kWh", "heating_load", "heating.png", "heating-icon-bg"),
        ("Cooling Ideal Load", "kWh", "cooling_load", "cooling.png", "cooling-icon-bg"),
        ("Carbon Emission", "CO₂e/kWh", "co2", "co2.png", "co2-icon-bg"),
    ]

    def create_value_with_savings(main_value, baseline_value, metric_key):
        main_value_formatted = format_value(main_value, metric_key)
        try:
            if metric_key == "co2":
                if (baseline_value is None or baseline_value == 0 or pd.isna(baseline_value) or
                    main_value is None or main_value == 0 or pd.isna(main_value)):
                    savings_element = html.Span("N/A", className="metric-savings-value na-value")
                else:
                    raise ValueError
            
            difference = main_value - baseline_value
            if baseline_value == 0:
                pct_text = "N/A"
                color = "#6C757D"
                arrow = ""
            else:
                pct = (difference / baseline_value) * 100
                is_improvement = (difference < 0)
                color = "#28a745" if is_improvement else "#dc3545"
                arrow = "↓" if is_improvement else "↑"
                pct_text = f"{pct:+.2f}%"

            savings_element = html.Div([
                html.Span(pct_text, style={"color": color}),
                html.Span(f" {arrow}", style={"color": color})
            ], className="metric-savings-value")
        except (ValueError, TypeError, ZeroDivisionError):
             savings_element = html.Span("", className="metric-savings-value")

        return html.Div([
            html.Div(main_value_formatted, className="metric-main-value"),
            savings_element
        ], className="value-cell-container")

    def format_value(raw_val, metric_key=None):
        try:
            if metric_key == "co2":
                return format_co2_value_spain(raw_val)
            else:
                if pd.isna(raw_val):
                    return html.Span("N/A", className="na-value")
                return f"{raw_val:,.0f}"
        except:
            return html.Span("N/A", className="na-value") if metric_key == "co2" else str(raw_val)

    def create_instance_content_with_remove_btn(instance_label, instance_id):
        display_id = instance_id - 1
        return html.Div([
            html.Div([
                html.Div([
                    html.Div(instance_label, className="label-main-text"),
                    html.Div(f"S{display_id}", className="label-sub-text")
                ], style={"flex": "1", "display": "flex", "flexDirection": "column", "alignItems": "center", "justifyContent": "center"}),
                html.Button(
                    "×", 
                    id={"type": "spa-remove-instance-btn", "index": instance_id},
                    className="remove-instance-btn",
                    title=f"Remove S{display_id}"
                )
            ], style={"position": "relative", "width": "100%", "height": "100%", "display": "flex", "alignItems": "center", "justifyContent": "center"})
        ], className="blue-label-content")

    num_selected = len(selected_instances) if selected_instances else 0
    card_class = "instance-comparison-card"

    header_cells = [html.Div("", className="grid-cell grid-header")]
    for title, unit, _, image_file, icon_class in metrics:
        header_content = html.Div([
            html.Div(html.Img(src=f"/assets/{image_file}", className="metric-icon-image"), className=f"metric-icon-background {icon_class}"),
            html.Div([html.Div(title, className="metric-header-title"), html.Div(unit, className="metric-header-unit")], className="metric-header-text-container")
        ], className="metric-header-content")
        header_cells.append(html.Div(header_content, className="grid-cell grid-header value-cell"))

    baseline_cells = [html.Div(html.Div("Baseline", style={
        "backgroundColor": "#2AACFD",
        "color": "#FFFFFF", 
        "borderRadius": "16px",
        "padding": "20px 12px",
        "fontFamily": "Poppins, sans-serif",
        "fontWeight": "600",
        "fontSize": "16px",
        "textAlign": "center",
        "display": "flex",
        "width": "100%",
        "alignItems": "center",
        "justifyContent": "center"
    }), className="grid-cell label-cell")]
    for _, _, col_key, _, _ in metrics:
        baseline_cells.append(
            html.Div(format_value(baseline_row.get(col_key, 0), col_key), className="grid-cell value-cell baseline-value")
        )

    # No selection - baseline only
    if num_selected == 0:
        content_grid = html.Div(
            header_cells + baseline_cells,
            className="comparison-grid content-block-50"
        )
        return html.Div(content_grid, className=f"{card_class} comparison-layout-baseline-only", style={'height': '100%'})

    # 1 instance selected
    elif num_selected == 1:
        instance_id = selected_instances[0]
        sel_row = df.iloc[instance_id - 1]
        instance_cells = [html.Div(create_instance_content_with_remove_btn("Instance 1", instance_id), className="grid-cell label-cell")]
        for _, _, col_key, _, _ in metrics:
            main_val = sel_row.get(col_key, 0)
            baseline_val = baseline_row.get(col_key, 0)
            cell_content = create_value_with_savings(main_val, baseline_val, col_key)
            instance_cells.append(html.Div(cell_content, className="grid-cell value-cell chosen-value"))
        
        content_grid = html.Div(
            header_cells + baseline_cells + instance_cells,
            className="comparison-grid content-block-75"
        )
        return html.Div(content_grid, className=f"{card_class} comparison-layout-one-instance", style={'height': '100%'})
        
    # 2, 3 or 4 instances selected
    else:
        if num_selected == 2:
            grid_class = "comparison-grid"
        elif num_selected == 3:
            grid_class = "comparison-grid-4rows"
        else:
            grid_class = "comparison-grid-5rows"
            
        grid_cells = header_cells + baseline_cells
        
        for i, instance_id in enumerate(selected_instances):
            sel_row = df.iloc[instance_id - 1]
            instance_content_with_btn = create_instance_content_with_remove_btn(f"Instance {i+1}", instance_id)
            grid_cells.append(html.Div(instance_content_with_btn, className="grid-cell label-cell"))
            for _, _, col_key, _, _ in metrics:
                main_val = sel_row.get(col_key, 0)
                baseline_val = baseline_row.get(col_key, 0)
                cell_content = create_value_with_savings(main_val, baseline_val, col_key)
                grid_cells.append(html.Div(cell_content, className="grid-cell value-cell chosen-value"))
        
        return html.Div(html.Div(grid_cells, className=grid_class), className=card_class, style={'height': '100%'})


# ==========================================
# REMOVE BUTTON - SPAKIYE
# ==========================================

@callback(
    Output('spa-comparison-selected-instances-store', 'data', allow_duplicate=True),
    Input({"type": "spa-remove-instance-btn", "index": dash.ALL}, 'n_clicks'),
    State('spa-comparison-selected-instances-store', 'data'),
    prevent_initial_call=True
)
def handle_remove_instance_button_spain(n_clicks_list, current_selected):
    """Handle remove instance button clicks"""
    
    if not ctx.triggered or not current_selected:
        raise PreventUpdate
    
    triggered = ctx.triggered[0]
    
    if triggered['value'] is None:
        raise PreventUpdate
    
    prop_id = triggered['prop_id']
    import json
    try:
        button_info = json.loads(prop_id.split('.')[0])
        instance_id_to_remove = button_info['index']
        print(f"SPA REMOVE: Will remove S{instance_id_to_remove}")
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"SPA Error parsing button prop_id: {prop_id}, error: {e}")
        raise PreventUpdate
    
    new_selected = [inst_id for inst_id in current_selected if inst_id != instance_id_to_remove]
    
    print(f"SPA REMOVE BUTTON: Removed S{instance_id_to_remove}, new selection: {new_selected}")
    
    global _dropdown_cache_spain, _comparison_cache_spain, _graph_cache_spain
    _dropdown_cache_spain.clear()
    _comparison_cache_spain.clear()
    _graph_cache_spain.clear()
    
    return new_selected


# ==========================================
# SYNCHRONIZATION - SPAKIYE
# ==========================================

@callback(
    Output('spa-selected-instances-store', 'data', allow_duplicate=True),
    Input('spa-comparison-selected-instances-store', 'data'),
    prevent_initial_call=True
)
def sync_comparison_to_main_store_spain(comparison_selected):
    """Sync comparison store to main store"""
    return comparison_selected


# ==========================================
# GRAPH UPDATE - SPAKIYE
# ==========================================

@callback(
    Output('spa-comparison-graph', 'figure'),
    Input('spa-comparison-selected-instances-store', 'data'),
    prevent_initial_call=False
)
def update_comparison_graph_optimized_spain(selected_instances):
    """Graph updates for Spain explorer"""
    
    df, _ = get_cached_data_spain()
    baseline_row = df.iloc[0]
    
    features = ['transmittance', 'window_shgc', 'window_u', 'roof_u', 'wall_u']
    
    feature_labels = {
        'transmittance': 'Transmittance (%)',
        'window_shgc': 'SHGC',
        'window_u': 'Window-U (W/m²K)',
        'roof_u': 'Roof-U (W/m²K)',
        'wall_u': 'Wall-U (W/m²K)'
    }
    
    display_features = [feature_labels.get(f, f) for f in features]

    def transform_value(val, feature):
        return val

    baseline_vals = [transform_value(baseline_row[f], f) for f in features]
    
    # No selection - baseline only
    if not selected_instances or len(selected_instances) == 0:
        fig = go.Figure(data=[
            go.Bar(
                x=display_features,
                y=baseline_vals,
                name='Baseline',
                marker_color='#011928',
                textposition='outside',
                marker=dict(cornerradius=5),
                hovertemplate='<b>%{x}</b><br>Value: %{y:.3f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            barmode='group',
            template='plotly_white',
            xaxis_title=None,
            yaxis_title="Value",
            font=dict(family="Poppins, sans-serif", size=12, color="#4E5E66"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=11),
                itemwidth=30
            ),
            yaxis=dict(showgrid=True, gridcolor='#E8E8E8', gridwidth=1, zeroline=True, zerolinecolor='#E0E0E0'),
            xaxis=dict(tickfont=dict(size=11)),
            margin=dict(t=80, b=20, l=40, r=20),
            bargap=0.6
        )
        
        return fig

    # Create cache key
    cache_key = "spa_" + "_".join(map(str, sorted(selected_instances)))
    
    if cache_key in _graph_cache_spain:
        return _graph_cache_spain[cache_key]

    traces = []
    
    colors = ['#083D5E', '#107ABC', '#2AACFD', '#86D0FE']
    
    # Baseline trace
    traces.append(go.Bar(
        x=display_features,
        y=baseline_vals,
        name='Baseline',
        marker_color='#011928',
        textposition='outside',
        marker=dict(cornerradius=5),
        hovertemplate='<b>%{x}</b><br>Value: %{y:.3f}<extra></extra>'
    ))
    
    # Selected instances traces
    for i, instance_id in enumerate(selected_instances[:4]):
        selected_row = df.iloc[instance_id - 1]
        selected_vals = [transform_value(selected_row[f], f) for f in features]
        display_id = instance_id - 1
        traces.append(go.Bar(
            x=display_features,
            y=selected_vals,
            name=f'S{display_id}',
            marker_color=colors[i % len(colors)],
            textposition='outside',
            marker=dict(cornerradius=5),
            hovertemplate='<b>%{x}</b><br>Value: %{y:.3f}<extra></extra>'
        ))
    
    bargap = 0.2 + (len(selected_instances) * 0.02)
    bargroupgap = 0.1 + (len(selected_instances) * 0.008)

    fig = go.Figure(data=traces)
    fig.update_layout(
        barmode='group',
        template='plotly_white',
        xaxis_title=None,
        yaxis_title="Value",
        font=dict(family="Poppins, sans-serif", size=12, color="#4E5E66"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
            itemwidth=30
        ),
        yaxis=dict(showgrid=True, gridcolor='#E8E8E8', gridwidth=1, zeroline=True, zerolinecolor='#E0E0E0'),
        xaxis=dict(tickfont=dict(size=11)),
        margin=dict(t=80, b=20, l=40, r=20),
        bargap=bargap,
        bargroupgap=bargroupgap
    )
    
    _graph_cache_spain[cache_key] = fig
    return fig


# ==========================================
# CLIENTSIDE CALLBACKS - SPAKIYE
# ==========================================

# Scroll handler
clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            setTimeout(function() {
                const container = document.getElementById('spa-virtual-scroll-container');
                
                if (container && !container.hasScrollListener) {
                    let scrollTimeout;
                    let lastScrollTop = 0;
                    
                    console.log('SPA: Setting up scroll listener...');
                    
                    container.addEventListener('scroll', function(e) {
                        const scrollTop = e.target.scrollTop;
                        
                        if (scrollTimeout) {
                            clearTimeout(scrollTimeout);
                        }
                        
                        scrollTimeout = setTimeout(function() {
                            if (Math.abs(scrollTop - lastScrollTop) > 3) {
                                lastScrollTop = scrollTop;
                                
                                if (window.dash_clientside && window.dash_clientside.set_props) {
                                    try {
                                        window.dash_clientside.set_props('spa-virtual-scroll-position', {
                                            data: scrollTop
                                        });
                                        console.log(`SPA SCROLL UPDATE: ${scrollTop}`);
                                    } catch (error) {
                                        console.error('SPA scroll error:', error);
                                    }
                                }
                            }
                        }, 30);
                        
                    }, { passive: true });
                    
                    container.hasScrollListener = true;
                    console.log('SPA scroll listener attached');
                }
            }, 100);
        }
        return n_clicks;
    }
    """,
    Output('spa-virtual-scroll-container', 'data-scroll-initialized'),
    Input('spa-virtual-dropdown-trigger', 'n_clicks'),
    prevent_initial_call=True
)

# Outside click handler
clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0 && !window.turOutsideClickAttached) {
            setTimeout(function() {
                document.addEventListener('click', function(e) {
                    const dropdown = document.getElementById('spa-virtual-dropdown-trigger');
                    const menu = document.getElementById('spa-virtual-scroll-container');
                    const warning = document.getElementById('spa-warning-overlay');
                    
                    if (dropdown && menu && 
                        !dropdown.contains(e.target) && 
                        !menu.contains(e.target) &&
                        (!warning || !warning.contains(e.target))) {
                        
                        if (menu.style.display === 'block') {
                            menu.style.display = 'none';
                            if (window.dash_clientside && window.dash_clientside.set_props) {
                                window.dash_clientside.set_props('spa-dropdown-open-state', {data: false});
                            }
                        }
                    }
                }, { passive: true });
                
                window.turOutsideClickAttached = true;
            }, 50);
        }
        return 'attached';
    }
    """,
    Output('spa-dummy-outside-click', 'children'),
    Input('spa-virtual-dropdown-trigger', 'n_clicks'),
    prevent_initial_call=True
)

@callback(
    [Output('spa-virtual-item-height', 'data'),
     Output('spa-virtual-container-height', 'data')],
    Input('spa-virtual-dropdown-trigger', 'n_clicks'),
    prevent_initial_call=False
)
def validate_virtual_dimensions_spain(n_clicks):
    """Validate virtual scrolling dimensions"""
    return 40, 320


@callback(
    Output('spa-virtual-scroll-container', 'data-total-items'),
    Input('spa-sort-by-dropdown', 'value'),
    prevent_initial_call=False
)
def validate_total_items_spain(sort_by):
    """Validate total number of items"""
    selectable_df = get_selectable_data_spain()
    total_items = len(selectable_df)
    print(f"SPA VIRTUAL VALIDATION: Total selectable items: {total_items}")
    return total_items


# ==========================================
# TABLE CALLBACKS - SPAKIYE
# ==========================================

@callback(
    [Output("spa-instance-table", "data"),
     Output("spa-table-info", "children"),
     Output("spa-instance-table", "selected_rows")],
    [Input("spa-instance-table", "page_current"),
     Input("spa-table-search-input", "value"),
     Input("spa-table-filters", "data"),
     Input('spa-scatter-plot', 'selectedData'),
     Input('spa-selected-instances-store', 'data'),
     Input('spa-instance-table', 'sort_by')],
    prevent_initial_call=False
)
def update_table_data_spain(page_current, search_value, filters, selectedData, selected_instances, sort_by):
    """Table data update for Spain"""
    
    try:
        df, df_with_id = get_cached_data_spain()
        
        baseline_df = df.iloc[[0]].copy()
        baseline_df['instance_name'] = 'Baseline'
        baseline_df['instance_id'] = 1
        
        selected_ids = set()
        
        # Scatter plot selections
        if selectedData and 'points' in selectedData:
            for point in selectedData['points']:
                instance_id = None
                
                if 'pointIndex' in point:
                    try:
                        point_index = point['pointIndex']
                        instance_id = point_index + 1
                    except (ValueError, TypeError):
                        pass
                
                if 'customdata' in point and point['customdata'] and instance_id is None:
                    try:
                        if isinstance(point['customdata'], list):
                            label = point['customdata'][0]
                            if label == "Baseline":
                                instance_id = 1
                            elif label.startswith("S"):
                                instance_id = int(label[1:]) + 1
                    except (ValueError, IndexError, TypeError):
                        pass
                
                if instance_id:
                    selected_ids.add(instance_id)
        
        # Dropdown selections
        if selected_instances:
            selected_ids.update(selected_instances)
        
        if selected_ids:
            non_baseline_selected = [id for id in selected_ids if id > 1]
            if non_baseline_selected:
                remaining_df = df.iloc[1:].copy()
                remaining_df['instance_name'] = 'S' + remaining_df.index.astype(str)
                remaining_df['instance_id'] = remaining_df.index + 1
                
                mask = remaining_df['instance_id'].isin(non_baseline_selected)
                selected_df = remaining_df[mask]
                
                table_df = pd.concat([baseline_df, selected_df]).reset_index(drop=True)
            else:
                table_df = baseline_df.reset_index(drop=True)
        else:
            table_df = baseline_df.reset_index(drop=True)

        required_columns = [
            'instance_name', 'transmittance', 'window_shgc', 
            'window_u', 'roof_u', 'wall_u', 'cooling_load', 'heating_load', 'instance_id'
        ]
        
        for col in required_columns:
            if col not in table_df.columns and col != 'instance_name' and col != 'instance_id':
                table_df[col] = 0.0
        
        available_columns = [col for col in required_columns if col in table_df.columns]
        table_df = table_df[available_columns]
        
        # Search filtering
        if search_value:
            try:
                search_num = int(search_value)
                if search_num == 0:
                    search_name = 'Baseline'
                else:
                    search_name = f'S{search_num}'
                table_df = table_df[table_df['instance_name'].str.contains(search_name, case=False, na=False)]
            except (ValueError, TypeError):
                search_str = str(search_value).lower()
                mask = table_df.astype(str).apply(lambda x: x.str.lower().str.contains(search_str, na=False)).any(axis=1)
                table_df = table_df[mask]

        # Filter application
        if filters:
            if isinstance(filters, dict):
                for column, filter_value in filters.items():
                    if column == 'instance_name':
                        if isinstance(filter_value, dict) and filter_value.get('type') == 'instance_range':
                            min_instance = filter_value.get('min', 1)
                            max_instance = filter_value.get('max', 9999)
                            
                            def extract_instance_num(name):
                                if name == 'Baseline':
                                    return 0
                                elif name.startswith('S'):
                                    try:
                                        return int(name[1:])
                                    except:
                                        return 9999
                                return 9999
                            
                            table_df['temp_instance_num'] = table_df['instance_name'].apply(extract_instance_num)
                            table_df = table_df[
                                (table_df['temp_instance_num'] >= min_instance) & 
                                (table_df['temp_instance_num'] <= max_instance)
                            ]
                            table_df = table_df.drop('temp_instance_num', axis=1)
                            
                    elif column in table_df.columns:
                        if isinstance(filter_value, list) and len(filter_value) == 2:
                            min_val, max_val = filter_value
                            table_df = table_df[
                                (table_df[column] >= min_val) & 
                                (table_df[column] <= max_val)
                            ]

        # Sorting
        if sort_by and len(sort_by) > 0:
            sort_column = sort_by[0]['column_id']
            sort_direction = sort_by[0]['direction']
            
            if sort_column in table_df.columns:
                ascending = (sort_direction == 'asc')
                
                baseline_rows = table_df[table_df['instance_name'] == 'Baseline']
                other_rows = table_df[table_df['instance_name'] != 'Baseline']
                
                if not other_rows.empty:
                    if sort_column == 'instance_name':
                        other_rows['sort_key'] = other_rows['instance_name'].str.extract(r'S(\d+)').astype(int)
                        other_rows = other_rows.sort_values('sort_key', ascending=ascending)
                        other_rows = other_rows.drop('sort_key', axis=1)
                    else:
                        other_rows = other_rows.sort_values(sort_column, ascending=ascending)
                
                table_df = pd.concat([baseline_rows, other_rows]).reset_index(drop=True)

        # Pagination
        page_size = 10
        page_current = page_current if page_current is not None else 0
        total_rows = len(table_df)
        
        start_index = page_current * page_size
        end_index = start_index + page_size
        paginated_data = table_df.iloc[start_index:end_index]
        
        if total_rows == 0:
            table_info = "No instances found"
        else:
            start_item = start_index + 1
            end_item = min(end_index, total_rows)
            table_info = f"Showing {start_item}-{end_item} of {total_rows} instances"
        
        table_data = paginated_data.to_dict('records')
        selected_rows_on_page = list(range(len(paginated_data)))

        print(f"SPA TABLE: Returning {len(table_data)} rows, total_rows={total_rows}")
        return table_data, table_info, selected_rows_on_page
        
    except Exception as e:
        print(f"SPA Error in update_table_data: {e}")
        import traceback
        traceback.print_exc()
        return [], "Error loading data", []


@callback(
    Output('spa-selected-instances-store', 'data', allow_duplicate=True),
    Input('spa-instance-table', 'selected_rows'),
    [State('spa-instance-table', 'data'),
     State('spa-selected-instances-store', 'data')],
    prevent_initial_call=True
)
def update_selection_from_table_spain(selected_rows, table_data, current_selected):
    """Update instance selection from table"""
    
    if not selected_rows or not table_data:
        return current_selected or []
    
    table_selected = []
    for row_idx in selected_rows:
        if row_idx < len(table_data):
            instance_id = table_data[row_idx].get('instance_id')
            if instance_id:
                table_selected.append(instance_id)
    
    all_selected = list(set((current_selected or []) + table_selected))
    
    if len(all_selected) > 4:
        all_selected = all_selected[:4]
    
    return all_selected


# ==========================================
# FILTER CHIPS - SPAKIYE
# ==========================================

@callback(
    Output('spa-filter-chips-container', 'children'),
    Input('spa-table-filters', 'data'),
    prevent_initial_call=False
)
def update_filter_chips_spain(filters):
    """Display active filters as chips"""
    
    if not filters:
        return []
    
    if isinstance(filters, list) or not isinstance(filters, dict):
        return []
    
    chips = []
    
    filter_names = {
        'instance_name': 'Instance',
        'transmittance': 'Transmittance',
        'window_u': 'Window-U',
        'roof_u': 'Roof-U',
        'wall_u': 'Wall-U',
        'window_shgc': 'SHGC'
    }
    
    for column, filter_value in filters.items():
        display_name = filter_names.get(column, column)
        
        if column == 'instance_name' and isinstance(filter_value, dict):
            if filter_value.get('type') == 'instance_range':
                min_instance = filter_value.get('min', 1)
                max_instance = filter_value.get('max', 100)
                chip_text = f"{display_name}: S{min_instance} - S{max_instance}"
            else:
                continue
        elif isinstance(filter_value, list) and len(filter_value) == 2:
            min_val, max_val = filter_value
            chip_text = f"{display_name}: {min_val:.2f} - {max_val:.2f}"
        elif isinstance(filter_value, dict):
            min_val = filter_value.get('min', 0)
            max_val = filter_value.get('max', 100)
            chip_text = f"{display_name}: {min_val:.2f} - {max_val:.2f}"
        else:
            continue
        
        chip = dbc.Badge(
            [
                chip_text,
                html.Span(" ×",
                    id={"type": "spa-remove-filter", "index": column},
                    style={
                        "marginLeft": "8px",
                        "cursor": "pointer",
                        "fontWeight": "bold",
                        "color": "#FFFFFF",
                        "fontSize": "14px"
                    }
                )
            ],
            color="primary",
            className="me-2 mb-1 filter-chip-custom",
            style={
                "backgroundColor": "#2AACFD",
                "color": "#FFFFFF",
                "borderRadius": "20px",
                "fontSize": "11px",
                "padding": "6px 12px",
                "display": "inline-flex",
                "alignItems": "center",
                "marginRight": "8px",
                "marginBottom": "4px",
                "border": "none",
                "boxShadow": "0 2px 4px rgba(42, 172, 253, 0.3)"
            }
        )
        chips.append(chip)
    
    return chips


@callback(
    Output('spa-table-filters', 'data'),
    Input({"type": "spa-remove-filter", "index": dash.ALL}, 'n_clicks'),
    State('spa-table-filters', 'data'),
    prevent_initial_call=True
)
def remove_filter_spain(n_clicks_list, current_filters):
    """Remove filter when X is clicked"""
    
    if not ctx.triggered or not current_filters:
        raise PreventUpdate
    
    triggered = ctx.triggered[0]
    if triggered['value'] is None:
        raise PreventUpdate
    
    prop_id = triggered['prop_id']
    import json
    button_info = json.loads(prop_id.split('.')[0])
    filter_to_remove = button_info['index']
    
    new_filters = current_filters.copy()
    if filter_to_remove in new_filters:
        del new_filters[filter_to_remove]
    
    return new_filters


@callback(
    Output('spa-download-instances', 'data'),
    Input('spa-export-selected-btn', 'n_clicks'),
    [State('spa-scatter-plot', 'selectedData'),
     State('spa-selected-instances-store', 'data'),
     State('spa-table-search-input', 'value'),
     State('spa-table-filters', 'data')],
    prevent_initial_call=True
)
def export_selected_instances_spain(n_clicks, selectedData, selected_instances, search_value, filters):
    """Export selected instances to CSV"""
    
    if not n_clicks:
        raise PreventUpdate
    
    try:
        df, _ = get_cached_data_spain()
        table_df = df.copy()
        table_df['instance_name'] = 'S' + (table_df.index + 1).astype(str)
        
        selected_ids = set()
        
        if selectedData and 'points' in selectedData:
            for point in selectedData['points']:
                instance_id = None
                
                if 'customdata' in point and point['customdata']:
                    try:
                        if isinstance(point['customdata'], list):
                            instance_id = int(point['customdata'][0])
                        else:
                            instance_id = int(point['customdata'])
                    except (ValueError, IndexError, TypeError):
                        pass
                
                if instance_id is None and 'pointIndex' in point:
                    try:
                        point_index = point['pointIndex']
                        instance_id = point_index + 1
                    except (ValueError, TypeError):
                        pass
                
                if instance_id:
                    selected_ids.add(instance_id)
        
        if selected_instances:
            selected_ids.update(selected_instances)
        
        if not selected_ids:
            return dash.no_update
        
        mask = table_df.index.isin([id-1 for id in selected_ids])
        table_df = table_df[mask]
        
        required_columns = [
            'instance_name', 'transmittance', 'window_shgc', 
            'window_u', 'roof_u', 'wall_u', 'cooling_load', 'heating_load'
        ]
        
        for col in required_columns:
            if col not in table_df.columns and col != 'instance_name':
                table_df[col] = 0.0
        
        available_columns = [col for col in required_columns if col in table_df.columns]
        table_df = table_df[available_columns]
        
        if search_value:
            try:
                search_num = int(search_value)
                search_name = f'S{search_num}'
                table_df = table_df[table_df['instance_name'].str.contains(search_name, case=False, na=False)]
            except (ValueError, TypeError):
                search_str = str(search_value).lower()
                mask = table_df.astype(str).apply(lambda x: x.str.lower().str.contains(search_str, na=False)).any(axis=1)
                table_df = table_df[mask]
        
        if filters:
            if isinstance(filters, dict):
                for column, filter_value in filters.items():
                    if column in table_df.columns:
                        if isinstance(filter_value, list) and len(filter_value) == 2:
                            min_val, max_val = filter_value
                            table_df = table_df[
                                (table_df[column] >= min_val) & 
                                (table_df[column] <= max_val)
                            ]
        
        if table_df.empty:
            return dash.no_update
        
        column_rename = {
            'instance_name': 'Instance',
            'transmittance': 'Transmittance (%)',
            'window_shgc': 'SHGC',
            'window_u': 'Window-U (W/m²K)',
            'roof_u': 'Roof-U (W/m²K)',
            'wall_u': 'Wall-U (W/m²K)',
            'cooling_load': 'Ideal Cooling (kWh)',
            'heating_load': 'Ideal Heating (kWh)'
        }
        
        export_df = table_df.rename(columns=column_rename)
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"SPA_AllSolutions_{timestamp}.csv"
        
        print(f"SPA EXPORT: Exporting {len(export_df)} instances")
        
        return dcc.send_data_frame(export_df.to_csv, filename, index=False)
        
    except Exception as e:
        print(f"SPA Export error: {e}")
        import traceback
        traceback.print_exc()
        return dash.no_update


# ==========================================
# PAGINATION - SPAKIYE
# ==========================================

@callback(
    [Output("spa-instance-table", "page_current"),
     Output("spa-table-current-page", "children"),
     Output("spa-table-total-pages", "children"),
     Output("spa-table-first-page-btn", "disabled"),
     Output("spa-table-prev-page-btn", "disabled"),
     Output("spa-table-next-page-btn", "disabled"),
     Output("spa-table-last-page-btn", "disabled")],
    [Input("spa-table-first-page-btn", "n_clicks"),
     Input("spa-table-prev-page-btn", "n_clicks"),
     Input("spa-table-next-page-btn", "n_clicks"),
     Input("spa-table-last-page-btn", "n_clicks"),
     Input("spa-table-search-input", "value"),
     Input("spa-table-filters", "data"),
     Input('spa-scatter-plot', 'selectedData'),
     Input('spa-selected-instances-store', 'data')],
    [State("spa-instance-table", "page_current")],
    prevent_initial_call=False
)
def handle_manual_pagination_updated_spain(first_clicks, prev_clicks, next_clicks, last_clicks,
                                   search_value, filters, selectedData, selected_instances, current_page):
    """Manual pagination control"""

    try:
        ctx = callback_context
        df, df_with_id = get_cached_data_spain()

        table_df = df.copy()
        table_df['instance_name'] = pd.Series(table_df.index).apply(lambda x: 'Baseline' if x == 0 else f'S{x}')
        table_df['instance_id'] = table_df.index + 1

        selected_ids = set()

        if selectedData and 'points' in selectedData:
            for point in selectedData['points']:
                instance_id = None

                if 'customdata' in point and point['customdata']:
                    try:
                        if isinstance(point['customdata'], list):
                            instance_id = int(point['customdata'][0])
                        else:
                            instance_id = int(point['customdata'])
                    except (ValueError, IndexError, TypeError):
                        pass

                if instance_id is None and 'pointIndex' in point:
                    try:
                        point_index = point['pointIndex']
                        instance_id = point_index + 1
                    except (ValueError, TypeError):
                        pass

                if instance_id:
                    selected_ids.add(instance_id)

        if selected_instances:
            selected_ids.update(selected_instances)

        baseline_df = table_df.iloc[[0]].copy()
        
        if selected_ids:
            non_baseline_selected = [id for id in selected_ids if id > 1]
            if non_baseline_selected:
                mask = table_df.index.isin([id-1 for id in non_baseline_selected])
                selected_df = table_df[mask]
                table_df = pd.concat([baseline_df, selected_df]).drop_duplicates().reset_index(drop=True)
            else:
                table_df = baseline_df.reset_index(drop=True)
        else:
            table_df = baseline_df.reset_index(drop=True)

        if search_value:
            try:
                search_num = int(search_value)
                if search_num == 0:
                    search_name = 'Baseline'
                else:
                    search_name = f'S{search_num}'
                table_df = table_df[table_df['instance_name'].str.contains(search_name, case=False, na=False)]
            except (ValueError, TypeError):
                search_str = str(search_value).lower()
                mask = table_df.astype(str).apply(lambda x: x.str.lower().str.contains(search_str, na=False)).any(axis=1)
                table_df = table_df[mask]

        if filters and isinstance(filters, dict):
            for column, filter_value in filters.items():
                if column in table_df.columns:
                    if isinstance(filter_value, list) and len(filter_value) == 2:
                        min_val, max_val = filter_value
                        table_df = table_df[
                            (table_df[column] >= min_val) & 
                            (table_df[column] <= max_val)
                        ]

        page_size = 10
        total_rows = len(table_df)
        total_pages = max(1, (total_rows + page_size - 1) // page_size)

        new_page = current_page if current_page is not None else 0

        if ctx.triggered:
            triggered_prop = ctx.triggered[0]["prop_id"]

            if ("spa-table-search-input" in triggered_prop or
                "spa-table-filters" in triggered_prop or
                "spa-scatter-plot.selectedData" in triggered_prop or
                "spa-selected-instances-store" in triggered_prop):
                new_page = 0
            elif "spa-table-first-page-btn" in triggered_prop and first_clicks:
                new_page = 0
            elif "spa-table-prev-page-btn" in triggered_prop and prev_clicks:
                new_page = max(0, current_page - 1)
            elif "spa-table-next-page-btn" in triggered_prop and next_clicks:
                new_page = min(total_pages - 1, current_page + 1)
            elif "spa-table-last-page-btn" in triggered_prop and last_clicks:
                new_page = total_pages - 1

        new_page = max(0, min(new_page, total_pages - 1))

        current_page_display = str(new_page + 1)
        total_pages_display = str(total_pages)

        first_disabled = (new_page == 0)
        prev_disabled = (new_page == 0)
        next_disabled = (new_page >= total_pages - 1)
        last_disabled = (new_page >= total_pages - 1)

        return (new_page, current_page_display, total_pages_display,
                first_disabled, prev_disabled, next_disabled, last_disabled)

    except Exception as e:
        print(f"SPA Error in pagination: {e}")
        import traceback
        traceback.print_exc()
        return 0, "1", "1", True, True, True, True


# ==========================================
# FILTER DROPDOWN - SPAKIYE
# ==========================================

@callback(
    [Output('spa-filter-dropdown-menu', 'style'),
     Output('spa-filter-dropdown-open', 'data'),
     Output('spa-add-filter-trigger-btn', 'className')],
    [Input('spa-add-filter-trigger-btn', 'n_clicks')],
    [State('spa-filter-dropdown-open', 'data')],
    prevent_initial_call=True
)
def toggle_filter_dropdown_spain(n_clicks, is_open):
    """Toggle filter dropdown"""
    
    if n_clicks:
        new_state = not is_open
        
        if new_state:
            style = {
                "display": "block",
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
            }
            button_class = "add-filter-trigger dropdown-open"
        else:
            style = {"display": "none"}
            button_class = "add-filter-trigger"
            
        return style, new_state, button_class
    
    raise PreventUpdate


@callback(
    [Output('spa-filter-step-1', 'style'),
     Output('spa-filter-step-2', 'style'),
     Output('spa-filter-current-step', 'data')],
    [Input({"type": "spa-param-selector", "param": dash.ALL}, 'n_clicks'),
     Input('spa-filter-back-btn', 'n_clicks')],
    [State('spa-filter-current-step', 'data')],
    prevent_initial_call=True
)
def handle_filter_step_navigation_spain(param_clicks, back_clicks, current_step):
    """Handle filter step navigation"""
    
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    triggered_id = ctx.triggered[0]['prop_id']
    
    if 'spa-filter-back-btn' in triggered_id:
        return (
            {"display": "block"},
            {"display": "none"},
            1
        )
    
    elif 'spa-param-selector' in triggered_id:
        return (
            {"display": "none"},
            {"display": "block"},
            2
        )
    
    raise PreventUpdate


@callback(
    [Output('spa-filter-selected-param', 'data'),
     Output('spa-filter-min-input', 'placeholder'),
     Output('spa-filter-max-input', 'placeholder')],
    [Input({"type": "spa-param-selector", "param": dash.ALL}, 'n_clicks')],
    [State({"type": "spa-param-selector", "param": dash.ALL}, 'id')],
    prevent_initial_call=True
)
def handle_parameter_selection_spain(n_clicks_list, param_ids):
    """Handle parameter selection"""
    
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    triggered_prop = ctx.triggered[0]['prop_id']
    
    import json
    try:
        param_info = json.loads(triggered_prop.split('.')[0])
        selected_param = param_info['param']
    except:
        raise PreventUpdate
    
    df, _ = get_cached_data_spain()
    
    if selected_param == 'instance_name':
        min_placeholder = "1"
        max_placeholder = "Enter max instance number (e.g. 100)"
        return selected_param, min_placeholder, max_placeholder
    
    if selected_param not in df.columns:
        raise PreventUpdate
    
    min_val = float(df[selected_param].min())
    max_val = float(df[selected_param].max())
    
    param_info = {
        'transmittance': ('Transmittance', 20, 80, '%'),
        'window_shgc': ('SHGC', 0.1, 0.75, ''),
        'window_u': ('Window-U', 0.3, 3.0, 'W/m²K'),
        'roof_u': ('Roof-U', 0.1, 0.6, 'W/m²K'),
        'wall_u': ('Wall-U', 0.1, 0.5, 'W/m²K'),
        'heating_load': ('Heating Load', min_val, max_val, 'kWh'),
        'cooling_load': ('Cooling Load', min_val, max_val, 'kWh')
    }
    
    if selected_param in param_info:
        name, min_default, max_default, unit = param_info[selected_param]
        min_placeholder = f"{min_default:.3f}" if unit != '' else str(min_default)
        max_placeholder = f"Enter Value (e.g. {max_default:.3f})" if unit != '' else f"Enter Value (e.g. {max_default})"
    else:
        min_placeholder = f"{min_val:.3f}"
        max_placeholder = f"Enter Value (e.g. {max_val:.3f})"
    
    return selected_param, min_placeholder, max_placeholder


@callback(
    [Output('spa-table-filters', 'data', allow_duplicate=True),
     Output('spa-filter-dropdown-menu', 'style', allow_duplicate=True),
     Output('spa-filter-dropdown-open', 'data', allow_duplicate=True),
     Output('spa-add-filter-trigger-btn', 'className', allow_duplicate=True)],
    [Input('spa-filter-apply-btn', 'n_clicks')],
    [State('spa-filter-selected-param', 'data'),
     State('spa-filter-min-input', 'value'),
     State('spa-filter-max-input', 'value'),
     State('spa-table-filters', 'data')],
    prevent_initial_call=True
)
def apply_filter_from_dropdown_spain(n_clicks, selected_param, min_val, max_val, current_filters):
    """Apply selected filter"""
    
    if not n_clicks or not selected_param:
        raise PreventUpdate
    
    if min_val is None or max_val is None:
        raise PreventUpdate
    
    new_filters = current_filters.copy() if current_filters else {}
    
    if selected_param == 'instance_name':
        new_filters[selected_param] = {
            'type': 'instance_range',
            'min': int(min_val),
            'max': int(max_val)
        }
    else:
        new_filters[selected_param] = [float(min_val), float(max_val)]
    
    closed_style = {"display": "none"}
    button_class = "add-filter-trigger"
    
    return new_filters, closed_style, False, button_class


# ==========================================
# CLIENTSIDE - WARNING AUTO-CLEAR - SPAKIYE
# ==========================================

clientside_callback(
    """
    function(warning_state) {
        if (warning_state && warning_state.show) {
            console.log('SPA Warning shown, will auto-clear in 3 seconds');
            
            if (window.turWarningTimeout) {
                clearTimeout(window.turWarningTimeout);
            }
            
            window.turWarningTimeout = setTimeout(function() {
                console.log('Auto-clearing SPA warning...');
                
                if (window.dash_clientside && window.dash_clientside.set_props) {
                    try {
                        window.dash_clientside.set_props('spa-selection-warning-state', {
                            data: {show: false, message: ''}
                        });
                    } catch (error) {
                        console.error('Error auto-clearing SPA warning:', error);
                    }
                }
            }, 3000);
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('spa-selection-warning-state', 'data', allow_duplicate=True),
    Input('spa-selection-warning-state', 'data'),
    prevent_initial_call=True
)

# Clear warning on dropdown open
clientside_callback(
    """
    function(n_clicks, warning_state) {
        if (n_clicks > 0 && warning_state && warning_state.show) {
            console.log('SPA Dropdown opened, clearing warning');
            return {show: false, message: ''};
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('spa-selection-warning-state', 'data', allow_duplicate=True),
    Input('spa-virtual-dropdown-trigger', 'n_clicks'),
    State('spa-selection-warning-state', 'data'),
    prevent_initial_call=True
)

# Warning overlay DOM manipulation
clientside_callback(
    """
    function(warning_state, dropdown_state) {
        const overlay = document.getElementById('spa-warning-overlay');
        
        if (overlay) {
            if (overlay.hideTimeout) {
                clearTimeout(overlay.hideTimeout);
                overlay.hideTimeout = null;
            }
            
            if (warning_state && warning_state.show) {
                overlay.style.display = 'flex';
                
                requestAnimationFrame(() => {
                    overlay.style.opacity = '1';
                    overlay.style.transform = 'translateY(0)';
                    
                    if (dropdown_state) {
                        overlay.style.top = 'calc(100% + 320px + 12px)';
                    } else {
                        overlay.style.top = 'calc(100% + 8px)';
                    }
                });
                
                console.log('SPA Warning overlay shown');
            } else {
                overlay.style.opacity = '0';
                overlay.style.transform = 'translateY(-5px)';
                
                overlay.hideTimeout = setTimeout(function() {
                    if (overlay.style.opacity === '0') {
                        overlay.style.display = 'none';
                    }
                }, 300);
                
                console.log('SPA Warning overlay hidden');
            }
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('spa-warning-overlay', 'data-status', allow_duplicate=True),
    [Input('spa-selection-warning-state', 'data'),
     Input('spa-dropdown-open-state', 'data')],
     prevent_initial_call=True
)

# Keyboard handler
clientside_callback(
    """
    function(trigger_clicks) {
        if (trigger_clicks > 0 && !window.turKeyboardHandlerAttached) {
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    const menu = document.getElementById('spa-virtual-scroll-container');
                    const warning = document.getElementById('spa-warning-overlay');
                    
                    if (menu && menu.style.display === 'block') {
                        menu.style.display = 'none';
                        if (window.dash_clientside && window.dash_clientside.set_props) {
                            window.dash_clientside.set_props('spa-dropdown-open-state', {data: false});
                        }
                    }
                    
                    if (warning && warning.style.display === 'flex') {
                        if (window.dash_clientside && window.dash_clientside.set_props) {
                            window.dash_clientside.set_props('spa-selection-warning-state', {
                                data: {show: false, message: ''}
                            });
                        }
                    }
                }
            });
            
            window.turKeyboardHandlerAttached = true;
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('spa-virtual-dropdown-trigger', 'data-keyboard-handler'),
    Input('spa-virtual-dropdown-trigger', 'n_clicks'),
    prevent_initial_call=True
)

# Outside click for filter dropdown
clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0 && !window.turFilterDropdownClickListener) {
            setTimeout(function() {
                document.addEventListener('click', function(e) {
                    const trigger = document.getElementById('spa-add-filter-trigger-btn');
                    const menu = document.getElementById('spa-filter-dropdown-menu');
                    
                    if (trigger && menu && 
                        !trigger.contains(e.target) && 
                        !menu.contains(e.target)) {
                        
                        if (menu.style.display === 'block') {
                            menu.style.display = 'none';
                            trigger.className = 'add-filter-trigger';
                            
                            if (window.dash_clientside && window.dash_clientside.set_props) {
                                try {
                                    window.dash_clientside.set_props('spa-filter-dropdown-open', {data: false});
                                } catch (error) {
                                    console.error('Error closing SPA filter dropdown:', error);
                                }
                            }
                        }
                    }
                }, { passive: true });
                
                window.turFilterDropdownClickListener = true;
            }, 50);
        }
        return 'attached';
    }
    """,
    Output('spa-add-filter-trigger-btn', 'data-click-listener'),
    Input('spa-add-filter-trigger-btn', 'n_clicks'),
    prevent_initial_call=True
)


# ==========================================
# CACHE MANAGEMENT - SPAKIYE
# ==========================================

def clear_caches_spain():
    """Clear all Spain caches"""
    global _dropdown_cache_spain, _param_cache_spain, _comparison_cache_spain, _graph_cache_spain
    _dropdown_cache_spain.clear()
    _param_cache_spain.clear()
    _comparison_cache_spain.clear()
    _graph_cache_spain.clear()
    print("SPA: All caches cleared")

