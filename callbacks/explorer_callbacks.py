from dash import callback, callback_context, Input, Output, State
import pandas as pd
from dash.exceptions import PreventUpdate
from dash import Input, Output, State, callback, clientside_callback
from dash.exceptions import PreventUpdate

# pages.explorer'dan gerekli değişkenleri import et
from pages.explorer import df, labels

# Modal data - resim bilgileri
MODAL_IMAGES = [
    {
        "id": "plot-wall-u",
        "title": "Ideal Heating vs Ideal Cooling Load (Colored by Wall-U)",
        "thumbnail": "/assets/plot_wall_u.png",
        "fullsize": "/assets/fullPlot_wall_u.png"
    },
    {
        "id": "plot-window-u", 
        "title": "Ideal Heating vs Ideal Cooling Load (Colored by Window-U)",
        "thumbnail": "/assets/plot_window_u.png",
        "fullsize": "/assets/fullPlot_window_u.png"
    },
    {
        "id": "plot-window-shgc",
        "title": "Ideal Heating vs Ideal Cooling Load (Colored by Window-SHGC)",
        "thumbnail": "/assets/plot_window_shgc.png",
        "fullsize": "/assets/fullPlot_window_shgc.png"
    },
    {
        "id": "plot-roof-u",
        "title": "Ideal Heating vs Ideal Cooling Load (Colored by Roof-U)",
        "thumbnail": "/assets/plot_roof_u.png",
        "fullsize": "/assets/fullPlot_roof_u.png"
    },
    {
        "id": "plot-transmittance",
        "title": "Ideal Heating vs Ideal Cooling Load (Colored by Transmittance)",
        "thumbnail": "/assets/plot_transmittance.png",
        "fullsize": "/assets/fullPlot_transmittance.png"
    }
]

@callback(
    [Output("parallel-plot", "figure"),
     Output("scatter-plot", "figure")],
    [Input("scatter-plot", "clickData"),
     Input("scatter-plot", "selectedData"),
     Input("parallel-plot", "restyleData")],
    [State("parallel-plot", "figure"),
     State("scatter-plot", "figure")],
    prevent_initial_call=True
)
def update_linked_graphs(scatter_click, scatter_selected, parallel_restyle, parallel_fig, scatter_fig):
    """
    Sadece scatter ve parallel coordinates plotlarını birbirine bağlayan sadeleştirilmiş callback.
    Tek nokta seçimi için daha sağlam bir mantık içerir.
    """
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_prop = ctx.triggered[0]["prop_id"]
    selected_indices = []

    # 1. Durum: Paralel Koordinat Grafiğinden Filtreleme Gelirse
    if "parallel-plot.restyleData" in triggered_prop:
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

    # 2. Durum: Scatter Plot'tan Seçim (Sürükleyerek veya Tıklayarak) Gelirse
    elif "scatter-plot.selectedData" in triggered_prop and scatter_selected and scatter_selected.get("points"):
        selected_indices = [pt["pointIndex"] for pt in scatter_selected.get("points")]
    
    elif "scatter-plot.clickData" in triggered_prop and scatter_click and scatter_click.get("points"):
        selected_indices = [scatter_click["points"][0]["pointIndex"]]

    # Her iki grafiği de güncelle
    scatter_fig["data"][0]["selectedpoints"] = selected_indices

    # Paralel koordinat grafiğindeki çizgileri seçime göre güncelle
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
            
            # Tek nokta seçimi için daha sağlam mantık
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
    [Output("image-modal", "style"),
     Output("modal-image", "src"),
     Output("modal-title", "children"),
     Output("current-image-index", "data"),
     Output("modal-prev", "disabled"),
     Output("modal-next", "disabled")],
    [Input("plot-wall-u", "n_clicks"),
     Input("plot-window-u", "n_clicks"),
     Input("plot-window-shgc", "n_clicks"),
     Input("plot-roof-u", "n_clicks"),
     Input("plot-transmittance", "n_clicks"),
     Input("modal-close", "n_clicks"),
     Input("modal-prev", "n_clicks"),
     Input("modal-next", "n_clicks")],
    [State("current-image-index", "data")],
    prevent_initial_call=True
)
def handle_modal_interactions(wall_clicks, window_u_clicks, shgc_clicks, roof_clicks, 
                            trans_clicks, close_clicks, prev_clicks, next_clicks, 
                            current_index):
    """Handle all modal interactions - open, close, navigation"""
    
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    triggered_prop = ctx.triggered[0]["prop_id"]
    
    # Modal'ı kapat
    if "modal-close" in triggered_prop:
        return {"display": "none"}, "", "", 0, False, False
    
    # Navigation - Previous
    if "modal-prev" in triggered_prop and prev_clicks:
        if current_index > 0:
            new_index = current_index - 1
            image_data = MODAL_IMAGES[new_index]
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
    if "modal-next" in triggered_prop and next_clicks:
        if current_index < len(MODAL_IMAGES) - 1:
            new_index = current_index + 1
            image_data = MODAL_IMAGES[new_index]
            prev_disabled = False
            next_disabled = (new_index == len(MODAL_IMAGES) - 1)
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
    
    # Hangi resme tıklandığını belirle ve modal'ı aç
    for i, image_data in enumerate(MODAL_IMAGES):
        if image_data["id"] in triggered_prop:
            prev_disabled = (i == 0)
            next_disabled = (i == len(MODAL_IMAGES) - 1)
            
            return (
                {"display": "flex"}, 
                image_data["fullsize"], 
                image_data["title"],
                i,
                prev_disabled,
                next_disabled
            )
    
    raise PreventUpdate


# Klavye kontrolü için clientside callback
clientside_callback(
    """
    function(modal_style) {
        if (modal_style && modal_style.display === 'flex') {
            if (window.modalKeyListener) {
                document.removeEventListener('keydown', window.modalKeyListener);
            }
            
            window.modalKeyListener = function(e) {
                const modal = document.getElementById('image-modal');
                if (modal && modal.style.display === 'flex') {
                    if (e.key === 'Escape') {
                        document.getElementById('modal-close').click();
                    } else if (e.key === 'ArrowLeft') {
                        document.getElementById('modal-prev').click();
                        e.preventDefault();
                    } else if (e.key === 'ArrowRight') {
                        document.getElementById('modal-next').click();
                        e.preventDefault();
                    }
                }
            };
            
            document.addEventListener('keydown', window.modalKeyListener);
            
            setTimeout(function() {
                const modal = document.getElementById('image-modal');
                if (modal) {
                    modal.focus();
                }
            }, 100);
        } else {
            if (window.modalKeyListener) {
                document.removeEventListener('keydown', window.modalKeyListener);
                window.modalKeyListener = null;
            }
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('keyboard-listener', 'value'),
    Input('image-modal', 'style'),
    prevent_initial_call=True
)


# MANUEL PAGINATION CALLBACKS - TEMİZ VERSİYON
"""
@callback(
    [Output("instance-table", "data"),
     Output("table-info", "children")],
    [Input("instance-table", "page_current"),
     Input("table-search-input", "value"),
     Input("table-filters", "data")],
    prevent_initial_call=False
)
def update_table_data(page_current, search_value, filters):
    
    try:
        # Veriyi hazırla
        table_df = df.copy()
        table_df['instance_name'] = 'S' + (table_df.index + 1).astype(str)
        
        # Gerekli sütunları seç
        required_columns = [
            'instance_name', 'transmittance', 'window_shgc', 
            'window_u', 'roof_u', 'wall_u', 'cooling_load', 'heating_load'
        ]
        
        # Mevcut sütunları kontrol et ve eksik olanları 0 ile doldur
        for col in required_columns:
            if col not in table_df.columns and col != 'instance_name':
                table_df[col] = 0.0
        
        # Sadece gerekli sütunları al
        available_columns = [col for col in required_columns if col in table_df.columns]
        table_df = table_df[available_columns]
        
        # Search filtering
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
            for column, filter_config in filters.items():
                if column in table_df.columns:
                    if filter_config.get('type') == 'range':
                        min_val = filter_config.get('min')
                        max_val = filter_config.get('max')
                        if min_val is not None:
                            table_df = table_df[table_df[column] >= min_val]
                        if max_val is not None:
                            table_df = table_df[table_df[column] <= max_val]
        
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
        
        return table_data, table_info
        
    except Exception as e:
        print(f"Error in update_table_data: {e}")
        return [], "Error loading data"

"""
"""
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
     Input("table-filters", "data")],
    [State("instance-table", "page_current")],
    prevent_initial_call=False
)
def handle_manual_pagination_updated(first_clicks, prev_clicks, next_clicks, last_clicks, 
                                   search_value, filters, current_page):
    
    try:
        ctx = callback_context
        
        # Veriyi hazırla (filtering için)
        table_df = df.copy()
        table_df['instance_name'] = 'S' + (table_df.index + 1).astype(str)
        
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
            for column, filter_config in filters.items():
                if column in table_df.columns:
                    if filter_config.get('type') == 'range':
                        min_val = filter_config.get('min')
                        max_val = filter_config.get('max')
                        if min_val is not None:
                            table_df = table_df[table_df[column] >= min_val]
                        if max_val is not None:
                            table_df = table_df[table_df[column] <= max_val]
        
        # Toplam sayfa sayısını hesapla
        page_size = 10
        total_rows = len(table_df)
        total_pages = max(1, (total_rows + page_size - 1) // page_size)
        
        # Varsayılan değerler
        new_page = current_page if current_page is not None else 0
        
        # Search veya filter değiştiğinde ilk sayfaya dön
        if ctx.triggered:
            triggered_prop = ctx.triggered[0]["prop_id"]
            
            if "table-search-input" in triggered_prop or "table-filters" in triggered_prop:
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
        
        return (new_page, current_page_display, total_pages_display, 
                first_disabled, prev_disabled, next_disabled, last_disabled)
                
    except Exception as e:
        print(f"Error in handle_manual_pagination_updated: {e}")
        return 0, "1", "1", True, True, True, True

"""