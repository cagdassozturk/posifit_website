import dash
import pandas as pd
from utils.plots import load_all_data
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate
import time
import threading  # BU EKLENDİ - Threading için
import re  # BU EKLENDİ - Regex için
from pages.explorer import df
from dash import callback, Output, Input, ctx, html, dcc, State, clientside_callback, callback_context

# ==========================================
# PERFORMANCE OPTIMIZATIONS
# ==========================================

# 1. Cache the data - load once, use everywhere
_cached_data = None
_cached_df_with_id = None

def get_cached_data():
    """Load data once and cache it"""
    global _cached_data, _cached_df_with_id
    if _cached_data is None:
        _cached_data = load_all_data()
        _cached_df_with_id = _cached_data.copy()
        _cached_df_with_id['ID'] = _cached_df_with_id.index + 1
    return _cached_data, _cached_df_with_id

def get_selectable_data():
    """Get data excluding baseline for user selection"""
    df, df_with_id = get_cached_data()
    # Exclude baseline (first row) from selectable instances
    selectable_df = df_with_id[df_with_id.index > 0].copy()
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
# DÜZELTME 1: VIRTUAL CONTENT UPDATE - CHECKBOX STATE İYİLEŞTİRMESİ
# ==========================================

# 4. Virtual content callback'inin cache kontolünü optimize edin

# ==========================================
# DÜZELTME: VIRTUAL CONTENT UPDATE - SİMPLİFİED
# ==========================================

@callback(
    [Output('virtual-scroll-container', 'children'),
     Output('virtual-scroll-position', 'data')],
    [Input('virtual-scroll-container', 'scrollTop'),
     Input('comparison-selected-instances-store', 'data'),
     Input('sort-by-dropdown', 'value'),
     Input('sort-order-radio', 'value'),
     Input('virtual-scroll-position', 'data')],
    [State('virtual-item-height', 'data'),
     State('virtual-container-height', 'data')],
    prevent_initial_call=False
)
def update_virtual_content_combined(scroll_top_prop, selected_instances, sort_by, sort_order, scroll_position_data, item_height, container_height):
    """DÜZELTME: Simplified virtual scrolling - hata düzeltmeleri"""
    
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
        
        # Cache key - basitleştirildi
        selected_key = "_".join(map(str, sorted(selected_set))) if selected_set else "none"
        scroll_group = int(scroll_top / (item_height * 5))  # 3'ten 5'e geri döndü - daha stabil
        cache_key = f"{scroll_group}_{selected_key}_{sort_by}_{sort_order}"
        
        triggered_id = ctx.triggered_id
        
        # Cache kontrolü - basitleştirildi
        if cache_key in _dropdown_cache and triggered_id != 'selected-instances-store':
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
        buffer = 20  # 15'ten 20'ye artırıldı - daha fazla item yükle
        items_per_view = max(1, int(container_height / item_height))  # ~8 item
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
            unique_checkbox_id = f"virtual-checkbox-{instance_id}-{scroll_group}"
            
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
                            id={"type": "virtual-checkbox", "index": instance_id, "unique": unique_checkbox_id},
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
                id=f"virtual-item-{instance_id}",
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
        
        # Cache yönetimi - basitleştirildi
        if len(_dropdown_cache) > 50:  # Cache boyutunu artır
            # En eski 25'ini sil
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


# YENİ CALLBACK: Uyarı overlay'ini yönetmek için
@callback(
    [Output('warning-overlay', 'children'),
     Output('warning-overlay', 'style')],
    Input('selection-warning-state', 'data'),
    [State('dropdown-open-state', 'data')],
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
        # Dropdown açıkken: dropdown'ın altına konumlandır
        top_position = "calc(100% + 320px + 12px)"  # trigger + dropdown height + margin
    else:
        # Dropdown kapalıyken: trigger'ın altına konumlandır
        top_position = "calc(100% + 8px)"
    
    # Görünür stil
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
        "opacity": "1",  # Görünür yap
        "animation": "fadeInWarning 0.3s ease-out"
    }
    
    return warning_content, visible_style



# ==========================================
# DÜZELTME 2: SELECTION HANDLING - 4 INSTANCE LİMİTİ
# ==========================================

# ESKİ CALLBACK'İ BOŞALTMİAK
@callback(
    Output('selection-warning-area', 'children'),
    Input('selection-warning-state', 'data'),
    prevent_initial_call=False
)
def update_warning_area_placeholder(warning_state):
    """Eski uyarı alanı artık kullanılmıyor - boş dön"""
    return html.Div()  # Boş div döndür


# YENİ CALLBACK: Dropdown state değiştiğinde uyarı pozisyonunu güncelle
@callback(
    Output('warning-overlay', 'style', allow_duplicate=True),
    Input('dropdown-open-state', 'data'),
    [State('selection-warning-state', 'data'),
     State('warning-overlay', 'style')],
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
        current_style["top"] = "calc(100% + 320px + 12px)"  # Dropdown'ın altı
    else:
        current_style["top"] = "calc(100% + 8px)"  # Trigger'ın altı
    
    return current_style
    
    
# 1. handle_selection_and_search_with_warning callback'inde cache temizleme işlemini erteleyin

# ==========================================
# SELECTION HANDLING - DÜZELTİLMİŞ
# ==========================================

@callback(
    [Output('comparison-selected-instances-store', 'data'),
     Output('selection-warning-state', 'data')],
    [Input({"type": "virtual-checkbox", "index": dash.ALL, "unique": dash.ALL}, 'value'),
     Input('search-input', 'n_submit')],
    [State({"type": "virtual-checkbox", "index": dash.ALL, "unique": dash.ALL}, 'id'),
     State('comparison-selected-instances-store', 'data'),
     State('search-input', 'value')],
    prevent_initial_call=True
)
def handle_selection_and_search_with_warning(all_values, n_submit, all_ids, current_selected, search_value):
    """DÜZELTME: Simplified selection handling"""
    
    if current_selected is None:
        current_selected = []
    
    triggered_id = ctx.triggered_id
    warning_state = {"show": False, "message": ""}
    
    # Handle search input
    # comparison_callbacks.py dosyasındaki handle_selection_and_search_with_warning fonksiyonunda
    # Handle search input kısmını bu şekilde değiştirin:

    if triggered_id == 'search-input' and n_submit and search_value is not None:
        try:
            # Kullanıcıdan gelen değeri doğrudan display ID olarak kabul et
            display_id = int(search_value)  # Kullanıcı S44 için 44 girer
            instance_id = display_id + 1    # Internal ID = display_id + 1
            
            # ID aralığını kontrol et (S1-S4320 için display_id 1-4320 olmalı)
            if 1 <= display_id <= 4320:
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
                    print(f"SEARCH: Added S{display_id} (ID:{instance_id}), total selected: {len(new_selected)}")
                
                # Clear cache with delay - simplified
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
    
    # Handle checkbox selection
    if all_values and all_ids:
        try:
            triggered_info = ctx.triggered[0] if ctx.triggered else None
            if not triggered_info:
                raise PreventUpdate
                
            prop_id = triggered_info.get('prop_id', '')
            if 'virtual-checkbox' not in prop_id:
                raise PreventUpdate
            
            # Extract instance ID from prop_id
            match = re.search(r'"index":(\d+)', prop_id)
            if not match:
                raise PreventUpdate
                
            changed_instance_id = int(match.group(1))
            print(f"SELECTION: Processing change for S{changed_instance_id}")
            
            # Find checkbox state
            is_now_checked = False
            for i, values in enumerate(all_values):
                if all_ids[i]["index"] == changed_instance_id:
                    is_now_checked = bool(values and len(values) > 0)
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
                print(f"SELECTION: Added S{changed_instance_id} (Total: {len(new_selected)})")
                    
            elif not is_now_checked and changed_instance_id in new_selected:
                # Removing instance
                new_selected.remove(changed_instance_id)
                print(f"SELECTION: Removed S{changed_instance_id} (Total: {len(new_selected)})")
            
            # Check if state changed
            if set(new_selected) != set(current_selected):
                print(f"SELECTION: Updated from {current_selected} to {new_selected}")
                
                # Clear cache with delay
                def delayed_cache_clear():
                    time.sleep(0.1)
                    global _dropdown_cache
                    _dropdown_cache.clear()
                    print("SELECTION: Cache cleared for checkbox update")
                
                threading.Thread(target=delayed_cache_clear, daemon=True).start()
                
                return new_selected, warning_state
        
        except Exception as e:
            print(f"Selection error: {e}")
            import traceback
            traceback.print_exc()
    
    return current_selected, warning_state


# ==========================================
# DÜZELTME 3: DROPDOWN STATE MANAGEMENT
# ==========================================

# DROPDOWN STATE CALLBACK'İNİ GÜNCELLE
@callback(
    [Output('virtual-scroll-container', 'style'),
     Output('dropdown-open-state', 'data'),
     Output('virtual-dropdown-trigger', 'children')],
    [Input('virtual-dropdown-trigger', 'n_clicks'),
     Input('comparison-selected-instances-store', 'data')],
    [State('dropdown-open-state', 'data')],
    prevent_initial_call=True
)
def handle_dropdown_state_combined(n_clicks, selected_instances, is_open):
    """GÜNCELLEME: Dropdown toggle + 320px yükseklik"""
    
    triggered_id = ctx.triggered_id
    
    # Handle dropdown toggle
    if triggered_id == 'virtual-dropdown-trigger' and n_clicks:
        new_state = not is_open if is_open is not None else True
        
        # YENİ: 320px yükseklik
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
    if triggered_id == 'selected-instances-store':
        current_style = {
            "display": "block" if is_open else "none",
            "height": "320px",
            "maxHeight": "320px",
            "minHeight": "320px"
        } if is_open else {"display": "none"}
        trigger_text = get_trigger_text(selected_instances)
        return current_style, is_open, trigger_text
    
    raise PreventUpdate
    
    
# YENİ CLİENTSİDE CALLBACK: Container class'ını yönet
clientside_callback(
    """
    function(dropdown_open, warning_show) {
        const container = document.querySelector('.enhanced-dropdown-container');
        
        if (container) {
            // Container class'larını temizle
            container.classList.remove('dropdown-open', 'warning-active');
            
            // Duruma göre class'ları ekle
            if (dropdown_open) {
                container.classList.add('dropdown-open');
                console.log('Added dropdown-open class');
            }
            
            if (warning_show && warning_show.show) {
                container.classList.add('warning-active');
                console.log('Added warning-active class');
            }
            
            // Dropdown açıkken ve uyarı varsa ek margin ekle
            if (dropdown_open && warning_show && warning_show.show) {
                container.style.marginBottom = '140px';
            } else if (dropdown_open) {
                container.style.marginBottom = '120px';
            } else {
                container.style.marginBottom = '16px';
            }
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('virtual-dropdown-trigger', 'data-container-class'),
    [Input('dropdown-open-state', 'data'),
     Input('selection-warning-state', 'data')],
    prevent_initial_call=True
)
def get_trigger_text(selected_instances):
    """DÜZELTİLMİŞ: S2,S3,S4... yerine S1,S2,S3... göster"""
    if not selected_instances or len(selected_instances) == 0:
        return "Select instances..."
    
    # Instance ID'lerini display ID'lerine çevir (S2->S1, S3->S2, vb.)
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

# 4. SEARCH TOGGLE CALLBACK (UNCHANGED)
@callback(
    [Output('search-input-container', 'className'),
     Output('search-toggle-state', 'data'),
     Output('search-input', 'value'),
     Output('search-toggle-button', 'className')],
    [Input('search-toggle-button', 'n_clicks'),
     Input('search-input', 'n_submit')],
    [State('search-toggle-state', 'data'),
     State('search-input', 'value')],
    prevent_initial_call=True
)
def handle_search_toggle_combined(toggle_clicks, submit_count, is_open, search_value):
    """Handle search visibility and button styling"""
    
    triggered_id = ctx.triggered_id
    
    if triggered_id == 'search-toggle-button':
        current_state = is_open if is_open is not None else False
        new_state = not current_state
        
        container_class = "search-input-container" if new_state else "search-input-container hidden"
        button_class = "search-toggle-button search-open" if new_state else "search-toggle-button"
        
        return container_class, new_state, dash.no_update, button_class

    if triggered_id == 'search-input' and search_value:
        return "search-input-container hidden", False, "", "search-toggle-button"
            
    raise PreventUpdate

# ==========================================
# PARAMETER UPDATE (UNCHANGED)
# ==========================================

# ==========================================
# PARAMETER UPDATE (BASELINE DESTEĞI EKLENDİ)
# ==========================================

# comparison_callbacks.py dosyasındaki update_instance_parameters_optimized fonksiyonunu güncelleyin

@callback(
    Output('instance-parameters', 'children'),
    Input('comparison-selected-instances-store', 'data'),
    prevent_initial_call=False
)
def update_instance_parameters_optimized(selected_instances):
    """Optimized parameter updates with caching - Baseline desteği eklendi"""
    
    df, _ = get_cached_data()
    
    # Eğer hiçbir instance seçilmemişse baseline'ı göster
    if not selected_instances or len(selected_instances) == 0:
        selected_id = 1  # Baseline (first row, but ID starts from 1)
        baseline_mode = True
    else:
        selected_id = selected_instances[0]
        baseline_mode = False
    
    # Cache key'e baseline durumu da dahil et
    cache_key = f"{selected_id}_baseline_{baseline_mode}"
    
    # Check cache first
    if cache_key in _param_cache:
        return _param_cache[cache_key]
    
    if selected_id > len(df):
        return "Invalid instance."
    
    row = df.iloc[selected_id - 1]

    # GÜNCELLENMIŞ param_card fonksiyonu - baseline ve parametre kontrolü eklenmiş
    def param_card(label, val, min_val, max_val, unit="", is_baseline=False, param_name=""):
        # Baseline için Transmittance özel durumu
        if is_baseline and param_name == "transmittance":
            value_text = "N/A"
            percent = 0  # Progress bar için 0% göster
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
                        "color": "#6C757D" if value_text == "N/A" else "#333",  # N/A için gri renk
                        "fontStyle": "italic" if value_text == "N/A" else "normal"  # N/A için italik
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
        display_id = selected_id - 1  # S2 -> S1, S3 -> S2, vb.
        title_text = f"Parameters for S{display_id}:"
        title_color = "#4E5E66"

    # GÜNCELLENMIŞ param_card çağrıları - baseline_mode ve param_name parametreleri eklendi
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
# COMPARISON UPDATE - 4 INSTANCE DESTEĞI (CLEAR BUTONLARI KALDIRILDI)
# ==========================================

# comparison_callbacks.py DOSYASINDAKİ MEVCUT FONKSİYONUN YERİNE BUNU EKLEYİN

@callback(
    Output('instance-comparison-content', 'children'),
    Input('comparison-selected-instances-store', 'data'),  # Sadece dropdown seçimini dinle
    prevent_initial_call=False
)
def update_instance_comparison_optimized(selected_instances):
    """
    Instance comparison table - SON GÜNCELLEME:
    - 0 ve 1 instance durumu için 'justify-content' kullanan, daha sağlam bir dikey ortalama eklendi.
    - Spacer div'leri kaldırıldı, mantık basitleştirildi.
    """
    df, _ = get_cached_data()
    n = len(df)
    
    # Scenario sütunundaki ilk satır (index 0) baseline
    baseline_idx = 0  # İlk satır baseline
    baseline_row = df.iloc[baseline_idx]
    
    metrics = [
        ("Heating Ideal Load", "kWh", "heating_load", "heating.png", "heating-icon-bg"),
        ("Cooling Ideal Load", "kWh", "cooling_load", "cooling.png", "cooling-icon-bg"),
        ("Carbon Emission", "CO₂e/kWh", "co2", "co2.png", "co2-icon-bg"),
    ]

    # --- YARDIMCI FONKSİYONLAR (Değişiklik yok) ---
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
        display_id = instance_id - 1  # S2 -> S1 dönüşümü
        return html.Div([
            html.Div([
                html.Div([
                    html.Div(instance_label, className="label-main-text"),
                    html.Div(f"S{display_id}", className="label-sub-text")  # Bu satırı değiştir
                ], style={"flex": "1", "display": "flex", "flexDirection": "column", "alignItems": "center", "justifyContent": "center"}),
                html.Button(
                    "×", 
                    id={"type": "remove-instance-btn", "index": instance_id},
                    className="remove-instance-btn",
                    title=f"Remove S{display_id}"  # Bu satırı da değiştir
                )
            ], style={"position": "relative", "width": "100%", "height": "100%", "display": "flex", "alignItems": "center", "justifyContent": "center"})
        ], className="blue-label-content")

    num_selected = len(selected_instances) if selected_instances else 0
    card_class = "instance-comparison-card"

    # --- HEADER VE BASELINE SATIRLARINI ÖNCEDEN OLUŞTURMA ---
    header_cells = [html.Div("", className="grid-cell grid-header")]
    for title, unit, _, image_file, icon_class in metrics:
        header_content = html.Div([
            html.Div(html.Img(src=f"/assets/{image_file}", className="metric-icon-image"), className=f"metric-icon-background {icon_class}"),
            html.Div([html.Div(title, className="metric-header-title"), html.Div(unit, className="metric-header-unit")], className="metric-header-text-container")
        ], className="metric-header-content")
        header_cells.append(html.Div(header_content, className="grid-cell grid-header value-cell"))

    #baseline_cells = [html.Div(html.Div([html.Div("", className="label-main-text"), html.Div("Baseline", className="label-sub-text")], className="blue-label-content"), className="grid-cell label-cell")]
    # Baseline'ı tamamen farklı yaklaşımla oluştur:
    baseline_cells = [html.Div(html.Div("Baseline", style={
        "backgroundColor": "#2AACFD",
        "color": "#FFFFFF", 
        "borderRadius": "16px",  # Tüm köşeler yuvarlak
        "padding": "20px 12px",  # Diğer kutucuklarla aynı toplam yükseklik
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

    # ==========================================================
    # YENİ VE BASİTLEŞTİRİLMİŞ MANTIK
    # ==========================================================

    # Durum 1: Hiç instance seçili değil (Sadece Baseline)
    if num_selected == 0:
        # Sadece 2 satır içeren (Header, Baseline) bir grid oluştur
        content_grid = html.Div(
            header_cells + baseline_cells,
            className="comparison-grid content-block-50" # İçeriğin %50'lik alanı kaplaması için yeni class
        )
        # Bu grid'i, dikeyde ortalama yapacak özel bir container'a koy
        return html.Div(content_grid, className=f"{card_class} comparison-layout-baseline-only", style={'height': '100%'})

    # Durum 2: 1 instance seçili
    elif num_selected == 1:
        instance_id = selected_instances[0]
        sel_row = df.iloc[instance_id - 1]
        instance_cells = [html.Div(create_instance_content_with_remove_btn("Instance 1", instance_id), className="grid-cell label-cell")]
        for _, _, col_key, _, _ in metrics:
            main_val = sel_row.get(col_key, 0)
            baseline_val = baseline_row.get(col_key, 0)
            cell_content = create_value_with_savings(main_val, baseline_val, col_key)
            instance_cells.append(html.Div(cell_content, className="grid-cell value-cell chosen-value"))
        
        # 3 satır içeren (Header, Baseline, Instance 1) bir grid oluştur
        content_grid = html.Div(
            header_cells + baseline_cells + instance_cells,
            className="comparison-grid content-block-75" # İçeriğin %75'lik alanı kaplaması için yeni class
        )
        # Bu grid'i, dikeyde ortalama yapacak özel bir container'a koy
        return html.Div(content_grid, className=f"{card_class} comparison-layout-one-instance", style={'height': '100%'})
        
    # Durum 3: 2, 3 veya 4 instance seçili (Mevcut Grid Sistemi)
    else:
        if num_selected == 2:
            grid_class = "comparison-grid"
        elif num_selected == 3:
            grid_class = "comparison-grid-4rows"
        else: # num_selected == 4
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

# YENİ CALLBACK: Remove button işlevselliği
# comparison_callbacks.py dosyasının sonuna bu callback'i ekleyin (eğer yoksa)

# YENİ CALLBACK: Remove button işlevselliği
@callback(
    Output('comparison-selected-instances-store', 'data', allow_duplicate=True),
    Input({"type": "remove-instance-btn", "index": dash.ALL}, 'n_clicks'),
    State('comparison-selected-instances-store', 'data'),
    prevent_initial_call=True
)
def handle_remove_instance_button(n_clicks_list, current_selected):
    """Handle remove instance button clicks"""
    
    print(f"DEBUG REMOVE: n_clicks_list = {n_clicks_list}")
    print(f"DEBUG REMOVE: current_selected = {current_selected}")
    
    if not ctx.triggered or not current_selected:
        print(f"DEBUG REMOVE: No trigger or no current selected")
        raise PreventUpdate
    
    # Hangi butonun tıklandığını bul
    triggered = ctx.triggered[0]
    print(f"DEBUG REMOVE: triggered = {triggered}")
    
    if triggered['value'] is None:
        print(f"DEBUG REMOVE: Triggered value is None")
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
# SYNCHRONIZATION CALLBACK
# ==========================================

@callback(
    Output('selected-instances-store', 'data', allow_duplicate=True),
    Input('comparison-selected-instances-store', 'data'),
    prevent_initial_call=True
)
def sync_comparison_to_main_store(comparison_selected):
    """Sync comparison store back to main store when instances are removed"""
    return comparison_selected

# ==========================================
# GRAPH UPDATE (4 INSTANCE DESTEĞİ)
# ==========================================

# comparison_callbacks.py dosyasındaki update_comparison_graph_optimized fonksiyonunda
# colors listesini bulun ve şu şekilde değiştirin:

@callback(
    Output('comparison-graph', 'figure'),
    Input('comparison-selected-instances-store', 'data'),
    prevent_initial_call=False  # İlk açılışta da çalışsın
)
def update_comparison_graph_optimized(selected_instances):
    """4 instance desteği ile graph updates - YENİ RENK PALETİ + BİRİMLER"""
    
    df, _ = get_cached_data()
    baseline_row = df.iloc[0]  # First row is baseline
    
    features = ['transmittance', 'window_shgc', 'window_u', 'roof_u', 'wall_u']
    
    # BİRİMLERLE GÜNCELLENMİŞ FEATURE LABELS
    feature_labels = {
        'transmittance': 'Transmittance (%)',
        'window_shgc': 'SHGC',
        'window_u': 'Window-U (W/m²K)',
        'roof_u': 'Roof-U (W/m²K)',
        'wall_u': 'Wall-U (W/m²K)'
    }
    
    display_features = [feature_labels.get(f, f) for f in features]

    def transform_value(val, feature):
        return val  # No transformation needed, transmittance is already in percentage

    baseline_vals = [transform_value(baseline_row[f], f) for f in features]
    
    # Hiçbir instance seçilmemişse sadece baseline göster
    if not selected_instances or len(selected_instances) == 0:
        fig = go.Figure(data=[
            go.Bar(
                x=display_features,
                y=baseline_vals,
                name='Baseline',
                marker_color='#011928',  # Baseline en koyu mavi
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
                itemwidth=30  # Legend kutucuk-metin arası boşluğu azalt
            ),
            yaxis=dict(showgrid=True, gridcolor='#E8E8E8', gridwidth=1, zeroline=True, zerolinecolor='#E0E0E0'),
            xaxis=dict(tickfont=dict(size=11)),
            margin=dict(t=80, b=20, l=40, r=20),
            bargap=0.6  # Tek bar olduğunda daha dar olsun
        )
        
        return fig

    # Create cache key
    cache_key = "_".join(map(str, sorted(selected_instances)))
    
    if cache_key in _graph_cache:
        return _graph_cache[cache_key]

    df, _ = get_cached_data()
    baseline_row = df.iloc[0]  # First row is baseline
    
    features = ['transmittance', 'window_shgc', 'window_u', 'roof_u', 'wall_u']
    
    # BİRİMLERLE GÜNCELLENMİŞ FEATURE LABELS
    feature_labels = {
        'transmittance': 'Transmittance (%)',
        'window_shgc': 'SHGC',  # SHGC dimensionless, birim yok
        'window_u': 'Window-U (W/m²K)',
        'roof_u': 'Roof-U (W/m²K)',
        'wall_u': 'Wall-U (W/m²K)'
    }
    
    display_features = [feature_labels.get(f, f) for f in features]

    def transform_value(val, feature):
        return val  # No transformation needed, transmittance is already in percentage

    baseline_vals = [transform_value(baseline_row[f], f) for f in features]
    
    traces = []
    
    # YENİ RENK PALETİ - Instance'lar için açıklaşan mavi tonları
    colors = ['#083D5E', '#107ABC', '#2AACFD', '#86D0FE']
    
    # Baseline trace (en koyu mavi)
    traces.append(go.Bar(
        x=display_features,
        y=baseline_vals,
        name='Baseline',
        marker_color='#011928',  # Baseline en koyu mavi
        textposition='outside',
        marker=dict(cornerradius=5),
        hovertemplate='<b>%{x}</b><br>Value: %{y:.3f}<extra></extra>'
    ))
    
    # Selected instances traces (maksimum 4 instance) - YENİ RENKLER
    for i, instance_id in enumerate(selected_instances[:4]):
        selected_row = df.iloc[instance_id - 1]
        selected_vals = [transform_value(selected_row[f], f) for f in features]
        display_id = instance_id - 1
        traces.append(go.Bar(
            x=display_features,
            y=selected_vals,
            name=f'S{display_id}',
            marker_color=colors[i % len(colors)],  # Yeni renk paleti kullanılıyor
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
            itemwidth=30  # Legend kutucuk-metin arası boşluğu azalt
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
# CLIENTSIDE CALLBACKS FOR PERFORMANCE
# ==========================================

# Scroll handler
clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            setTimeout(function() {
                const container = document.getElementById('virtual-scroll-container');
                
                if (container && !container.hasScrollListener) {
                    let scrollTimeout;
                    let lastScrollTop = 0;
                    let isScrolling = false;
                    
                    console.log('Setting up enhanced scroll listener...');
                    
                    container.addEventListener('scroll', function(e) {
                        const scrollTop = e.target.scrollTop;
                        const scrollHeight = e.target.scrollHeight;
                        const clientHeight = e.target.clientHeight;
                        
                        // DEBUG: Scroll bilgilerini logla
                        if (Math.abs(scrollTop - lastScrollTop) > 10) {
                            console.log(`SCROLL: top=${scrollTop}, height=${scrollHeight}, client=${clientHeight}`);
                        }
                        
                        // Scroll durduğunda da update yap
                        isScrolling = true;
                        
                        if (scrollTimeout) {
                            clearTimeout(scrollTimeout);
                        }
                        
                        // DÜZELTME: Daha sık update - 30ms'ye düşürüldü
                        scrollTimeout = setTimeout(function() {
                            if (Math.abs(scrollTop - lastScrollTop) > 3) {  // 5'ten 3'e düşürüldü - daha hassas
                                lastScrollTop = scrollTop;
                                
                                if (window.dash_clientside && window.dash_clientside.set_props) {
                                    try {
                                        window.dash_clientside.set_props('virtual-scroll-position', {
                                            data: scrollTop
                                        });
                                        console.log(`SCROLL UPDATE: ${scrollTop}`);
                                    } catch (error) {
                                        console.error('Error updating scroll position:', error);
                                    }
                                }
                            }
                            isScrolling = false;
                        }, 30); // 50ms'den 30ms'ye düşürüldü - daha responsive
                        
                        // DÜZELTME: Scroll'un sonuna yaklaşıldığında immediate update
                        if (scrollTop + clientHeight >= scrollHeight - 20) {
                            console.log('SCROLL: Near bottom, immediate update');
                            if (window.dash_clientside && window.dash_clientside.set_props) {
                                try {
                                    window.dash_clientside.set_props('virtual-scroll-position', {
                                        data: scrollTop
                                    });
                                } catch (error) {
                                    console.error('Error in immediate scroll update:', error);
                                }
                            }
                        }
                        
                    }, { passive: true });
                    
                    container.hasScrollListener = true;
                    console.log('Enhanced scroll listener attached');
                }
            }, 100);
        }
        return n_clicks;
    }
    """,
    Output('virtual-scroll-container', 'data-scroll-initialized'),
    Input('virtual-dropdown-trigger', 'n_clicks'),
    prevent_initial_call=True
)

# Outside click handler - güncellenmiş (warning overlay için)
clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0 && !window.outsideClickAttached) {
            setTimeout(function() {
                document.addEventListener('click', function(e) {
                    const dropdown = document.getElementById('virtual-dropdown-trigger');
                    const menu = document.getElementById('virtual-scroll-container');
                    const warning = document.getElementById('warning-overlay');
                    
                    if (dropdown && menu && 
                        !dropdown.contains(e.target) && 
                        !menu.contains(e.target) &&
                        (!warning || !warning.contains(e.target))) {
                        
                        if (menu.style.display === 'block') {
                            menu.style.display = 'none';
                            if (window.dash_clientside && window.dash_clientside.set_props) {
                                window.dash_clientside.set_props('dropdown-open-state', {data: false});
                            }
                        }
                    }
                }, { passive: true });
                
                window.outsideClickAttached = true;
            }, 50);
        }
        return 'attached';
    }
    """,
    Output('dummy-outside-click', 'children'),
    Input('virtual-dropdown-trigger', 'n_clicks'),
    prevent_initial_call=True
)

@callback(
    [Output('virtual-item-height', 'data'),
     Output('virtual-container-height', 'data')],
    Input('virtual-dropdown-trigger', 'n_clicks'),
    prevent_initial_call=False
)
def validate_virtual_dimensions(n_clicks):
    """Validate virtual scrolling dimensions"""
    
    item_height = 40
    container_height = 320
    
    print(f"VIRTUAL DIMENSIONS: item_height={item_height}, container_height={container_height}")
    print(f"VIRTUAL DIMENSIONS: items_per_view={container_height/item_height}")
    
    return item_height, container_height


@callback(
    Output('virtual-scroll-container', 'data-total-items'),
    Input('sort-by-dropdown', 'value'),
    prevent_initial_call=False
)
def validate_total_items(sort_by):
    """Validate total number of items available for virtual scrolling"""
    
    selectable_df = get_selectable_data()
    total_items = len(selectable_df)
    
    print(f"VIRTUAL VALIDATION: Total selectable items: {total_items}")
    print(f"VIRTUAL VALIDATION: Max scroll position should be around: {total_items * 40}px")
    print(f"VIRTUAL VALIDATION: ID range: {selectable_df['ID'].min()} - {selectable_df['ID'].max()}")
    
    return total_items

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
    max_cache_size = 25  # Daha küçük cache
    
    for cache_dict in [_dropdown_cache, _param_cache, _comparison_cache, _graph_cache]:
        if len(cache_dict) > max_cache_size:
            items = list(cache_dict.items())
            cache_dict.clear()
            cache_dict.update(items[-max_cache_size//2:])

import threading
import time

def cache_cleanup_thread():
    """Background thread for cache cleanup"""
    while True:
        time.sleep(180)  # 3 dakikada bir
        try:
            manage_cache_size()
        except Exception as e:
            print(f"Cache cleanup error: {e}")

# Start cache cleanup thread
cleanup_thread = threading.Thread(target=cache_cleanup_thread, daemon=True)
cleanup_thread.start()


# Clientside callback - Uyarıyı 4 saniye sonra otomatik temizle (güncellenmiş)
# 2. Clientside callback'i basitleştirin - otomatik temizleme süresini kısaltın

clientside_callback(
    """
    function(warning_state) {
        // Eğer uyarı gösteriliyorsa, 3 saniye sonra temizle (4'ten 3'e düşürüldü)
        if (warning_state && warning_state.show) {
            console.log('Warning shown, will auto-clear in 3 seconds');
            
            // Önceki timeout'ları temizle
            if (window.warningTimeout) {
                clearTimeout(window.warningTimeout);
            }
            
            // 3 saniye bekle
            window.warningTimeout = setTimeout(function() {
                console.log('Auto-clearing warning...');
                
                // Warning state'i temizle
                if (window.dash_clientside && window.dash_clientside.set_props) {
                    try {
                        window.dash_clientside.set_props('selection-warning-state', {
                            data: {show: false, message: ''}
                        });
                    } catch (error) {
                        console.error('Error auto-clearing warning:', error);
                    }
                }
            }, 3000); // 4000'den 3000'e düşüldü
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('selection-warning-state', 'data', allow_duplicate=True),
    Input('selection-warning-state', 'data'),
    prevent_initial_call=True
)


# Dropdown açıldığında uyarıyı temizle (güncellenmiş)
clientside_callback(
    """
    function(n_clicks, warning_state) {
        // Dropdown açıldığında uyarıyı temizle
        if (n_clicks > 0 && warning_state && warning_state.show) {
            console.log('Dropdown opened, clearing warning overlay');
            return {show: false, message: ''};
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('selection-warning-state', 'data', allow_duplicate=True),
    Input('virtual-dropdown-trigger', 'n_clicks'),
    State('selection-warning-state', 'data'),
    prevent_initial_call=True
)

# YENİ: Warning overlay DOM manipülasyonu için clientside callback
clientside_callback(
    """
    function(warning_state, dropdown_state) {
        const overlay = document.getElementById('warning-overlay');
        
        if (overlay) {
            // Önceki animasyon timeout'larını temizle
            if (overlay.hideTimeout) {
                clearTimeout(overlay.hideTimeout);
                overlay.hideTimeout = null;
            }
            
            if (warning_state && warning_state.show) {
                // Uyarı gösterilecek
                overlay.style.display = 'flex';
                
                // Animasyonlu gösterim
                requestAnimationFrame(() => {
                    overlay.style.opacity = '1';
                    overlay.style.transform = 'translateY(0)';
                    
                    // Dropdown durumuna göre pozisyon ayarla
                    if (dropdown_state) {
                        overlay.style.top = 'calc(100% + 320px + 12px)';
                    } else {
                        overlay.style.top = 'calc(100% + 8px)';
                    }
                });
                
                console.log('Warning overlay shown (optimized)');
            } else {
                // Uyarı gizlenecek
                overlay.style.opacity = '0';
                overlay.style.transform = 'translateY(-5px)';
                
                // Animasyon bitince gizle
                overlay.hideTimeout = setTimeout(function() {
                    if (overlay.style.opacity === '0') {
                        overlay.style.display = 'none';
                    }
                }, 300);
                
                console.log('Warning overlay hidden (optimized)');
            }
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('warning-overlay', 'data-status', allow_duplicate=True),
    [Input('selection-warning-state', 'data'),
     Input('dropdown-open-state', 'data')],
     prevent_initial_call=True
)

# Uyarı CSS class'ını dinamik olarak ekle/çıkar
clientside_callback(
    """
    function(warning_state) {
        const dropdownContainer = document.querySelector('.enhanced-dropdown-container');
        
        if (dropdownContainer) {
            if (warning_state && warning_state.show) {
                // Uyarı varsa CSS class'ı ekle
                dropdownContainer.classList.add('warning-active');
                console.log('Added warning-active class');
            } else {
                // Uyarı yoksa CSS class'ı çıkar
                dropdownContainer.classList.remove('warning-active');
                console.log('Removed warning-active class');
            }
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('virtual-dropdown-trigger', 'data-warning-status'),
    Input('selection-warning-state', 'data'),
    prevent_initial_call=True
)

# YENİ: Keyboard handler - ESC tuşu ile dropdown'ı kapat
clientside_callback(
    """
    function(trigger_clicks) {
        if (trigger_clicks > 0 && !window.keyboardHandlerAttached) {
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    const menu = document.getElementById('virtual-scroll-container');
                    const warning = document.getElementById('warning-overlay');
                    
                    // Dropdown açıksa kapat
                    if (menu && menu.style.display === 'block') {
                        menu.style.display = 'none';
                        if (window.dash_clientside && window.dash_clientside.set_props) {
                            window.dash_clientside.set_props('dropdown-open-state', {data: false});
                        }
                    }
                    
                    // Warning açıksa kapat
                    if (warning && warning.style.display === 'flex') {
                        if (window.dash_clientside && window.dash_clientside.set_props) {
                            window.dash_clientside.set_props('selection-warning-state', {
                                data: {show: false, message: ''}
                            });
                        }
                    }
                }
            });
            
            window.keyboardHandlerAttached = true;
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('virtual-dropdown-trigger', 'data-keyboard-handler'),
    Input('virtual-dropdown-trigger', 'n_clicks'),
    prevent_initial_call=True
)


# comparison_callbacks.py dosyasının sonuna bu callback'leri ekleyin:

# ==========================================
# INSTANCE TABLE CALLBACKS
# ==========================================
"""
@callback(
    [Output('instance-table', 'data'),
     Output('instance-table', 'selected_rows'),
     Output('table-info', 'children')],
    [Input('scatter-plot', 'selectedData'),
     Input('selected-instances-store', 'data'),
     Input('table-search-input', 'value'),
     Input('table-filters', 'data'),
     Input('instance-table', 'page_current'),
     Input('instance-table', 'page_size')],
    prevent_initial_call=False
)
def update_instance_table(selectedData, selected_instances, search_value, filters, page_current, page_size):

    
    df, df_with_id = get_cached_data()
    
    # DEBUG: Scatter plot selection'ını kontrol et
    print(f"DEBUG: selectedData = {selectedData}")
    print(f"DEBUG: selected_instances = {selected_instances}")
    
    # Seçili instance'ları belirle
    selected_ids = set()
    
    # Scatter plot'tan seçilenler - DÜZELTME
    if selectedData and 'points' in selectedData:
        print(f"DEBUG: Found {len(selectedData['points'])} selected points")
        for point in selectedData['points']:
            print(f"DEBUG: Point data = {point}")
            
            # CustomData'dan ID'yi al - Farklı formatları dene
            instance_id = None
            
            # Format 1: customdata array
            if 'customdata' in point and point['customdata']:
                try:
                    if isinstance(point['customdata'], list):
                        instance_id = int(point['customdata'][0])
                    else:
                        instance_id = int(point['customdata'])
                    print(f"DEBUG: Got ID from customdata: {instance_id}")
                except (ValueError, IndexError, TypeError) as e:
                    print(f"DEBUG: customdata error: {e}")
            
            # Format 2: pointIndex kullan (fallback)
            if instance_id is None and 'pointIndex' in point:
                try:
                    point_index = point['pointIndex']
                    # DataFrame'den ID'yi al
                    instance_id = int(df_with_id.iloc[point_index]['ID'])
                    print(f"DEBUG: Got ID from pointIndex: {instance_id}")
                except (ValueError, IndexError, TypeError) as e:
                    print(f"DEBUG: pointIndex error: {e}")
            
            # Format 3: pointNumber kullan (son fallback)
            if instance_id is None and 'pointNumber' in point:
                try:
                    instance_id = int(point['pointNumber']) + 1  # 0-based'den 1-based'e
                    print(f"DEBUG: Got ID from pointNumber: {instance_id}")
                except (ValueError, TypeError) as e:
                    print(f"DEBUG: pointNumber error: {e}")
            
            if instance_id:
                selected_ids.add(instance_id)
                print(f"DEBUG: Added S{instance_id} to selection")
    
    # Dropdown'dan seçilenler
    if selected_instances:
        selected_ids.update(selected_instances)
        print(f"DEBUG: Added dropdown selections: {selected_instances}")
    
    print(f"DEBUG: Total selected IDs: {selected_ids}")
    
    if not selected_ids:
        return [], [], "No instances selected"
    
    # Seçili instance'ları filtrele
    selected_df = df_with_id[df_with_id['ID'].isin(selected_ids)].copy()
    
    if selected_df.empty:
        return [], [], "No matching instances found"
    
    # Arama filtresi uygula
    if search_value:
        search_value = search_value.lower()
        mask = (
            selected_df['ID'].astype(str).str.contains(search_value, na=False) |
            selected_df['transmittance'].astype(str).str.contains(search_value, na=False) |
            selected_df['window_shgc'].astype(str).str.contains(search_value, na=False)
        )
        selected_df = selected_df[mask]
    
    # Ekstra filtreler uygula (filters dict'inden)
    if filters:
        for column, filter_range in filters.items():
            if column in selected_df.columns:
                min_val, max_val = filter_range
                selected_df = selected_df[
                    (selected_df[column] >= min_val) &
                    (selected_df[column] <= max_val)
                ]
    
    # Tablo için veri hazırla
    table_data = []
    for idx, row in selected_df.iterrows():
        instance_id = int(row['ID'])
        
        # Checkbox için markdown
        checkbox_md = "☑️" if instance_id in (selected_instances or []) else "☐"

        display_id = instance_id - 1

        table_data.append({
            'select': checkbox_md,
            'instance_name': f'S{display_id}',
            'transmittance': round(float(row['transmittance']), 2),
            'window_shgc': round(float(row['window_shgc']), 3),
            'window_u': round(float(row['window_u']), 3),
            'roof_u': round(float(row['roof_u']), 3),
            'wall_u': round(float(row['wall_u']), 3),
            'cooling_load': round(float(row['cooling_load']), 1),
            'heating_load': round(float(row['heating_load']), 1),
            'instance_id': instance_id  # Gizli alan, seçim için
        })
    
    # Seçili satırları belirle (dropdown'dan seçilenler)
    selected_rows = []
    if selected_instances:
        for i, data in enumerate(table_data):
            if data['instance_id'] in selected_instances:
                selected_rows.append(i)
    
    # Tablo bilgisi
    total_instances = len(table_data)
    start_idx = page_current * page_size + 1
    end_idx = min((page_current + 1) * page_size, total_instances)
    
    table_info = f"Showing {start_idx}-{end_idx} of {total_instances} instances"
    
    print(f"DEBUG: Returning {len(table_data)} table rows")
    return table_data, selected_rows, table_info

"""

# Ve update_table_data fonksiyonunu da güncelleyin:

# update_table_data fonksiyonunda, scatter plot seçimlerini işleyen kısmı düzeltin:

# comparison_callbacks.py dosyasına eklenecek callback

@callback(
    [Output("instance-table", "data"),
     Output("table-info", "children"),
     Output("instance-table", "selected_rows")],
    [Input("instance-table", "page_current"),
     Input("table-search-input", "value"),
     Input("table-filters", "data"),
     Input('scatter-plot', 'selectedData'),
     Input('selected-instances-store', 'data'),
     Input('instance-table', 'sort_by')],  # Bu satırı ekleyin
    prevent_initial_call=False
)
def update_table_data(page_current, search_value, filters, selectedData, selected_instances, sort_by):
    """TÜM VERİ ÜZERİNDE SIRALAMA İLE Table data update"""
    
    try:
        print(f"TABLE DATA DEBUG: sort_by = {sort_by}")
        
        df, df_with_id = get_cached_data()
        
        # Veriyi hazırla - BASELINE HER ZAMAN GÖRÜNECEKSİN
        baseline_df = df.iloc[[0]].copy()  # Baseline (index 0)
        baseline_df['instance_name'] = 'Baseline'
        baseline_df['instance_id'] = 1
        
        # Seçili instance'ları belirle
        selected_ids = set()
        
        # Scatter plot'tan seçilenler
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
        
        # Dropdown'dan seçilenler
        if selected_instances:
            selected_ids.update(selected_instances)
        
        if selected_ids:
            # Baseline olmayan seçimleri filtrele (ID > 1)
            non_baseline_selected = [id for id in selected_ids if id > 1]
            if non_baseline_selected:
                # Non-baseline instance'lar
                remaining_df = df.iloc[1:].copy()  # Baseline'ı atla
                remaining_df['instance_name'] = 'S' + remaining_df.index.astype(str)
                remaining_df['instance_id'] = remaining_df.index + 1
                
                mask = remaining_df['instance_id'].isin(non_baseline_selected)
                selected_df = remaining_df[mask]
                
                # Baseline + seçili instance'lar
                table_df = pd.concat([baseline_df, selected_df]).reset_index(drop=True)
            else:
                # Sadece baseline seçilmişse
                table_df = baseline_df.reset_index(drop=True)
        else:
            # Hiç seçim yoksa sadece baseline
            table_df = baseline_df.reset_index(drop=True)

        # Gerekli sütunları seç
        required_columns = [
            'instance_name', 'transmittance', 'window_shgc', 
            'window_u', 'roof_u', 'wall_u', 'cooling_load', 'heating_load', 'instance_id'
        ]
        
        for col in required_columns:
            if col not in table_df.columns and col != 'instance_name' and col != 'instance_id':
                table_df[col] = 0.0
        
        available_columns = [col for col in required_columns if col in table_df.columns]
        table_df = table_df[available_columns]
        
        # Search filtering uygula
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

        # YENİ: TÜM VERİ ÜZERİNDE SIRALAMA UYGULA
        if sort_by and len(sort_by) > 0:
            sort_column = sort_by[0]['column_id']
            sort_direction = sort_by[0]['direction']
            
            print(f"SORTING: column={sort_column}, direction={sort_direction}")
            
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
        
        # Dictionary formatına çevir
        table_data = paginated_data.to_dict('records')
        
        # Sayfadaki tüm satırları seç
        selected_rows_on_page = list(range(len(paginated_data)))

        print(f"TABLE: Returning {len(table_data)} rows, total_rows={total_rows}")
        return table_data, table_info, selected_rows_on_page
        
    except Exception as e:
        print(f"Error in update_table_data: {e}")
        import traceback
        traceback.print_exc()
        return [], "Error loading data", []


@callback(
    Output('selected-instances-store', 'data', allow_duplicate=True),
    Input('instance-table', 'selected_rows'),
    [State('instance-table', 'data'),
     State('selected-instances-store', 'data')],
    prevent_initial_call=True
)
def update_selection_from_table(selected_rows, table_data, current_selected):
    """Update instance selection based on table row selection"""
    
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


# comparison_callbacks.py dosyasındaki update_filter_chips callback'ini bu kodla değiştirin:

@callback(
    Output('filter-chips-container', 'children'),
    Input('table-filters', 'data'),
    prevent_initial_call=False
)
def update_filter_chips(filters):
    """Display active filters as chips - INSTANCE FILTER SUPPORT"""
    
    print(f"FILTER CHIPS DEBUG: filters = {filters}, type = {type(filters)}")
    
    if not filters:
        return []
    
    if isinstance(filters, list):
        print("FILTER CHIPS WARNING: filters is a list, converting to dict")
        return []
    elif not isinstance(filters, dict):
        print(f"FILTER CHIPS WARNING: filters is not dict, type: {type(filters)}")
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
            print(f"FILTER CHIPS WARNING: Unknown filter format for {column}: {filter_value}")
            continue
        
        # Chip oluştur
        chip = dbc.Badge(
            [
                chip_text,
                html.Span(" ×",
                    id={"type": "remove-filter", "index": column},
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
    
    print(f"FILTER CHIPS: Created {len(chips)} chips")
    return chips


@callback(
    Output('table-filters', 'data'),
    Input({"type": "remove-filter", "index": dash.ALL}, 'n_clicks'),
    State('table-filters', 'data'),
    prevent_initial_call=True
)
def remove_filter(n_clicks_list, current_filters):
    """Remove filter when X is clicked"""
    
    if not ctx.triggered or not current_filters:
        raise PreventUpdate
    
    # Hangi filtrenin kaldırılacağını bul
    triggered = ctx.triggered[0]
    if triggered['value'] is None:
        raise PreventUpdate
    
    prop_id = triggered['prop_id']
    # JSON parse et
    import json
    button_info = json.loads(prop_id.split('.')[0])
    filter_to_remove = button_info['index']
    
    # Filtreyi kaldır
    new_filters = current_filters.copy()
    if filter_to_remove in new_filters:
        del new_filters[filter_to_remove]
    
    return new_filters


@callback(
    Output('download-instances', 'data'),
    Input('export-selected-btn', 'n_clicks'),
    [State('scatter-plot', 'selectedData'),
     State('selected-instances-store', 'data'),
     State('table-search-input', 'value'),
     State('table-filters', 'data')],
    prevent_initial_call=True
)
def export_selected_instances(n_clicks, selectedData, selected_instances, search_value, filters):
    """Export ALL filtered instances to CSV - not just current page"""
    
    if not n_clicks:
        raise PreventUpdate
    
    try:
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
        filename = f"LUX_AllSolutions_{timestamp}.csv"
        
        print(f"EXPORT: Exporting {len(export_df)} instances (filtered from {len(df)} total)")
        
        return dcc.send_data_frame(export_df.to_csv, filename, index=False)
        
    except Exception as e:
        print(f"Export error: {e}")
        import traceback
        traceback.print_exc()
        return dash.no_update


# Add Filter Modal Callback
@callback(
    Output('add-filter-modal', 'is_open'),
    [Input('add-filter-btn', 'n_clicks'),
     Input('add-filter-confirm', 'n_clicks'),
     Input('add-filter-cancel', 'n_clicks')],
    State('add-filter-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_filter_modal(add_clicks, confirm_clicks, cancel_clicks, is_open):
    """Toggle add filter modal"""
    
    if add_clicks or confirm_clicks or cancel_clicks:
        return not is_open
    return is_open


# Filter Modal Content
@callback(
    Output('filter-modal-body', 'children'),
    Input('add-filter-btn', 'n_clicks'),
    prevent_initial_call=True
)
def update_filter_modal_content(n_clicks):
    """Create filter modal content"""
    
    if not n_clicks:
        raise PreventUpdate
    
    df, _ = get_cached_data()
    
    # Filtrelenebilir sütunlar
    filterable_columns = {
        'transmittance': ('Transmittance (%)', df['transmittance'].min(), df['transmittance'].max()),
        'window_shgc': ('SHGC', df['window_shgc'].min(), df['window_shgc'].max()),
        'window_u': ('Window-U (W/m²K)', df['window_u'].min(), df['window_u'].max()),
        'roof_u': ('Roof-U (W/m²K)', df['roof_u'].min(), df['roof_u'].max()),
        'wall_u': ('Wall-U (W/m²K)', df['wall_u'].min(), df['wall_u'].max())
    }
    
    content = [
        dbc.Row([
            dbc.Col([
                html.Label("Select Parameter:", style={"fontWeight": "600", "marginBottom": "8px"}),
                dcc.Dropdown(
                    id="filter-column-dropdown",
                    options=[
                        {"label": display_name, "value": col}
                        for col, (display_name, _, _) in filterable_columns.items()
                    ],
                    placeholder="Choose parameter to filter...",
                    style={"marginBottom": "16px"}
                )
            ], width=12)
        ]),
        
        html.Div(id="filter-range-container", children=[])
    ]
    
    return content


@callback(
    Output('filter-range-container', 'children'),
    Input('filter-column-dropdown', 'value'),
    prevent_initial_call=True
)
def update_filter_range(selected_column):
    """Update range slider based on selected column"""
    
    if not selected_column:
        return []
    
    df, _ = get_cached_data()
    
    if selected_column not in df.columns:
        return []
    
    min_val = float(df[selected_column].min())
    max_val = float(df[selected_column].max())
    
    # Column display names
    column_names = {
        'transmittance': 'Transmittance (%)',
        'window_shgc': 'SHGC',
        'window_u': 'Window-U (W/m²K)',
        'roof_u': 'Roof-U (W/m²K)',
        'wall_u': 'Wall-U (W/m²K)'
    }
    
    display_name = column_names.get(selected_column, selected_column)
    
    return [
        html.Label(f"{display_name} Range:", style={"fontWeight": "600", "marginBottom": "8px"}),
        dcc.RangeSlider(
            id="filter-range-slider",
            min=min_val,
            max=max_val,
            step=(max_val - min_val) / 100,
            value=[min_val, max_val],
            marks={
                min_val: f"{min_val:.2f}",
                max_val: f"{max_val:.2f}"
            },
            tooltip={"placement": "bottom", "always_visible": True}
        )
    ]


@callback(
    Output('table-filters', 'data', allow_duplicate=True),
    Input('add-filter-confirm', 'n_clicks'),
    [State('filter-column-dropdown', 'value'),
     State('filter-range-slider', 'value'),
     State('table-filters', 'data')],
    prevent_initial_call=True
)
def add_new_filter(n_clicks, selected_column, range_values, current_filters):
    """Add new filter to the active filters"""
    
    if not n_clicks or not selected_column or not range_values:
        raise PreventUpdate
    
    new_filters = current_filters.copy() if current_filters else {}
    new_filters[selected_column] = range_values
    
    return new_filters

# comparison_callbacks.py dosyasındaki handle_manual_pagination_updated fonksiyonunu bu kodla değiştirin:

@callback(
    [Output("instance-table", "page_current"),
     Output("table-current-page", "children"),
     Output("table-total-pages", "children"),
     Output("table-first-page-btn", "disabled"),
     Output("table-prev-page-btn", "disabled"),
     Output("table-next-page-btn", "disabled"),
     Output("table-last-page-btn", "disabled")],
    [Input("table-first-page-btn", "n_clicks"),
     Input("table-prev-page-btn", "n_clicks"),
     Input("table-next-page-btn", "n_clicks"),
     Input("table-last-page-btn", "n_clicks"),
     Input("table-search-input", "value"),
     Input("table-filters", "data"),
     Input('scatter-plot', 'selectedData'),
     Input('selected-instances-store', 'data')],
    [State("instance-table", "page_current")],
    prevent_initial_call=False
)
def handle_manual_pagination_updated(first_clicks, prev_clicks, next_clicks, last_clicks,
                                   search_value, filters, selectedData, selected_instances, current_page):
    """Manuel pagination butonlarını kontrol eden güncellenmiş callback - BASELINE SABİT"""

    try:
        print("PAGINATION: comparison_callbacks.py callback çalışıyor")
        print(f"PAGINATION DEBUG: filters type = {type(filters)}, value = {filters}")

        ctx = callback_context
        df, df_with_id = get_cached_data()

        # Veriyi hazırla - DÜZELTİLDİ
        table_df = df.copy()  # DataFrame'i kopyala
        # INDEX ÜZERİNDE APPLY YAPMAK YERİNE DİREKT PANDAS SERİSİ OLUŞTUR
        table_df['instance_name'] = pd.Series(table_df.index).apply(lambda x: 'Baseline' if x == 0 else f'S{x}')
        table_df['instance_id'] = table_df.index + 1

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

        # BASELINE HER ZAMAN GÖRÜNÜR
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

        # Search filtering uygula
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
        if filters:
            print(f"FILTER DEBUG: Processing filters: {filters}")
            
            if isinstance(filters, list):
                print("FILTER WARNING: filters is a list, converting to dict")
                filters = {}
            elif not isinstance(filters, dict):
                print(f"FILTER WARNING: filters is not dict or list, type: {type(filters)}")
                filters = {}
            
            for column, filter_value in filters.items():
                if column in table_df.columns:
                    print(f"FILTER DEBUG: Applying filter for {column}: {filter_value}")
                    
                    if isinstance(filter_value, list) and len(filter_value) == 2:
                        min_val, max_val = filter_value
                        print(f"FILTER DEBUG: Range filter {column}: {min_val} - {max_val}")
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
                        print(f"FILTER WARNING: Unknown filter format for {column}: {filter_value}")

        # Toplam sayfa sayısını filtrelenmiş veri üzerinden hesapla
        page_size = 10
        total_rows = len(table_df)
        total_pages = max(1, (total_rows + page_size - 1) // page_size)

        print(f"PAGINATION: {total_rows} toplam satır, {total_pages} sayfa")

        # Varsayılan değerler
        new_page = current_page if current_page is not None else 0

        # Search, filter, veya seçim değiştiğinde ilk sayfaya dön
        if ctx.triggered:
            triggered_prop = ctx.triggered[0]["prop_id"]

            if ("table-search-input" in triggered_prop or
                "table-filters" in triggered_prop or
                "scatter-plot.selectedData" in triggered_prop or
                "selected-instances-store" in triggered_prop):
                new_page = 0
            elif "table-first-page-btn" in triggered_prop and first_clicks:
                new_page = 0
            elif "table-prev-page-btn" in triggered_prop and prev_clicks:
                new_page = max(0, current_page - 1)
            elif "table-next-page-btn" in triggered_prop and next_clicks:
                new_page = min(total_pages - 1, current_page + 1)
            elif "table-last-page-btn" in triggered_prop and last_clicks:
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

        print(f"PAGINATION: Sayfa {new_page + 1}/{total_pages}")

        return (new_page, current_page_display, total_pages_display,
                first_disabled, prev_disabled, next_disabled, last_disabled)

    except Exception as e:
        print(f"Error in handle_manual_pagination_updated: {e}")
        import traceback
        traceback.print_exc()
        return 0, "1", "1", True, True, True, True

@callback(
    [Output('filter-dropdown-menu', 'style'),
     Output('filter-dropdown-open', 'data'),
     Output('add-filter-trigger-btn', 'className')],
    [Input('add-filter-trigger-btn', 'n_clicks')],
    [State('filter-dropdown-open', 'data')],
    prevent_initial_call=True
)
def toggle_filter_dropdown(n_clicks, is_open):
    """Toggle filter dropdown visibility and update button appearance"""
    
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
    [Output('filter-step-1', 'style'),
     Output('filter-step-2', 'style'),
     Output('filter-current-step', 'data')],
    [Input({"type": "param-selector", "param": dash.ALL}, 'n_clicks'),
     Input('filter-back-btn', 'n_clicks')],
    [State('filter-current-step', 'data')],
    prevent_initial_call=True
)
def handle_filter_step_navigation(param_clicks, back_clicks, current_step):
    """Handle navigation between filter steps"""
    
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    triggered_id = ctx.triggered[0]['prop_id']
    
    # Back button clicked - go to step 1
    if 'filter-back-btn' in triggered_id:
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
    [Output('filter-selected-param', 'data'),
     Output('filter-min-input', 'placeholder'),
     Output('filter-max-input', 'placeholder')],
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
    [Output('table-filters', 'data', allow_duplicate=True),
     Output('filter-dropdown-menu', 'style', allow_duplicate=True),
     Output('filter-dropdown-open', 'data', allow_duplicate=True),
     Output('add-filter-trigger-btn', 'className', allow_duplicate=True)],
    [Input('filter-apply-btn', 'n_clicks')],
    [State('filter-selected-param', 'data'),
     State('filter-min-input', 'value'),
     State('filter-max-input', 'value'),
     State('table-filters', 'data')],
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


# 3. CLİENTSİDE CALLBACK - Dışarı tıklama ile dropdown'ı kapatmak için

clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0 && !window.filterDropdownClickListener) {
            setTimeout(function() {
                document.addEventListener('click', function(e) {
                    const trigger = document.getElementById('add-filter-trigger-btn');
                    const menu = document.getElementById('filter-dropdown-menu');
                    
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
                                    window.dash_clientside.set_props('filter-dropdown-open', {data: false});
                                } catch (error) {
                                    console.error('Error closing filter dropdown:', error);
                                }
                            }
                        }
                    }
                }, { passive: true });
                
                window.filterDropdownClickListener = true;
                console.log('Filter dropdown outside click listener attached');
            }, 50);
        }
        return 'attached';
    }
    """,
    Output('add-filter-trigger-btn', 'data-click-listener'),
    Input('add-filter-trigger-btn', 'n_clicks'),
    prevent_initial_call=True
)

# ==========================================
# HELP TOUR SYSTEM CALLBACKS
# ==========================================

# Tour adımları tanımı - spotlight mode eklenmiş
# comparison_callbacks.py dosyasındaki mevcut TOUR_STEPS listesini bu kodla değiştirin:

# comparison_callbacks.py dosyasında TOUR_STEPS listesini bu şekilde güncelleyin:

# Sonra TOUR_STEPS'te de target'ı güncelleyin:
TOUR_STEPS = [
    {
        "target": "body",
        "title": "Welcome to the MCDM User Interface",
        "description": [
            "This user interface is designed to support and guide retrofit decision-making. It presents the impacts of all possible retrofit actions for single buildings, showing how each option affects heating and cooling loads as well as emissions compared to the baseline scenario.",
            html.Br(),
            html.Br(),
            "You can find all simulated solutions under the '",
            html.B("All Solutions"),
            "' tab, while the '",
            html.B("Optimized"),
            "' tab highlights the best-performing scenarios."
        ],
        "position": "center",
        "spotlight": False,
        "width": 700
    },
    {
        "target": ".chosen-instance-card",
        "title": "Instance Selection",
        "description": [
            "All solutions can be sorted based on their ideal heating and cooling loads. Solutions can also be compared to the baseline (existing) energy performance.",
            html.Br(),
            html.Br(),
            html.B("-Wall-U / Roof-U / Window-U:"),
            " Indicate the thermal performance of the material; lower values represent better insulation and reduced heat transfer.",
            html.Br(),
            html.Br(),
            html.B("-Window-SHGC:"),
            " Represents the amount of solar heat admitted through the window; lower values reduce unwanted solar gain.",
            html.Br(),
            html.Br(),
            html.B("-Shutter Transmittance:"),
            " Refers to the amount of light and solar radiation passing through the shutters; lower values provide more shading and reduce heat gain.",
        ],
        "position": "right",
        "spotlight": True,  
        "width": 700
    },
    {
        "target": ".instance-comparison-card",
        "title": "Instance Comparison",
        "description": "Multiple scenarios selected from the instance dropdown can be compared here. You can see detailed parameter values and savings calculations.",
        "position": "left",
        "spotlight": True
    },
    {
        "target": "#comparison-graph",
        "title": "Comparison Graph",
        "description": [
            "Multiple scenarios selected from the instance selection can be compared in the graph.",
            html.Br(),
            html.Br(),
            "You can click on the check boxes to add more scenarios to comparison.",
        ],
        "position": "left",
        "spotlight": True,
        "width": 480
    },
    {
        "target": "#model3d-card",  # DEĞİŞTİRİLDİ: 3d-model-card -> model3d-card
        "title": "3D Model",
        "description": [
            "3D model of the pilot can be explored here.",
            html.Br(),
            html.Br(),
            "Envelope property ranges can be viewed by hovering over them.",
        ],
        "position": "right",
        "spotlight": True,
        "width": 600
    },
    {
        "target": "#parallel-plot",
        "title": "Parallel Coordinates Plot",
        "description": [
            "The parallel coordinates chart illustrates the relationships between envelope properties and their corresponding energy demand and emissions.",
            html.Br(),
            html.Br(),
            "You can filter each axis by clicking and dragging along it, allowing you to explore specific combinations within the solution space.",
            html.Br(),
            html.Br(),
            "Double-clicking on a filter bar will clear the applied filter.",
        ],
        "position": "right",
        "spotlight": False,
        "width": 480
    },
    {
        "target": "#scatter-plot",
        "title": "Ideal Loads Chart",
        "description": [
            "The scatter plot allows you to filter individual scenarios or groups of scenarios.",
            html.Br(),
            html.Br(),
            "Clicking on a single point highlights its corresponding envelope properties and energy demands.",
            html.Br(),
            html.Br(),
            "To select a group of scenarios, click and drag over the points, or use the lasso select tool for custom selection.  Selected scenarios are highlighted in the “instance table” and can be filtered further with the filtering tool.",
        ],
        "position": "top-left",
        "spotlight": False,
        "width": 600
    },
    {
        "target": "#figure-grid",
        "title": "Feature Plots",
        "description": [
            "The plots visualize how each building element is distributed across the building’s energy demand.",
            html.Br(),
            html.Br(),
            "The full plots can be viewed by clicking on them.",
        ],
        "position": "top",
        "spotlight": False,
        "width": 600
    },
    {
        "target": "#instance-table-card",
        "title": "Instance Table",
        "description": [
            "The Instance Table allows users to select, filter, and export instances (scenarios). The table is also linked to the Scatter Plot, updating dynamically based on selections. The filtering tool can be applied either to filter scenarios directly or to refine the selection made in the Scatter Plot. Both single and multiple instances can be selected and exported.",
        ],
        "position": "top",
        "spotlight": False,
        "width": 800
    }
]

@callback(
    [Output("tour-overlay", "style"),
     Output("tour-active", "data"),
     Output("tour-current-step", "data")],
    Input("help-button", "n_clicks"),
    State("tour-active", "data"),
    prevent_initial_call=True
)
def start_tour(n_clicks, tour_active):
    if n_clicks and not tour_active:
        return {"display": "block"}, True, 0
    raise PreventUpdate

# Tour kontrol butonları
@callback(
    [Output("tour-current-step", "data", allow_duplicate=True),
     Output("tour-overlay", "style", allow_duplicate=True),
     Output("tour-active", "data", allow_duplicate=True)],
    [Input("tour-next", "n_clicks"),
     Input("tour-prev", "n_clicks"),
     Input("tour-close", "n_clicks")],
    [State("tour-current-step", "data"),
     State("tour-active", "data")],
    prevent_initial_call=True
)
def control_tour(next_clicks, prev_clicks, close_clicks, current_step, tour_active):
    if not tour_active:
        raise PreventUpdate
    
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "tour-close":
        return 0, {"display": "none"}, False
    elif button_id == "tour-next":
        if current_step < len(TOUR_STEPS) - 1:
            return current_step + 1, {"display": "block"}, True
        else:
            # Son adımda finish
            return 0, {"display": "none"}, False
    elif button_id == "tour-prev":
        if current_step > 0:
            return current_step - 1, {"display": "block"}, True
    
    raise PreventUpdate

# Tour içeriğini güncelle
@callback(
    [Output("tour-title", "children"),
     Output("tour-description", "children"),
     Output("tour-step", "children"),
     Output("tour-prev", "disabled"),
     Output("tour-next", "children")],
    Input("tour-current-step", "data"),
    State("tour-active", "data")
)
def update_tour_content(current_step, tour_active):
    if not tour_active or current_step >= len(TOUR_STEPS):
        raise PreventUpdate
    
    step = TOUR_STEPS[current_step]
    
    # Buton durumları
    prev_disabled = current_step == 0
    next_text = "Finish" if current_step == len(TOUR_STEPS) - 1 else "Next"
    step_text = f"{current_step + 1} / {len(TOUR_STEPS)}"
    
    return step["title"], step["description"], step_text, prev_disabled, next_text


@callback(
    Output("tour-tooltip", "data-debug"),
    Input("tour-current-step", "data"),
    State("tour-active", "data"),
    prevent_initial_call=True
)
def debug_tour_steps(current_step, tour_active):
    """Debug için tour bilgilerini logla"""
    if tour_active:
        print(f"DEBUG TOUR: Current step = {current_step}")
        print(f"DEBUG TOUR: Total steps = {len(TOUR_STEPS)}")
        if current_step < len(TOUR_STEPS):
            step = TOUR_STEPS[current_step]
            print(f"DEBUG TOUR: Step {current_step} target = {step['target']}")
            print(f"DEBUG TOUR: Step {current_step} title = {step['title']}")
        else:
            print(f"DEBUG TOUR: Step index {current_step} is out of range!")
    
    return f"step_{current_step}"


# comparison_callbacks.py dosyasında mevcut tour callback'ini bu ile değiştirin:

# Ve JavaScript callback'ini de aynı şekilde güncelleyin:

# 2. JavaScript callback'ini bu debug versiyonu ile değiştirin:

# JavaScript callback'inde de target'ı güncelle:
clientside_callback(
    """
    function(current_step, tour_active) {
        console.log('=== TOUR DEBUG START ===');
        console.log('Tour positioning callback triggered:', current_step, tour_active);
        
        if (!tour_active) {
            document.querySelectorAll('.tour-highlight').forEach(el => {
                el.classList.remove('tour-highlight', 'spotlight');
                el.style.zIndex = '';
            });
            
            const overlay = document.getElementById('tour-overlay');
            if (overlay) {
                overlay.className = 'tour-overlay';
                overlay.style.removeProperty('--spotlight-left');
                overlay.style.removeProperty('--spotlight-top');
                overlay.style.removeProperty('--spotlight-width');
                overlay.style.removeProperty('--spotlight-height');
            }
            return window.dash_clientside.no_update;
        }
        
        // GÜNCELLENMİŞ TARGET: model3d-card
        const steps = [
            { target: "body", position: "center", spotlight: false, width: 700, title: "Welcome" },
            { target: ".chosen-instance-card", position: "right", spotlight: true, width: 700, title: "Instance Selection" },
            { target: ".instance-comparison-card", position: "left", spotlight: true, title: "Instance Comparison" },
            { target: "#comparison-graph", position: "left", spotlight: true, width: 480, title: "Comparison Graph" },
            { target: "#model3d-card", position: "right", spotlight: true, width: 600, title: "3D Model" },  // DEĞİŞTİRİLDİ
            { target: "#parallel-plot", position: "right", spotlight: false, width: 480, title: "Parallel Plot" },
            { target: "#scatter-plot", position: "top-left", spotlight: false, width: 600, title: "Scatter Plot" },
            { target: "#figure-grid", position: "top", spotlight: false, width: 600, title: "Feature Plots" },
            { target: "#instance-table-card", position: "top", spotlight: false, width: 800, title: "Instance Table" }
        ];
        
        if (current_step >= steps.length) {
            return window.dash_clientside.no_update;
        }
        
        const step = steps[current_step];
        const overlay = document.getElementById('tour-overlay');
        const tooltip = document.getElementById('tour-tooltip');
        
        if (!tooltip || !overlay) {
            return window.dash_clientside.no_update;
        }
        
        // Cleanup
        overlay.classList.remove('normal-mode', 'spotlight-mode-simple');
        overlay.style.removeProperty('--spotlight-left');
        overlay.style.removeProperty('--spotlight-top');
        overlay.style.removeProperty('--spotlight-width');
        overlay.style.removeProperty('--spotlight-height');
        
        document.querySelectorAll('.tour-highlight').forEach(el => {
            el.classList.remove('tour-highlight', 'spotlight');
            el.style.zIndex = '';
        });
        
        tooltip.style.opacity = '0';
        tooltip.style.visibility = 'hidden';
        
        if (step.width) {
            tooltip.style.maxWidth = step.width + 'px';
        } else {
            tooltip.style.maxWidth = '380px'; 
        }

        if (step.position === 'center') {
            overlay.classList.add('normal-mode');
            tooltip.className = 'tour-tooltip center-position';
            tooltip.style.opacity = '1';
            tooltip.style.visibility = 'visible';
            return window.dash_clientside.no_update;
        }
        
        // Apply wide-tooltip class for instance table step
        if (step.target === '#instance-table-card') {
            tooltip.className = 'tour-tooltip wide-tooltip';
        } else {
            tooltip.className = 'tour-tooltip';
        }
        
        console.log('Looking for target element:', step.target);
        const targetElement = document.querySelector(step.target);
        
        if (!targetElement) {
            console.error('TARGET ELEMENT NOT FOUND:', step.target);
            overlay.classList.add('normal-mode');
            // Apply wide-tooltip class even for center position if it's the instance table step
            if (step.target === '#instance-table-card') {
                tooltip.className = 'tour-tooltip center-position wide-tooltip';
            } else {
                tooltip.className = 'tour-tooltip center-position';
            }
            tooltip.style.opacity = '1';
            tooltip.style.visibility = 'visible';
            return window.dash_clientside.no_update;
        }
        
        console.log('Target element found:', targetElement);
        targetElement.classList.add('tour-highlight');
        targetElement.style.zIndex = '10002';
        
        const executePositioning = () => {
            targetElement.scrollIntoView({
                behavior: 'smooth',
                block: 'center',
                inline: 'center'
            });
            
            setTimeout(() => {
                if (step.spotlight) {
                    targetElement.classList.add('spotlight');
                    overlay.classList.add('spotlight-mode-simple');
                    
                    const rect = targetElement.getBoundingClientRect();
                    const padding = 10;
                    const spotlightLeft = rect.left - padding;
                    const spotlightTop = rect.top - padding;  
                    const spotlightWidth = rect.width + (padding * 2);
                    const spotlightHeight = rect.height + (padding * 2);
                    
                    overlay.style.setProperty('--spotlight-left', spotlightLeft + 'px');
                    overlay.style.setProperty('--spotlight-top', spotlightTop + 'px');
                    overlay.style.setProperty('--spotlight-width', spotlightWidth + 'px');
                    overlay.style.setProperty('--spotlight-height', spotlightHeight + 'px');
                } else {
                    overlay.classList.add('normal-mode');
                }
                
                const targetRect = targetElement.getBoundingClientRect();
                tooltip.style.display = 'block';
                tooltip.style.position = 'absolute';
                const tooltipRect = tooltip.getBoundingClientRect();
                
                let top, left;
                const margin = 25;
                
                switch(step.position) {
                    case 'top':
                        top = targetRect.top - tooltipRect.height - margin;
                        left = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);
                        break;
                    case 'bottom':
                        top = targetRect.bottom + margin;
                        left = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);
                        break;
                    case 'left':
                        top = targetRect.top + (targetRect.height / 2) - (tooltipRect.height / 2);
                        left = targetRect.left - tooltipRect.width - margin;
                        break;
                    case 'top-left':
                        top = targetRect.top + (targetRect.height / 2) - (tooltipRect.height / 2);
                        left = targetRect.left - tooltipRect.width - margin - 80;
                        break;
                    case 'right':
                        top = targetRect.top + (targetRect.height / 2) - (tooltipRect.height / 2) - 50;
                        left = targetRect.right + margin;
                        break;
                    default:
                        top = targetRect.bottom + margin;
                        left = targetRect.left;
                }
                
                const viewportPadding = 20;
                const maxTop = window.innerHeight - tooltipRect.height - viewportPadding;
                const maxLeft = window.innerWidth - tooltipRect.width - viewportPadding;
                
                top = Math.max(viewportPadding, Math.min(top, maxTop));
                left = Math.max(viewportPadding, Math.min(left, maxLeft));
                
                tooltip.style.top = top + 'px';
                tooltip.style.left = left + 'px';
                
                setTimeout(() => {
                    tooltip.style.visibility = 'visible';
                    tooltip.style.opacity = '1';
                }, 100);
                
            }, 500);
        };
        
        executePositioning();
        return window.dash_clientside.no_update;
    }
    """,
    Output("tour-tooltip", "data-positioned"),
    [Input("tour-current-step", "data")],
    [State("tour-active", "data")],
    prevent_initial_call=True
)


clientside_callback(
    """
    function(tour_active) {
        if (tour_active && !window.tourEventListeners) {
            // ESC tuşu ile kapat
            const handleKeydown = (e) => {
                if (e.key === 'Escape') {
                    document.getElementById('tour-close').click();
                }
            };
            
            // Overlay'e tıklayınca kapat
            const handleOverlayClick = (e) => {
                if (e.target.id === 'tour-overlay') {
                    document.getElementById('tour-close').click();
                }
            };
            
            document.addEventListener('keydown', handleKeydown);
            document.getElementById('tour-overlay').addEventListener('click', handleOverlayClick);
            
            window.tourEventListeners = { handleKeydown, handleOverlayClick };
        } else if (!tour_active && window.tourEventListeners) {
            // Event listener'ları temizle
            document.removeEventListener('keydown', window.tourEventListeners.handleKeydown);
            const overlay = document.getElementById('tour-overlay');
            if (overlay) {
                overlay.removeEventListener('click', window.tourEventListeners.handleOverlayClick);
                
                // SPOTLIGHT TEMİZLEME
                overlay.classList.remove('normal-mode', 'spotlight-mode-simple');
                overlay.style.removeProperty('--spotlight-left');
                overlay.style.removeProperty('--spotlight-top');
                overlay.style.removeProperty('--spotlight-width');
                overlay.style.removeProperty('--spotlight-height');
            }
            
            // Highlight'ları temizle
            document.querySelectorAll('.tour-highlight').forEach(el => {
                el.classList.remove('tour-highlight', 'spotlight');
                el.style.zIndex = '';
            });
            
            window.tourEventListeners = null;
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output("tour-system", "data-events-attached"),
    Input("tour-active", "data"),
    prevent_initial_call=True
)

