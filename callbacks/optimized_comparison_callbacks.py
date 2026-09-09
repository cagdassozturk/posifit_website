import dash
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate
import time
import threading
import re
from pages.optimized import df
from dash import callback, Output, Input, ctx, html, dcc, State, clientside_callback, callback_context

# ==========================================
# PERFORMANCE OPTIMIZATIONS
# ==========================================

# 1. Cache the data - load once, use everywhere
_cached_data = None
_cached_df_with_id = None

def get_cached_data():
    """Load data once and cache it - optimized page uses pareto_front_predicted_100_yeni.csv"""
    global _cached_data, _cached_df_with_id
    if _cached_data is None:
        # Use the optimized CSV file with semicolon separator
        _cached_data = pd.read_csv("data/pareto_front_predicted_100_yeni.csv", sep=';')
        _cached_df_with_id = _cached_data.copy()
        _cached_df_with_id['ID'] = _cached_df_with_id.index + 1
    return _cached_data, _cached_df_with_id

def get_selectable_data():
    """Get selectable data for optimized page"""
    df, df_with_id = get_cached_data()
    # Optimized sayfasında baseline (index=0) hariç tüm instance'lar seçilebilir
    selectable_df = df_with_id.iloc[1:].copy()  # İlk satırı (baseline) atla
    # ID'leri yeniden ayarla: S1=1, S2=2, ..., S100=100
    selectable_df = selectable_df.reset_index(drop=True)
    selectable_df['ID'] = selectable_df.index + 1  # 0-based index'i 1-based ID'ye çevir
    return selectable_df

# ==========================================
# CACHE DICTIONARIES
# ==========================================

# Cache dictionaries
_dropdown_cache = {}
_param_cache = {}
_comparison_cache = {}
_graph_cache = {}

def format_co2_value(co2_value):
    """CO2 değerini formatla - 0 ise N/A göster"""
    try:
        if co2_value is None or co2_value == 0 or pd.isna(co2_value):
            return "N/A"
        else:
            return f"{co2_value:,.0f}"
    except:
        return "N/A"
        
# ==========================================
# VIRTUAL CONTENT UPDATE - OPTIMIZED PAGE
# ==========================================

@callback(
    [Output('opt-virtual-scroll-container', 'children'),
     Output('opt-virtual-scroll-position', 'data')],
    [Input('opt-virtual-scroll-container', 'scrollTop'),
     Input('opt-comparison-selected-instances-store', 'data'),
     Input('opt-sort-by-dropdown', 'value'),
     Input('opt-sort-order-radio', 'value'),
     Input('opt-virtual-scroll-position', 'data')],
    [State('opt-virtual-item-height', 'data'),
     State('opt-virtual-container-height', 'data')],
    prevent_initial_call=False
)
def update_virtual_content_combined(scroll_top_prop, selected_instances, sort_by, sort_order, scroll_position_data, item_height, container_height):
    """Virtual scrolling for optimized page"""
    
    try:
        # Scroll pozisyonunu doğru şekilde al
        scroll_top = scroll_position_data if scroll_position_data is not None else (scroll_top_prop if scroll_top_prop is not None else 0)
        
        # Varsayılan değerleri ayarla
        if item_height is None:
            item_height = 40
        if container_height is None:
            container_height = 320
        
        df, df_with_id = get_cached_data()
        # Use only selectable data (excluding baseline)
        selectable_df = get_selectable_data()
        
        # Selected instances'ı set olarak kullan
        selected_set = set(selected_instances) if selected_instances else set()
        
        # Cache key
        selected_key = "_".join(map(str, sorted(selected_set))) if selected_set else "none"
        scroll_group = int(scroll_top / (item_height * 5))
        cache_key = f"{scroll_group}_{selected_key}_{sort_by}_{sort_order}"
        
        triggered_id = ctx.triggered_id
        
        # Cache kontrolü
        if cache_key in _dropdown_cache and triggered_id != 'opt-selected-instances-store':
            print(f"CACHE HIT: Using cached content for scroll_group={scroll_group}")
            return _dropdown_cache[cache_key], scroll_top
        
        # Sorting
        is_ascending = (sort_order == 'asc')
        if sort_by == 'ID':
            sorted_df = selectable_df.sort_values('ID', ascending=True)
        else:
            sorted_df = selectable_df.sort_values(by=sort_by, ascending=is_ascending)
        
        total_items = len(sorted_df)
        
        # Buffer ve görünür aralık hesaplaması
        buffer = 20
        items_per_view = max(1, int(container_height / item_height))
        first_visible_index = max(0, int(scroll_top / item_height))
        
        # Visible range hesaplaması
        visible_start = max(0, first_visible_index - buffer)
        visible_end = min(total_items, first_visible_index + items_per_view + buffer)
        
        # Minimum görünür range garanti et
        min_items = items_per_view + (buffer * 2)
        if (visible_end - visible_start) < min_items:
            visible_end = min(total_items, visible_start + min_items)
        
        print(f"VIRTUAL RENDER: Scroll={scroll_top}, Range={visible_start}-{visible_end}/{total_items}, Buffer={buffer}")
        
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
                print(f"VIRTUAL: Breaking at index {i}, total items: {len(sorted_df)}")
                break
                
            row = sorted_df.iloc[i]
            instance_id = int(row['ID'])
            
            # DEBUG: S1 için özel log
            if instance_id == 1:
                print(f"DEBUG: Rendering S1 with instance_id={instance_id}, selected_set={selected_set}")
            
            # Selected state kontrolü
            is_selected = instance_id in selected_set
            
            # Extra info for sorting
            extra_info = ""
            if sort_by != 'ID' and sort_by in row:
                try:
                    extra_val = row.get(sort_by, 0)
                    if isinstance(extra_val, (int, float)):
                        extra_info = f" ({extra_val:.1f})"
                except:
                    pass
            
            # Checkbox'ı unique ID ile oluştur
            checkbox_value = [instance_id] if is_selected else []
            unique_checkbox_id = f"opt-virtual-checkbox-{instance_id}-{scroll_group}"
            
            visible_items.append(
                html.Div([
                    html.Div(
                        f"S{instance_id}{extra_info}",
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
                            id={"type": "opt-virtual-checkbox", "index": instance_id, "unique": unique_checkbox_id},
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
                id=f"opt-virtual-item-{instance_id}",
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
        
        print(f"VIRTUAL: Successfully rendered {items_rendered} items")
        
        # Cache yönetimi
        if len(_dropdown_cache) > 50:
            old_keys = list(_dropdown_cache.keys())[:25]
            for key in old_keys:
                del _dropdown_cache[key]
            print("Cache cleaned - removed old entries")
        
        _dropdown_cache[cache_key] = visible_items
        
        return visible_items, scroll_top
        
    except Exception as e:
        print(f"Virtual content error: {e}")
        import traceback
        traceback.print_exc()
        return [html.Div(f"Loading error: {str(e)}", style={"padding": "20px", "textAlign": "center", "color": "red"})], scroll_top or 0


# ==========================================
# WARNING OVERLAY MANAGEMENT - OPTIMIZED PAGE
# ==========================================

@callback(
    [Output('opt-warning-overlay', 'children'),
     Output('opt-warning-overlay', 'style')],
    Input('opt-selection-warning-state', 'data'),
    [State('opt-dropdown-open-state', 'data')],
    prevent_initial_call=False
)
def update_warning_overlay(warning_state, dropdown_is_open):
    """Uyarı overlay'ini dropdown'ın altında yönet"""
    
    # Eğer uyarı gösterilmeyecekse gizli tut
    if not warning_state or not warning_state.get('show', False):
        return [], {
            "display": "none",
            "position": "absolute",
            "top": "calc(100% + 8px)",
            "left": "0",
            "right": "0",
            "zIndex": "999",
            "pointerEvents": "none",
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
    
    # Uyarı içeriğini oluştur
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
    
    # Dropdown durumuna göre pozisyonu ayarla
    if dropdown_is_open:
        top_position = "calc(100% + 320px + 12px)"
    else:
        top_position = "calc(100% + 8px)"
    
    # Görünür stil
    visible_style = {
        "display": "flex",
        "position": "absolute",
        "top": top_position,
        "left": "0",
        "right": "0",
        "zIndex": "999",
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
    Output('opt-warning-overlay', 'style', allow_duplicate=True),
    Input('opt-dropdown-open-state', 'data'),
    [State('opt-selection-warning-state', 'data'),
     State('opt-warning-overlay', 'style')],
    prevent_initial_call=True
)
def update_warning_position_on_dropdown_toggle(dropdown_is_open, warning_state, current_style):
    """Dropdown açılıp kapandığında uyarı pozisyonunu güncelle"""
    
    if not warning_state or not warning_state.get('show', False):
        raise PreventUpdate
    
    if current_style is None:
        current_style = {}
    
    # Pozisyonu güncelle
    if dropdown_is_open:
        current_style["top"] = "calc(100% + 320px + 12px)"
    else:
        current_style["top"] = "calc(100% + 8px)"
    
    return current_style
    

# ==========================================
# SELECTION HANDLING - OPTIMIZED PAGE
# ==========================================

@callback(
    [Output('opt-comparison-selected-instances-store', 'data'),
     Output('opt-selection-warning-state', 'data')],
    [Input({"type": "opt-virtual-checkbox", "index": dash.ALL, "unique": dash.ALL}, 'value'),
     Input('opt-search-input', 'n_submit')],
    [State({"type": "opt-virtual-checkbox", "index": dash.ALL, "unique": dash.ALL}, 'id'),
     State('opt-comparison-selected-instances-store', 'data'),
     State('opt-search-input', 'value')],
    prevent_initial_call=True
)
def handle_selection_and_search_with_warning(all_values, n_submit, all_ids, current_selected, search_value):
    """Selection handling for optimized page"""
    
    if current_selected is None:
        current_selected = []
    
    triggered_id = ctx.triggered_id
    warning_state = {"show": False, "message": ""}
    
    # Handle search input
    if triggered_id == 'opt-search-input' and n_submit and search_value is not None:
        try:
            instance_id = int(search_value)
            if 1 <= instance_id <= 100:  # S1 to S100
                new_selected = current_selected.copy()
                if instance_id not in new_selected:
                    # 4 instance limit check
                    if len(new_selected) >= 4:
                        warning_state = {
                            "show": True,
                            "message": "⚠️ Maximum 4 instances can be selected for comparison"
                        }
                        return current_selected, warning_state
                    
                    new_selected.append(instance_id)
                    print(f"SEARCH: Added S{instance_id}, total selected: {len(new_selected)}")
                
                # Clear cache with delay
                def delayed_cache_clear():
                    time.sleep(0.1)
                    global _dropdown_cache
                    _dropdown_cache.clear()
                    print("SEARCH: Cache cleared")
                
                threading.Thread(target=delayed_cache_clear, daemon=True).start()
                
                return new_selected, warning_state
        except (ValueError, TypeError):
            pass
        return current_selected, warning_state
    
    # Handle checkbox selection - DEBUG eklendi
    if all_values and all_ids:
        try:
            triggered_info = ctx.triggered[0] if ctx.triggered else None
            if not triggered_info:
                raise PreventUpdate
                
            prop_id = triggered_info.get('prop_id', '')
            if 'opt-virtual-checkbox' not in prop_id:
                raise PreventUpdate
            
            # Extract instance ID from prop_id
            match = re.search(r'"index":(\d+)', prop_id)
            if not match:
                raise PreventUpdate
                
            changed_instance_id = int(match.group(1))
            print(f"OPT SELECTION: Processing change for S{changed_instance_id}")
            
            # Find checkbox state
            is_now_checked = False
            for i, values in enumerate(all_values):
                if all_ids[i]["index"] == changed_instance_id:
                    is_now_checked = bool(values and len(values) > 0)
                    print(f"OPT SELECTION: S{changed_instance_id} checkbox state: {is_now_checked}")
                    break
            
            # Update selection
            new_selected = current_selected.copy()
            
            if is_now_checked and changed_instance_id not in new_selected:
                # Adding instance
                if len(new_selected) >= 4:
                    warning_state = {
                        "show": True,
                        "message": "⚠️ Maximum 4 instances can be selected for comparison"
                    }
                    return current_selected, warning_state
                
                new_selected.append(changed_instance_id)
                print(f"OPT SELECTION: Added S{changed_instance_id} (Total: {len(new_selected)})")
                    
            elif not is_now_checked and changed_instance_id in new_selected:
                # Removing instance
                new_selected.remove(changed_instance_id)
                print(f"OPT SELECTION: Removed S{changed_instance_id} (Total: {len(new_selected)})")
            
            # Check if state changed
            if set(new_selected) != set(current_selected):
                print(f"OPT SELECTION: Updated from {current_selected} to {new_selected}")
                
                # Clear cache with delay
                def delayed_cache_clear():
                    time.sleep(0.1)
                    global _dropdown_cache
                    _dropdown_cache.clear()
                    print("OPT SELECTION: Cache cleared for checkbox update")
                
                threading.Thread(target=delayed_cache_clear, daemon=True).start()
                
                return new_selected, warning_state
        
        except Exception as e:
            print(f"OPT Selection error: {e}")
            import traceback
            traceback.print_exc()
    
    return current_selected, warning_state


# ==========================================
# DROPDOWN STATE MANAGEMENT - OPTIMIZED PAGE
# ==========================================

@callback(
    [Output('opt-virtual-scroll-container', 'style'),
     Output('opt-dropdown-open-state', 'data'),
     Output('opt-virtual-dropdown-trigger', 'children')],
    [Input('opt-virtual-dropdown-trigger', 'n_clicks'),
     Input('opt-comparison-selected-instances-store', 'data')],
    [State('opt-dropdown-open-state', 'data')],
    prevent_initial_call=True
)
def handle_dropdown_state_combined(n_clicks, selected_instances, is_open):
    """Dropdown toggle for optimized page"""
    
    triggered_id = ctx.triggered_id
    
    # Handle dropdown toggle
    if triggered_id == 'opt-virtual-dropdown-trigger' and n_clicks:
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
        
        # Dropdown açıldığında cache'i temizle
        if new_state:
            global _dropdown_cache
            _dropdown_cache.clear()
            print("DROPDOWN: Opened, cleared cache for fresh content")
        
        trigger_text = get_trigger_text(selected_instances)
        return style, new_state, trigger_text
    
    # Handle only trigger text update
    if triggered_id == 'opt-selected-instances-store':
        current_style = {
            "display": "block" if is_open else "none",
            "height": "320px",
            "maxHeight": "320px",
            "minHeight": "320px"
        } if is_open else {"display": "none"}
        trigger_text = get_trigger_text(selected_instances)
        return current_style, is_open, trigger_text
    
    raise PreventUpdate
    
    
def get_trigger_text(selected_instances):
    """Display text for dropdown trigger"""
    if not selected_instances or len(selected_instances) == 0:
        return "Select instances..."
    
    # For optimized: IDs directly map to display (S1=ID1, S2=ID2, etc.)
    display_ids = selected_instances
    
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
# SEARCH TOGGLE - OPTIMIZED PAGE
# ==========================================

@callback(
    [Output('opt-search-input-container', 'className'),
     Output('opt-search-toggle-state', 'data'),
     Output('opt-search-input', 'value'),
     Output('opt-search-toggle-button', 'className')],
    [Input('opt-search-toggle-button', 'n_clicks'),
     Input('opt-search-input', 'n_submit')],
    [State('opt-search-toggle-state', 'data'),
     State('opt-search-input', 'value')],
    prevent_initial_call=True
)
def handle_search_toggle_combined(toggle_clicks, submit_count, is_open, search_value):
    """Handle search visibility and button styling"""
    
    triggered_id = ctx.triggered_id
    
    if triggered_id == 'opt-search-toggle-button':
        current_state = is_open if is_open is not None else False
        new_state = not current_state
        
        container_class = "search-input-container" if new_state else "search-input-container hidden"
        button_class = "search-toggle-button search-open" if new_state else "search-toggle-button"
        
        return container_class, new_state, dash.no_update, button_class

    if triggered_id == 'opt-search-input' and search_value:
        return "search-input-container hidden", False, "", "search-toggle-button"
            
    raise PreventUpdate


# ==========================================
# PARAMETER UPDATE - OPTIMIZED PAGE
# ==========================================

@callback(
    Output('opt-instance-parameters', 'children'),
    Input('opt-comparison-selected-instances-store', 'data'),
    prevent_initial_call=False
)
def update_instance_parameters_optimized(selected_instances):
    """Optimized parameter updates with caching"""
    
    df, _ = get_cached_data()
    
    # Eğer hiçbir instance seçilmemişse baseline'ı göster
    if not selected_instances or len(selected_instances) == 0:
        selected_id = 0  # Baseline row index
        baseline_mode = True
        row = df.iloc[0]  # Baseline row
    else:
        selected_id = selected_instances[0]
        baseline_mode = False
        # Map selectable ID to actual dataframe row: S1 (ID=1) -> row 1, S2 (ID=2) -> row 2, etc.
        row = df.iloc[selected_id]  # selected_id directly maps to row index for scenarios
    
    # Cache key'e baseline durumu da dahil et
    cache_key = f"{selected_id}_baseline_{baseline_mode}"
    
    # Check cache first
    if cache_key in _param_cache:
        return _param_cache[cache_key]
    
    def param_card(label, val, min_val, max_val, unit="", is_baseline=False, param_name=""):
        # Baseline için Transmittance özel durumu
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

    # Başlık metnini baseline durumuna göre ayarla
    if baseline_mode:
        title_text = f"Parameters for Baseline:"
        title_color = "#4E5E66"
    else:
        display_id = selected_id  # For optimized: S1 has ID=1, S2 has ID=2, etc.
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
    
    # Cache the result
    _param_cache[cache_key] = result
    return result


# ==========================================
# COMPARISON UPDATE - OPTIMIZED PAGE
# ==========================================

@callback(
    Output('opt-instance-comparison-content', 'children'),
    Input('opt-comparison-selected-instances-store', 'data'),
    prevent_initial_call=False
)
def update_instance_comparison_optimized(selected_instances):
    """Instance comparison table for optimized page"""
    df, _ = get_cached_data()
    
    # Scenario sütunundaki ilk satır (index 0) baseline
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
                return format_co2_value(raw_val)
            else:
                if pd.isna(raw_val):
                    return html.Span("N/A", className="na-value")
                return f"{raw_val:,.0f}"
        except:
            return html.Span("N/A", className="na-value") if metric_key == "co2" else str(raw_val)

    def create_instance_content_with_remove_btn(instance_label, instance_id):
        display_id = instance_id  # For optimized: ID directly maps to display (S1=ID1, S2=ID2, etc.)
        return html.Div([
            html.Div([
                html.Div([
                    html.Div(instance_label, className="label-main-text"),
                    html.Div(f"S{display_id}", className="label-sub-text")
                ], style={"flex": "1", "display": "flex", "flexDirection": "column", "alignItems": "center", "justifyContent": "center"}),
                html.Button(
                    "×", 
                    id={"type": "opt-remove-instance-btn", "index": instance_id},
                    className="remove-instance-btn",
                    title=f"Remove S{display_id}"
                )
            ], style={"position": "relative", "width": "100%", "height": "100%", "display": "flex", "alignItems": "center", "justifyContent": "center"})
        ], className="blue-label-content")

    num_selected = len(selected_instances) if selected_instances else 0
    card_class = "instance-comparison-card"

    # Header cells
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

    # Durum 1: Hiç instance seçili değil (Sadece Baseline)
    if num_selected == 0:
        content_grid = html.Div(
            header_cells + baseline_cells,
            className="comparison-grid content-block-50"
        )
        return html.Div(content_grid, className=f"{card_class} comparison-layout-baseline-only", style={'height': '100%'})

    # Durum 2: 1 instance seçili
    elif num_selected == 1:
        instance_id = selected_instances[0]
        sel_row = df.iloc[instance_id]  # For optimized: ID directly maps to row index
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
        
    # Durum 3: 2, 3 veya 4 instance seçili
    else:
        if num_selected == 2:
            grid_class = "comparison-grid"
        elif num_selected == 3:
            grid_class = "comparison-grid-4rows"
        else: # num_selected == 4
            grid_class = "comparison-grid-5rows"
            
        grid_cells = header_cells + baseline_cells
        
        for i, instance_id in enumerate(selected_instances):
            sel_row = df.iloc[instance_id]  # For optimized: ID directly maps to row index
            instance_content_with_btn = create_instance_content_with_remove_btn(f"Instance {i+1}", instance_id)
            grid_cells.append(html.Div(instance_content_with_btn, className="grid-cell label-cell"))
            for _, _, col_key, _, _ in metrics:
                main_val = sel_row.get(col_key, 0)
                baseline_val = baseline_row.get(col_key, 0)
                cell_content = create_value_with_savings(main_val, baseline_val, col_key)
                grid_cells.append(html.Div(cell_content, className="grid-cell value-cell chosen-value"))
        
        return html.Div(html.Div(grid_cells, className=grid_class), className=card_class, style={'height': '100%'})


# ==========================================
# REMOVE BUTTON - OPTIMIZED PAGE
# ==========================================

@callback(
    Output('opt-comparison-selected-instances-store', 'data', allow_duplicate=True),
    Input({"type": "opt-remove-instance-btn", "index": dash.ALL}, 'n_clicks'),
    State('opt-comparison-selected-instances-store', 'data'),
    prevent_initial_call=True
)
def handle_remove_instance_button(n_clicks_list, current_selected):
    """Handle remove instance button clicks"""
    
    if not ctx.triggered or not current_selected:
        raise PreventUpdate
    
    # Hangi butonun tıklandığını bul
    triggered = ctx.triggered[0]
    
    if triggered['value'] is None:
        raise PreventUpdate
    
    # Button'un prop_id'sinden instance_id'yi çıkar
    prop_id = triggered['prop_id']
    import json
    try:
        button_info = json.loads(prop_id.split('.')[0])
        instance_id_to_remove = button_info['index']
        print(f"DEBUG REMOVE: Will remove S{instance_id_to_remove}")
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Error parsing button prop_id: {prop_id}, error: {e}")
        raise PreventUpdate
    
    # Instance'ı listeden kaldır
    new_selected = [inst_id for inst_id in current_selected if inst_id != instance_id_to_remove]
    
    print(f"REMOVE BUTTON: Removed S{instance_id_to_remove}, new selection: {new_selected}")
    
    # Cache'i temizle
    global _dropdown_cache, _comparison_cache, _graph_cache
    _dropdown_cache.clear()
    _comparison_cache.clear()
    _graph_cache.clear()
    
    return new_selected


# ==========================================
# GRAPH UPDATE - OPTIMIZED PAGE
# ==========================================

@callback(
    Output('opt-comparison-graph', 'figure'),
    Input('opt-comparison-selected-instances-store', 'data'),
    prevent_initial_call=False
)
def update_comparison_graph_optimized(selected_instances):
    """Graph updates for optimized page"""
    
    df, _ = get_cached_data()
    baseline_row = df.iloc[0]  # First row is baseline
    
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
    
    # Hiçbir instance seçilmemişse sadece baseline göster
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
    cache_key = "_".join(map(str, sorted(selected_instances)))
    
    if cache_key in _graph_cache:
        return _graph_cache[cache_key]
    
    traces = []
    
    # Renk paleti
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
        selected_row = df.iloc[instance_id]  # For optimized: ID directly maps to row index
        selected_vals = [transform_value(selected_row[f], f) for f in features]
        display_id = instance_id  # For optimized: ID directly maps to display
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
    
    # Cache the result
    _graph_cache[cache_key] = fig
    return fig


# ==========================================
# CLIENTSIDE CALLBACKS FOR PERFORMANCE - OPTIMIZED PAGE
# ==========================================

# Scroll handler
clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            setTimeout(function() {
                const container = document.getElementById('opt-virtual-scroll-container');
                
                if (container && !container.hasScrollListener) {
                    let scrollTimeout;
                    let lastScrollTop = 0;
                    let isScrolling = false;
                    
                    console.log('Setting up enhanced scroll listener for optimized...');
                    
                    container.addEventListener('scroll', function(e) {
                        const scrollTop = e.target.scrollTop;
                        const scrollHeight = e.target.scrollHeight;
                        const clientHeight = e.target.clientHeight;
                        
                        if (Math.abs(scrollTop - lastScrollTop) > 10) {
                            console.log(`OPT SCROLL: top=${scrollTop}, height=${scrollHeight}, client=${clientHeight}`);
                        }
                        
                        isScrolling = true;
                        
                        if (scrollTimeout) {
                            clearTimeout(scrollTimeout);
                        }
                        
                        scrollTimeout = setTimeout(function() {
                            if (Math.abs(scrollTop - lastScrollTop) > 3) {
                                lastScrollTop = scrollTop;
                                
                                if (window.dash_clientside && window.dash_clientside.set_props) {
                                    try {
                                        window.dash_clientside.set_props('opt-virtual-scroll-position', {
                                            data: scrollTop
                                        });
                                        console.log(`OPT SCROLL UPDATE: ${scrollTop}`);
                                    } catch (error) {
                                        console.error('Error updating opt scroll position:', error);
                                    }
                                }
                            }
                            isScrolling = false;
                        }, 30);
                        
                        if (scrollTop + clientHeight >= scrollHeight - 20) {
                            console.log('OPT SCROLL: Near bottom, immediate update');
                            if (window.dash_clientside && window.dash_clientside.set_props) {
                                try {
                                    window.dash_clientside.set_props('opt-virtual-scroll-position', {
                                        data: scrollTop
                                    });
                                } catch (error) {
                                    console.error('Error in immediate opt scroll update:', error);
                                }
                            }
                        }
                        
                    }, { passive: true });
                    
                    container.hasScrollListener = true;
                    console.log('Enhanced scroll listener attached for optimized');
                }
            }, 100);
        }
        return n_clicks;
    }
    """,
    Output('opt-virtual-scroll-container', 'data-scroll-initialized'),
    Input('opt-virtual-dropdown-trigger', 'n_clicks'),
    prevent_initial_call=True
)

# Outside click handler
clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0 && !window.optOutsideClickAttached) {
            setTimeout(function() {
                document.addEventListener('click', function(e) {
                    const dropdown = document.getElementById('opt-virtual-dropdown-trigger');
                    const menu = document.getElementById('opt-virtual-scroll-container');
                    const warning = document.getElementById('opt-warning-overlay');
                    
                    if (dropdown && menu && 
                        !dropdown.contains(e.target) && 
                        !menu.contains(e.target) &&
                        (!warning || !warning.contains(e.target))) {
                        
                        if (menu.style.display === 'block') {
                            menu.style.display = 'none';
                            if (window.dash_clientside && window.dash_clientside.set_props) {
                                window.dash_clientside.set_props('opt-dropdown-open-state', {data: false});
                            }
                        }
                    }
                }, { passive: true });
                
                window.optOutsideClickAttached = true;
            }, 50);
        }
        return 'attached';
    }
    """,
    Output('opt-dummy-outside-click', 'children'),
    Input('opt-virtual-dropdown-trigger', 'n_clicks'),
    prevent_initial_call=True
)

@callback(
    [Output('opt-virtual-item-height', 'data'),
     Output('opt-virtual-container-height', 'data')],
    Input('opt-virtual-dropdown-trigger', 'n_clicks'),
    prevent_initial_call=False
)
def validate_virtual_dimensions(n_clicks):
    """Validate virtual scrolling dimensions"""
    
    item_height = 40
    container_height = 320
    
    print(f"OPT VIRTUAL DIMENSIONS: item_height={item_height}, container_height={container_height}")
    print(f"OPT VIRTUAL DIMENSIONS: items_per_view={container_height/item_height}")
    
    return item_height, container_height


@callback(
    Output('opt-virtual-scroll-container', 'data-total-items'),
    Input('opt-sort-by-dropdown', 'value'),
    prevent_initial_call=False
)
def validate_total_items(sort_by):
    """Validate total number of items available for virtual scrolling"""
    
    selectable_df = get_selectable_data()
    total_items = len(selectable_df)
    
    print(f"OPT VIRTUAL VALIDATION: Total selectable items: {total_items}")
    print(f"OPT VIRTUAL VALIDATION: Max scroll position should be around: {total_items * 40}px")
    print(f"OPT VIRTUAL VALIDATION: ID range: {selectable_df['ID'].min()} - {selectable_df['ID'].max()}")
    
    return total_items


# ==========================================
# WARNING AUTO-CLEAR - OPTIMIZED PAGE
# ==========================================

clientside_callback(
    """
    function(warning_state) {
        if (warning_state && warning_state.show) {
            console.log('OPT Warning shown, will auto-clear in 3 seconds');
            
            if (window.optWarningTimeout) {
                clearTimeout(window.optWarningTimeout);
            }
            
            window.optWarningTimeout = setTimeout(function() {
                console.log('Auto-clearing opt warning...');
                
                if (window.dash_clientside && window.dash_clientside.set_props) {
                    try {
                        window.dash_clientside.set_props('opt-selection-warning-state', {
                            data: {show: false, message: ''}
                        });
                    } catch (error) {
                        console.error('Error auto-clearing opt warning:', error);
                    }
                }
            }, 3000);
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('opt-selection-warning-state', 'data', allow_duplicate=True),
    Input('opt-selection-warning-state', 'data'),
    prevent_initial_call=True
)

# Dropdown açıldığında uyarıyı temizle
clientside_callback(
    """
    function(n_clicks, warning_state) {
        if (n_clicks > 0 && warning_state && warning_state.show) {
            console.log('OPT Dropdown opened, clearing warning overlay');
            return {show: false, message: ''};
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('opt-selection-warning-state', 'data', allow_duplicate=True),
    Input('opt-virtual-dropdown-trigger', 'n_clicks'),
    State('opt-selection-warning-state', 'data'),
    prevent_initial_call=True
)

# Warning overlay DOM manipulation
clientside_callback(
    """
    function(warning_state, dropdown_state) {
        const overlay = document.getElementById('opt-warning-overlay');
        
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
                
                console.log('OPT Warning overlay shown');
            } else {
                overlay.style.opacity = '0';
                overlay.style.transform = 'translateY(-5px)';
                
                overlay.hideTimeout = setTimeout(function() {
                    if (overlay.style.opacity === '0') {
                        overlay.style.display = 'none';
                    }
                }, 300);
                
                console.log('OPT Warning overlay hidden');
            }
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('opt-warning-overlay', 'data-status', allow_duplicate=True),
    [Input('opt-selection-warning-state', 'data'),
     Input('opt-dropdown-open-state', 'data')],
     prevent_initial_call=True
)

# Keyboard handler
clientside_callback(
    """
    function(trigger_clicks) {
        if (trigger_clicks > 0 && !window.optKeyboardHandlerAttached) {
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    const menu = document.getElementById('opt-virtual-scroll-container');
                    const warning = document.getElementById('opt-warning-overlay');
                    
                    if (menu && menu.style.display === 'block') {
                        menu.style.display = 'none';
                        if (window.dash_clientside && window.dash_clientside.set_props) {
                            window.dash_clientside.set_props('opt-dropdown-open-state', {data: false});
                        }
                    }
                    
                    if (warning && warning.style.display === 'flex') {
                        if (window.dash_clientside && window.dash_clientside.set_props) {
                            window.dash_clientside.set_props('opt-selection-warning-state', {
                                data: {show: false, message: ''}
                            });
                        }
                    }
                }
            });
            
            window.optKeyboardHandlerAttached = true;
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('opt-virtual-dropdown-trigger', 'data-keyboard-handler'),
    Input('opt-virtual-dropdown-trigger', 'n_clicks'),
    prevent_initial_call=True
)


# ==========================================
# CACHE MANAGEMENT
# ==========================================

def clear_caches():
    """Clear all caches to free memory"""
    global _dropdown_cache, _param_cache, _comparison_cache, _graph_cache
    _dropdown_cache.clear()
    _param_cache.clear()
    _comparison_cache.clear()
    _graph_cache.clear()
    print("All caches cleared")

def manage_cache_size():
    """Manage cache size to prevent memory issues"""
    max_cache_size = 25
    
    for cache_dict in [_dropdown_cache, _param_cache, _comparison_cache, _graph_cache]:
        if len(cache_dict) > max_cache_size:
            items = list(cache_dict.items())
            cache_dict.clear()
            cache_dict.update(items[-max_cache_size//2:])

# Cache cleanup disabled for now to avoid syntax issues
# def cache_cleanup_thread():
#     """Background thread for cache cleanup"""
#     while True:
#         time.sleep(180)
#         try:
#             manage_cache_size()
#         except Exception as e:
#             print(f"Cache cleanup error: {e}")

# # Start cache cleanup thread
# cleanup_thread = threading.Thread(target=cache_cleanup_thread, daemon=True)
# cleanup_thread.start()


# ==========================================
# INSTANCE TABLE CALLBACKS - OPTIMIZED PAGE
# ==========================================

# optimized_comparison_callbacks.py dosyasındaki update_table_data_optimized fonksiyonunu bu kodla değiştirin:

@callback(
    [Output("opt-instance-table", "data"),
     Output("opt-table-info", "children"),
     Output("opt-instance-table", "selected_rows")],
    [Input("opt-instance-table", "page_current"),
     Input("opt-table-search-input", "value"),
     Input("opt-table-filters", "data"),
     Input('opt-scatter-plot', 'selectedData'),
     Input('opt-selected-instances-store', 'data'),
     Input('opt-instance-table', 'sort_by')],
    prevent_initial_call=False
)
def update_table_data_optimized(page_current, search_value, filters, selectedData, selected_instances, sort_by):
    """Table data update for optimized page with BASELINE ALWAYS ON TOP + FORMATTING"""
    
    try:
        print(f"OPT TABLE DATA DEBUG: sort_by = {sort_by}")
        
        df, _ = get_cached_data()
        
        # Veriyi hazırla - BASELINE HER ZAMAN GÖRÜNECEK
        baseline_df = df.iloc[[0]].copy()  # Baseline (index 0)
        baseline_df['instance_name'] = 'Baseline'
        baseline_df['instance_id'] = 0  # Baseline için özel ID
        
        # Seçili instance'ları belirle
        selected_ids = set()
        
        # Scatter plot'tan seçilenler
        if selectedData and 'points' in selectedData:
            for point in selectedData['points']:
                instance_id = None
                
                # CustomData'dan ID'yi al
                if 'customdata' in point and point['customdata']:
                    try:
                        if isinstance(point['customdata'], list):
                            instance_id = int(point['customdata'][0])
                        else:
                            instance_id = int(point['customdata'])
                    except (ValueError, IndexError, TypeError):
                        pass
                
                # Fallback: pointIndex kullan
                if instance_id is None and 'pointIndex' in point:
                    try:
                        point_index = point['pointIndex']
                        instance_id = point_index + 1
                    except (ValueError, TypeError):
                        pass
                
                if instance_id:
                    selected_ids.add(instance_id)
        
        # Dropdown'dan seçilenler
        if selected_instances:
            selected_ids.update(selected_instances)
        
        if selected_ids:
            # Non-baseline seçimleri filtrele (ID > 0)
            non_baseline_selected = [id for id in selected_ids if id > 0]
            if non_baseline_selected:
                # Non-baseline instance'lar (1-based indexing)
                remaining_df = df.iloc[1:].copy()  # Baseline'ı atla
                remaining_df['instance_name'] = 'S' + (remaining_df.index).astype(str)  # S1, S2, S3...
                remaining_df['instance_id'] = remaining_df.index  # 1, 2, 3, ...
                
                mask = remaining_df['instance_id'].isin(non_baseline_selected)
                selected_df = remaining_df[mask]
                
                # Baseline + seçili instance'lar
                table_df = pd.concat([baseline_df, selected_df]).reset_index(drop=True)
            else:
                # Sadece baseline seçilmişse veya baseline dahil seçim varsa
                table_df = baseline_df.reset_index(drop=True)
        else:
            # Hiç seçim yoksa sadece baseline
            table_df = baseline_df.reset_index(drop=True)

        # Gerekli sütunları seç ve işle
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
        
        # Filter uygula
        # Filter uygula - INSTANCE FILTER SUPPORT EKLENDI
        if filters:
            if isinstance(filters, dict):
                for column, filter_value in filters.items():
                    if column == 'instance_name':
                        # INSTANCE NAME İÇİN ÖZEL FİLTRELEME
                        if isinstance(filter_value, dict) and filter_value.get('type') == 'instance_range':
                            min_instance = filter_value.get('min', 1)
                            max_instance = filter_value.get('max', 9999)
                            
                            # Instance name'den numarayı çıkar ve filtrele
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
                        # DİĞER PARAMETRELER İÇİN NORMAL FİLTRELEME
                        if isinstance(filter_value, list) and len(filter_value) == 2:
                            min_val, max_val = filter_value
                            table_df = table_df[
                                (table_df[column] >= min_val) & 
                                (table_df[column] <= max_val)
                            ]

        # SIRALAMADA BASELINE'I EN ÜSTTE TUT
        if sort_by and len(sort_by) > 0:
            sort_column = sort_by[0]['column_id']
            sort_direction = sort_by[0]['direction']
            
            print(f"OPT SORTING: column={sort_column}, direction={sort_direction}")
            
            if sort_column in table_df.columns:
                ascending = (sort_direction == 'asc')
                
                # Baseline'ı her zaman üstte tutmak için özel sıralama
                baseline_rows = table_df[table_df['instance_name'] == 'Baseline']
                other_rows = table_df[table_df['instance_name'] != 'Baseline']
                
                if not other_rows.empty:
                    if sort_column == 'instance_name':
                        # Instance name için özel sıralama (S1, S2, S3...)
                        other_rows['sort_key'] = other_rows['instance_name'].str.extract(r'S(\d+)').astype(int)
                        other_rows = other_rows.sort_values('sort_key', ascending=ascending)
                        other_rows = other_rows.drop('sort_key', axis=1)
                    else:
                        # Diğer sütunlar için normal sıralama
                        other_rows = other_rows.sort_values(sort_column, ascending=ascending)
                
                # Baseline + sıralanmış diğerleri
                table_df = pd.concat([baseline_rows, other_rows]).reset_index(drop=True)

        # Pagination ayarları
        page_size = 10
        page_current = page_current if page_current is not None else 0
        total_rows = len(table_df)
        
        # Sayfalama uygula
        start_index = page_current * page_size
        end_index = start_index + page_size
        paginated_data = table_df.iloc[start_index:end_index]
        
        # Table info metni
        if total_rows == 0:
            table_info = "No instances found"
        else:
            start_item = start_index + 1
            end_item = min(end_index, total_rows)
            table_info = f"Showing {start_item}-{end_item} of {total_rows} instances"
        
        # Dictionary formatına çevir ve FLOATING POINT FORMATLAMA
        table_data = []
        for _, row in paginated_data.iterrows():
            formatted_row = {}
            for col in row.index:
                if col in ['instance_name', 'instance_id']:
                    # String ve ID sütunları aynen kalsın
                    formatted_row[col] = row[col]
                elif pd.api.types.is_numeric_dtype(type(row[col])):
                    # Numeric sütunları 2 ondalık haneye yuvarla
                    try:
                        formatted_row[col] = round(float(row[col]), 2)
                    except (ValueError, TypeError):
                        formatted_row[col] = row[col]
                else:
                    formatted_row[col] = row[col]
            table_data.append(formatted_row)
        
        # Sayfadaki tüm satırları seç
        selected_rows_on_page = list(range(len(table_data)))

        print(f"OPT TABLE: Returning {len(table_data)} rows, total_rows={total_rows}")
        return table_data, table_info, selected_rows_on_page
        
    except Exception as e:
        print(f"Error in update_table_data_optimized: {e}")
        import traceback
        traceback.print_exc()
        return [], "Error loading data", []


@callback(
    [Output("opt-instance-table", "page_current"),
     Output("opt-table-current-page", "children"),
     Output("opt-table-total-pages", "children"),
     Output("opt-table-first-page-btn", "disabled"),
     Output("opt-table-prev-page-btn", "disabled"),
     Output("opt-table-next-page-btn", "disabled"),
     Output("opt-table-last-page-btn", "disabled")],
    [Input("opt-table-first-page-btn", "n_clicks"),
     Input("opt-table-prev-page-btn", "n_clicks"),
     Input("opt-table-next-page-btn", "n_clicks"),
     Input("opt-table-last-page-btn", "n_clicks"),
     Input("opt-table-search-input", "value"),
     Input("opt-table-filters", "data"),
     Input('opt-scatter-plot', 'selectedData'),
     Input('opt-selected-instances-store', 'data')],
    [State("opt-instance-table", "page_current")],
    prevent_initial_call=False
)
def handle_manual_pagination_optimized(first_clicks, prev_clicks, next_clicks, last_clicks,
                                   search_value, filters, selectedData, selected_instances, current_page):
    """Manuel pagination for optimized page"""

    try:
        print("OPT PAGINATION: optimized callback çalışıyor")
        print(f"OPT PAGINATION DEBUG: filters type = {type(filters)}, value = {filters}")

        ctx = callback_context

        df, df_with_id = get_cached_data()

        # Veriyi hazırla
        table_df = df.copy()
        table_df['instance_name'] = 'S' + (table_df.index + 1).astype(str)

        # Seçili instance'ları belirle
        selected_ids = set()

        # Scatter plot'tan seçilenler
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

        # Dropdown'dan seçilenler
        if selected_instances:
            selected_ids.update(selected_instances)

        if selected_ids:
            mask = table_df.index.isin([id-1 for id in selected_ids])
            table_df = table_df[mask]
            print(f"OPT PAGINATION: {len(selected_ids)} instance seçili, {len(table_df)} satır filtrelendi")
        else:
            table_df = table_df.iloc[0:0]
            print("OPT PAGINATION: Hiç seçim yok, pagination için boş tablo kullanılıyor.")

        # Search filtering uygula
        if search_value:
            try:
                search_num = int(search_value)
                search_name = f'S{search_num}'
                table_df = table_df[table_df['instance_name'].str.contains(search_name, case=False, na=False)]
            except (ValueError, TypeError):
                search_str = str(search_value).lower()
                mask = table_df.astype(str).apply(lambda x: x.str.lower().str.contains(search_str, na=False)).any(axis=1)
                table_df = table_df[mask]

        # Filter uygula
        if filters:
            print(f"OPT FILTER DEBUG: Processing filters: {filters}")
            
            if isinstance(filters, list):
                print("OPT FILTER WARNING: filters is a list, converting to dict")
                filters = {}
            elif not isinstance(filters, dict):
                print(f"OPT FILTER WARNING: filters is not dict or list, type: {type(filters)}")
                filters = {}
            
            for column, filter_value in filters.items():
                if column in table_df.columns:
                    print(f"OPT FILTER DEBUG: Applying filter for {column}: {filter_value}")
                    
                    if isinstance(filter_value, list) and len(filter_value) == 2:
                        min_val, max_val = filter_value
                        print(f"OPT FILTER DEBUG: Range filter {column}: {min_val} - {max_val}")
                        table_df = table_df[
                            (table_df[column] >= min_val) & 
                            (table_df[column] <= max_val)
                        ]
                    elif isinstance(filter_value, dict):
                        if filter_value.get('type') == 'range':
                            min_val = filter_value.get('min')
                            max_val = filter_value.get('max')
                            if min_val is not None:
                                table_df = table_df[table_df[column] >= min_val]
                            if max_val is not None:
                                table_df = table_df[table_df[column] <= max_val]
                    else:
                        print(f"OPT FILTER WARNING: Unknown filter format for {column}: {filter_value}")

        # Toplam sayfa sayısını filtrelenmiş veri üzerinden hesapla
        page_size = 10
        total_rows = len(table_df)
        total_pages = max(1, (total_rows + page_size - 1) // page_size)

        print(f"OPT PAGINATION: {total_rows} toplam satır, {total_pages} sayfa")

        # Varsayılan değerler
        new_page = current_page if current_page is not None else 0

        # Search, filter, veya seçim değiştiğinde ilk sayfaya dön
        if ctx.triggered:
            triggered_prop = ctx.triggered[0]["prop_id"]

            if ("opt-table-search-input" in triggered_prop or
                "opt-table-filters" in triggered_prop or
                "opt-scatter-plot.selectedData" in triggered_prop or
                "opt-selected-instances-store" in triggered_prop):
                new_page = 0
            elif "opt-table-first-page-btn" in triggered_prop and first_clicks:
                new_page = 0
            elif "opt-table-prev-page-btn" in triggered_prop and prev_clicks:
                new_page = max(0, current_page - 1)
            elif "opt-table-next-page-btn" in triggered_prop and next_clicks:
                new_page = min(total_pages - 1, current_page + 1)
            elif "opt-table-last-page-btn" in triggered_prop and last_clicks:
                new_page = total_pages - 1

        # Sayfa numarasını sınırla
        new_page = max(0, min(new_page, total_pages - 1))

        # Ayrı sayfa bilgileri
        current_page_display = str(new_page + 1)
        total_pages_display = str(total_pages)

        # Buton durumları
        first_disabled = (new_page == 0)
        prev_disabled = (new_page == 0)
        next_disabled = (new_page >= total_pages - 1)
        last_disabled = (new_page >= total_pages - 1)

        print(f"OPT PAGINATION: Sayfa {new_page + 1}/{total_pages}")

        return (new_page, current_page_display, total_pages_display,
                first_disabled, prev_disabled, next_disabled, last_disabled)

    except Exception as e:
        print(f"Error in handle_manual_pagination_optimized: {e}")
        import traceback
        traceback.print_exc()
        return 0, "1", "1", True, True, True, True


@callback(
    Output('opt-selected-instances-store', 'data', allow_duplicate=True),
    Input('opt-instance-table', 'selected_rows'),
    [State('opt-instance-table', 'data'),
     State('opt-selected-instances-store', 'data')],
    prevent_initial_call=True
)
def update_selection_from_table_optimized(selected_rows, table_data, current_selected):
    """Update instance selection based on table row selection for optimized page"""
    
    if not selected_rows or not table_data:
        return current_selected or []
    
    # Tablodan seçilen instance ID'lerini al
    table_selected = []
    for row_idx in selected_rows:
        if row_idx < len(table_data):
            instance_id = table_data[row_idx].get('instance_id')
            if instance_id:
                table_selected.append(instance_id)
    
    # Mevcut seçimle birleştir (maksimum 4 instance)
    all_selected = list(set((current_selected or []) + table_selected))
    
    # 4 instance limiti
    if len(all_selected) > 4:
        all_selected = all_selected[:4]
    
    return all_selected


# optimized_comparison_callbacks.py dosyasındaki update_filter_chips fonksiyonunu bu şekilde düzeltin:

@callback(
    Output('opt-filter-chips-container', 'children'),
    Input('opt-table-filters', 'data'),
    prevent_initial_call=False
)
def update_filter_chips(filters):
    """Display active filters as chips - INSTANCE FILTER SUPPORT - FIXED REMOVE BUTTONS"""
    
    print(f"OPT FILTER CHIPS DEBUG: filters = {filters}, type = {type(filters)}")
    
    if not filters:
        return []
    
    if isinstance(filters, list):
        print("OPT FILTER CHIPS WARNING: filters is a list, converting to dict")
        return []
    elif not isinstance(filters, dict):
        print(f"OPT FILTER CHIPS WARNING: filters is not dict, type: {type(filters)}")
        return []
    
    chips = []
    
    # Filtre adları mapping
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
        
        # INSTANCE NAME İÇİN ÖZEL GÖRÜNTÜLEME
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
            # Eski format için uyumluluk
            min_val = filter_value.get('min', 0)
            max_val = filter_value.get('max', 100)
            chip_text = f"{display_name}: {min_val:.2f} - {max_val:.2f}"
        else:
            print(f"OPT FILTER CHIPS WARNING: Unknown filter format for {column}: {filter_value}")
            continue
        
        # Chip oluştur - DÜZELTİLDİ: opt-remove-filter kullanılıyor
        chip = dbc.Badge(
            [
                chip_text,
                html.Span(" ×",
                    id={"type": "opt-remove-filter", "index": column},  # DÜZELTİLDİ: opt-remove-filter
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
    
    print(f"OPT FILTER CHIPS: Created {len(chips)} chips")
    return chips


@callback(
    Output('opt-table-filters', 'data'),
    Input({"type": "opt-remove-filter", "index": dash.ALL}, 'n_clicks'),
    State('opt-table-filters', 'data'),
    prevent_initial_call=True
)
def remove_filter_optimized(n_clicks_list, current_filters):
    """Remove filter when X is clicked for optimized page"""
    
    if not ctx.triggered or not current_filters:
        raise PreventUpdate
    
    triggered = ctx.triggered[0]
    if triggered['value'] is None:
        raise PreventUpdate
    
    prop_id = triggered['prop_id']
    import json
    button_info = json.loads(prop_id.split('.')[0])
    filter_to_remove = button_info['index']
    
    # Filtreyi kaldır
    new_filters = current_filters.copy()
    if filter_to_remove in new_filters:
        del new_filters[filter_to_remove]
    
    return new_filters


@callback(
    Output('opt-download-instances', 'data'),
    Input('opt-export-selected-btn', 'n_clicks'),
    [State('opt-scatter-plot', 'selectedData'),
     State('opt-selected-instances-store', 'data'),
     State('opt-table-search-input', 'value'),
     State('opt-table-filters', 'data')],
    prevent_initial_call=True
)
def export_selected_instances_optimized(n_clicks, selectedData, selected_instances, search_value, filters):
    """Export ALL filtered instances to CSV for optimized page - not just current page"""
    
    if not n_clicks:
        raise PreventUpdate
    
    try:
        df, _ = get_cached_data()
        
        # Veriyi hazırla - TÜM VERİ ile başla
        table_df = df.copy()
        table_df['instance_name'] = 'S' + (table_df.index + 1).astype(str)
        
        # Seçili instance'ları belirle
        selected_ids = set()
        
        # Scatter plot'tan seçilenler
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
        
        # Dropdown'dan seçilenler
        if selected_instances:
            selected_ids.update(selected_instances)
        
        if not selected_ids:
            # Hiç seçim yoksa boş export
            return dash.no_update
        
        # Seçili instance'ları filtrele
        mask = table_df.index.isin([id-1 for id in selected_ids])
        table_df = table_df[mask]
        
        # Gerekli sütunları seç
        required_columns = [
            'instance_name', 'transmittance', 'window_shgc', 
            'window_u', 'roof_u', 'wall_u', 'cooling_load', 'heating_load'
        ]
        
        for col in required_columns:
            if col not in table_df.columns and col != 'instance_name':
                table_df[col] = 0.0
        
        available_columns = [col for col in required_columns if col in table_df.columns]
        table_df = table_df[available_columns]
        
        # Search filtering uygula - AYNI FİLTRELEME
        if search_value:
            try:
                search_num = int(search_value)
                search_name = f'S{search_num}'
                table_df = table_df[table_df['instance_name'].str.contains(search_name, case=False, na=False)]
            except (ValueError, TypeError):
                search_str = str(search_value).lower()
                mask = table_df.astype(str).apply(lambda x: x.str.lower().str.contains(search_str, na=False)).any(axis=1)
                table_df = table_df[mask]
        
        # Filter uygula - AYNI FİLTRELEME
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
                        elif isinstance(filter_value, dict):
                            if filter_value.get('type') == 'range':
                                min_val = filter_value.get('min')
                                max_val = filter_value.get('max')
                                if min_val is not None:
                                    table_df = table_df[table_df[column] >= min_val]
                                if max_val is not None:
                                    table_df = table_df[table_df[column] <= max_val]
        
        if table_df.empty:
            return dash.no_update
        
        # Sütun adlarını düzenle
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
        
        # CSV olarak indir
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"LUX_OptimizedSolutions_{timestamp}.csv"
        
        print(f"OPT EXPORT: Exporting {len(export_df)} instances (filtered from {len(df)} total)")
        
        return dcc.send_data_frame(export_df.to_csv, filename, index=False)
        
    except Exception as e:
        print(f"Optimized export error: {e}")
        import traceback
        traceback.print_exc()
        return dash.no_update


# ==========================================
# FILTER DROPDOWN CALLBACKS - OPTIMIZED PAGE
# ==========================================

@callback(
    [Output('opt-filter-dropdown-menu', 'style'),
     Output('opt-filter-dropdown-open', 'data'),
     Output('opt-add-filter-trigger-btn', 'className')],
    [Input('opt-add-filter-trigger-btn', 'n_clicks')],
    [State('opt-filter-dropdown-open', 'data')],
    prevent_initial_call=True
)
def toggle_filter_dropdown_optimized(n_clicks, is_open):
    """Toggle filter dropdown visibility for optimized page"""
    
    if n_clicks:
        new_state = not is_open
        
        if new_state:
            # Dropdown açık - göster ve buton stilini değiştir
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
            # Dropdown kapalı - gizle ve buton stilini normale döndür
            style = {"display": "none"}
            button_class = "add-filter-trigger"
            
        return style, new_state, button_class
    
    raise PreventUpdate


@callback(
    [Output('opt-filter-step-1', 'style'),
     Output('opt-filter-step-2', 'style'),
     Output('opt-filter-current-step', 'data')],
    [Input({"type": "param-selector", "param": dash.ALL}, 'n_clicks'),
     Input('opt-filter-back-btn', 'n_clicks')],
    [State('opt-filter-current-step', 'data')],
    prevent_initial_call=True
)
def handle_filter_step_navigation_optimized(param_clicks, back_clicks, current_step):
    """Handle navigation between filter steps for optimized page"""
    
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    triggered_id = ctx.triggered[0]['prop_id']
    
    # Back button clicked - go to step 1
    if 'opt-filter-back-btn' in triggered_id:
        return (
            {"display": "block"},    # Show step 1
            {"display": "none"},     # Hide step 2
            1                        # Set step to 1
        )
    
    # Parameter selected - go to step 2
    elif 'param-selector' in triggered_id:
        return (
            {"display": "none"},     # Hide step 1
            {"display": "block"},    # Show step 2
            2                        # Set step to 2
        )
    
    raise PreventUpdate


@callback(
    [Output('opt-filter-selected-param', 'data'),
     Output('opt-filter-min-input', 'placeholder'),
     Output('opt-filter-max-input', 'placeholder')],
    [Input({"type": "param-selector", "param": dash.ALL}, 'n_clicks')],
    [State({"type": "param-selector", "param": dash.ALL}, 'id')],
    prevent_initial_call=True
)
def handle_parameter_selection(n_clicks_list, param_ids):
    """Handle parameter selection and update input placeholders - INSTANCE FILTER SUPPORT"""
    
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    # Hangi parametreye tıklandığını bul
    triggered_prop = ctx.triggered[0]['prop_id']
    
    # JSON parse ederek param değerini al
    import json
    try:
        param_info = json.loads(triggered_prop.split('.')[0])
        selected_param = param_info['param']
    except:
        raise PreventUpdate
    
    # DataFrame'den min/max değerleri al
    df, _ = get_cached_data()
    
    # INSTANCE NAME İÇİN ÖZEL DURUM
    if selected_param == 'instance_name':
        # Instance için özel placeholder'lar
        min_placeholder = "1"  # S1 için
        max_placeholder = "Enter max instance number (e.g. 100)"
        return selected_param, min_placeholder, max_placeholder
    
    if selected_param not in df.columns:
        raise PreventUpdate
    
    min_val = float(df[selected_param].min())
    max_val = float(df[selected_param].max())
    
    # Parameter adı ve birim bilgileri
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
    [Output('opt-table-filters', 'data', allow_duplicate=True),
     Output('opt-filter-dropdown-menu', 'style', allow_duplicate=True),
     Output('opt-filter-dropdown-open', 'data', allow_duplicate=True),
     Output('opt-add-filter-trigger-btn', 'className', allow_duplicate=True)],
    [Input('opt-filter-apply-btn', 'n_clicks')],
    [State('opt-filter-selected-param', 'data'),
     State('opt-filter-min-input', 'value'),
     State('opt-filter-max-input', 'value'),
     State('opt-table-filters', 'data')],
    prevent_initial_call=True
)
def apply_filter_from_dropdown(n_clicks, selected_param, min_val, max_val, current_filters):
    """Apply the selected filter and close dropdown - INSTANCE FILTER SUPPORT"""
    
    if not n_clicks or not selected_param:
        raise PreventUpdate
    
    if min_val is None or max_val is None:
        raise PreventUpdate
    
    # Yeni filtreyi ekle
    new_filters = current_filters.copy() if current_filters else {}
    
    # INSTANCE NAME İÇİN ÖZEL İŞLEM
    if selected_param == 'instance_name':
        # Instance için özel format: min ve max instance numaraları
        new_filters[selected_param] = {
            'type': 'instance_range',
            'min': int(min_val),
            'max': int(max_val)
        }
    else:
        # Diğer parametreler için normal list format
        new_filters[selected_param] = [float(min_val), float(max_val)]
    
    # Dropdown'ı kapat ve buton stilini normale döndür
    closed_style = {"display": "none"}
    button_class = "add-filter-trigger"
    
    return new_filters, closed_style, False, button_class


# CLİENTSİDE CALLBACK - Dışarı tıklama ile dropdown'ı kapatmak için
clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0 && !window.optFilterDropdownClickListener) {
            setTimeout(function() {
                document.addEventListener('click', function(e) {
                    const trigger = document.getElementById('opt-add-filter-trigger-btn');
                    const menu = document.getElementById('opt-filter-dropdown-menu');
                    
                    if (trigger && menu && 
                        !trigger.contains(e.target) && 
                        !menu.contains(e.target)) {
                        
                        if (menu.style.display === 'block') {
                            menu.style.display = 'none';
                            
                            // Buton stilini normale döndür
                            trigger.className = 'add-filter-trigger';
                            
                            // Dash state'i güncelle
                            if (window.dash_clientside && window.dash_clientside.set_props) {
                                try {
                                    window.dash_clientside.set_props('opt-filter-dropdown-open', {data: false});
                                } catch (error) {
                                    console.error('Error closing opt filter dropdown:', error);
                                }
                            }
                        }
                    }
                }, { passive: true });
                
                window.optFilterDropdownClickListener = true;
                console.log('Opt Filter dropdown outside click listener attached');
            }, 50);
        }
        return 'attached';
    }
    """,
    Output('opt-add-filter-trigger-btn', 'data-click-listener'),
    Input('opt-add-filter-trigger-btn', 'n_clicks'),
    prevent_initial_call=True
)