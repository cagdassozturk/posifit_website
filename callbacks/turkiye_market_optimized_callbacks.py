from dash import callback, Output, Input, State, dcc, clientside_callback
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate
import dash

from pages.turkiye_market_optimized import (
    df_plot,
    df_search,
    find_closest_instances,
    create_spider_chart,
    get_product_names,
    get_layer_descriptions,
)


@callback(
    [Output('tur-market-optimized-selected-point-store', 'data'),
     Output('tur-market-optimized-scatter-plot', 'figure')],
    Input('tur-market-optimized-scatter-plot', 'clickData'),
    State('tur-market-optimized-scatter-plot', 'figure'),
    prevent_initial_call=True,
)
def tur_market_opt_update_selected_point(clickData, current_fig):
    if not clickData:
        raise PreventUpdate

    point_index = clickData['points'][0]['pointIndex']

    fig = px.scatter(
        df_plot,
        x="heating_load",
        y="cooling_load",
        labels={
            "heating_load": "Ideal Heating Load (kWh)",
            "cooling_load": "Ideal Cooling Load (kWh)",
        },
    )
    fig.update_traces(
        marker=dict(size=6, opacity=0.4, color="#2AACFD"),
        hovertemplate="Ideal Heating Load: %{x:.1f} kWh<br>"
                      "Ideal Cooling Load: %{y:.1f} kWh<extra></extra>",
    )

    selected_row = df_plot.iloc[point_index]
    fig.add_trace(go.Scatter(
        x=[selected_row['heating_load']],
        y=[selected_row['cooling_load']],
        mode='markers',
        marker=dict(size=12, color='#063D5E', line=dict(width=3, color='white')),
        name=f'Selected (S{point_index})',
        hovertemplate=(
            "<b>Selected Point</b><br>"
            f"Ideal Heating Load: {selected_row['heating_load']:.1f} kWh<br>"
            f"Ideal Cooling Load: {selected_row['cooling_load']:.1f} kWh<extra></extra>"
        ),
    ))

    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font_color="#2C3E50",
        showlegend=False,
        margin=dict(l=50, r=50, t=20, b=50),
        xaxis=dict(showgrid=True, gridcolor="lightgrey"),
        yaxis=dict(showgrid=True, gridcolor="lightgrey"),
        dragmode=False,
    )

    return point_index, fig


@callback(
    [Output('tur-market-optimized-spider-chart', 'figure'),
     Output('tur-market-optimized-instances-store', 'data')],
    [Input('tur-market-optimized-selected-point-store', 'data'),
     Input('tur-market-optimized-neighbors-slider', 'value')],
)
def tur_market_opt_update_spider(selected_idx, n_neighbors):
    if selected_idx is None:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            annotations=[{
                'text': 'Click a point on the scatter plot to see neighbors',
                'xref': 'paper', 'yref': 'paper',
                'x': 0.5, 'y': 0.5, 'xanchor': 'center', 'yanchor': 'middle',
                'showarrow': False, 'font': {'size': 16, 'color': 'grey'},
            }],
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
        )
        return empty_fig, []

    if n_neighbors is None:
        n_neighbors = 5

    closest_indices = find_closest_instances(selected_idx, n_neighbors)
    spider_fig = create_spider_chart(selected_idx, closest_indices)
    all_indices = [selected_idx] + closest_indices
    return spider_fig, all_indices


@callback(
    [Output('tur-market-optimized-instance-table', 'data'),
     Output('tur-market-optimized-table-info', 'children'),
     Output('tur-market-optimized-layers-data', 'data')],
    [Input('tur-market-optimized-instances-store', 'data'),
     Input('tur-market-optimized-selected-point-store', 'data'),
     Input('tur-market-optimized-neighbors-slider', 'value')],
    prevent_initial_call=False,
)
def tur_market_opt_update_table(instance_indices, selected_idx, n_neighbors):
    if not instance_indices or selected_idx is None:
        return [], "No instances selected", {}

    table_data = []

    def get_val(row, col_name, alt_names=None):
        if col_name in row.index:
            return float(row[col_name])
        if alt_names:
            if isinstance(alt_names, str):
                alt_names_local = [alt_names]
            else:
                alt_names_local = alt_names
            for alt in alt_names_local:
                if alt in row.index:
                    return float(row[alt])
        return 0.0

    for i, idx in enumerate(instance_indices):
        if i == 0:
            row = df_plot.iloc[idx]
            instance_name = f"Selected Instance (S{idx})"
            instance_type = "selected"
        else:
            row = df_search.iloc[idx]
            instance_name = f"P{i}"
            instance_type = "market"

        if instance_type == "selected":
            window_product = "-"
            roof_product = "-"
            wall_product = "-"
        else:
            scenario_id = f"p{idx}"
            products = get_product_names(scenario_id)
            window_product = products['window_product']
            roof_product = products['roof_product']
            wall_product = products['wall_product']

        if instance_type == "selected":
            row_data = {
                'instance_name': instance_name,
                'transmittance': get_val(row, 'transmittance') * 100,
                'window_shgc': get_val(row, 'window_shgc'),
                'window_u': get_val(row, 'window_u'),
                'window_product': window_product,
                'roof_u': get_val(row, 'roof_u'),
                'roof_product': roof_product,
                'wall_u': get_val(row, 'wall_u'),
                'wall_product': wall_product,
                'cooling_load': get_val(row, 'cooling_load'),
                'heating_load': get_val(row, 'heating_load'),
                'instance_idx': idx,
            }
        else:
            row_data = {
                'instance_name': instance_name,
                'transmittance': get_val(row, 'transmittance') * 100,
                'window_shgc': get_val(row, 'window_shgc'),
                'window_u': get_val(row, 'window_u'),
                'window_product': window_product,
                'roof_u': get_val(row, 'roof_u'),
                'roof_product': roof_product,
                'wall_u': get_val(row, 'wall_u'),
                'wall_product': wall_product,
                'cooling_load': get_val(row, 'predicted_cooling_load', ['cooling_load']),
                'heating_load': get_val(row, 'predicted_heating_load', ['heating_load']),
                'instance_idx': idx,
            }

        table_data.append(row_data)

    total_rows = len(table_data)
    if total_rows == 0:
        table_info = "No instances found"
    else:
        n_market = max(0, total_rows - 1)
        table_info = f"{n_market} market instances shown"

    layers_data = {}
    for i, idx in enumerate(instance_indices):
        if i == 0:
            window_layers = []
            roof_layers = []
            wall_layers = []
        else:
            scenario_id = f"p{idx}"
            products = get_product_names(scenario_id)
            window_layers = get_layer_descriptions('window', products['window_id'])
            roof_layers = get_layer_descriptions('roof', products['roof_id'])
            wall_layers = get_layer_descriptions('wall', products['wall_id'])

        layers_data[i] = {
            'window_layers': window_layers,
            'roof_layers': roof_layers,
            'wall_layers': wall_layers,
        }

    return table_data, table_info, layers_data


@callback(
    Output('tur-market-optimized-download-instances', 'data'),
    Input('tur-export-market-optimized-button', 'n_clicks'),
    [State('tur-market-optimized-instance-table', 'selected_rows'),
     State('tur-market-optimized-instance-table', 'data')],
    prevent_initial_call=True,
)
def tur_market_opt_export_selected(n_clicks, selected_rows, table_data):
    if not n_clicks or not table_data:
        raise PreventUpdate

    if selected_rows:
        selected_data = [table_data[i] for i in selected_rows if i < len(table_data)]
    else:
        selected_data = table_data

    if not selected_data:
        raise PreventUpdate

    export_df = pd.DataFrame(selected_data)
    export_columns = {
        'instance_name': 'Instance',
        'transmittance': 'Transmittance (%)',
        'window_shgc': 'SHGC',
        'window_u': 'Window-U (W/m²K)',
        'window_product': 'Window Product',
        'roof_u': 'Roof-U (W/m²K)',
        'roof_product': 'Roof Product',
        'wall_u': 'Wall-U (W/m²K)',
        'wall_product': 'Wall Product',
        'cooling_load': 'Ideal Cooling (kWh)',
        'heating_load': 'Ideal Heating (kWh)',
    }
    available_cols = [c for c in export_columns if c in export_df.columns]
    export_df = export_df[available_cols]
    export_df = export_df.rename(columns={c: export_columns[c] for c in available_cols})

    numeric_cols = [
        'Transmittance (%)', 'SHGC', 'Window-U (W/m²K)', 'Roof-U (W/m²K)',
        'Wall-U (W/m²K)', 'Ideal Cooling (kWh)', 'Ideal Heating (kWh)',
    ]
    for col in numeric_cols:
        if col in export_df.columns:
            export_df[col] = pd.to_numeric(export_df[col], errors='coerce').round(3)

    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"TUR_MarketAvailableScenarios_Optimized_{ts}.csv"
    return dcc.send_data_frame(export_df.to_csv, filename, index=False)


@callback(
    Output('tur-market-optimized-instance-table', 'selected_rows'),
    Input('tur-market-optimized-instance-table', 'data'),
    prevent_initial_call=False,
)
def tur_market_opt_default_selection(table_data):
    if table_data and len(table_data) > 1:
        return list(range(1, len(table_data)))
    return []


clientside_callback(
    """
    function(layersData) {
        setTimeout(function() {
            document
              .querySelectorAll('td[data-dash-column="window_product"], td[data-dash-column="roof_product"], td[data-dash-column="wall_product"]')
              .forEach(cell => {
                  if (!cell.hasAttribute('data-hover-initialized')) {
                      cell.setAttribute('data-hover-initialized', 'true');
                      cell.addEventListener('mouseenter', function() {
                          const columnType = this.getAttribute('data-dash-column').replace('_product', '');
                          const cellElement = this;
                          const rowElement = cellElement.closest('tr');
                          const tbody = cellElement.closest('tbody');
                          const allRows = Array.from(tbody.querySelectorAll('tr'));
                          let actualRowIndex = allRows.indexOf(rowElement);
                          if (actualRowIndex > 0) {
                              actualRowIndex = actualRowIndex - 1;
                          }
                          const layers = layersData &&
                                         layersData[actualRowIndex] &&
                                         layersData[actualRowIndex][columnType + '_layers'] || [];
                          createProductBubble(cellElement, layers, columnType);
                      });
                      cell.addEventListener('mouseleave', function() {
                          removeProductBubble();
                      });
                  }
              });
        }, 500);
        return null;
    }
    """,
    Output('tur-market-optimized-hover-state', 'data'),
    Input('tur-market-optimized-layers-data', 'data'),
)

clientside_callback(
    """
    function() {
        window.createProductBubble = function(element, layers, productType) {
            const existing = document.querySelector('.product-hover-bubble');
            if (existing) existing.remove();
            const minHeight = 160;
            const maxHeight = 400;
            let bubbleHeight = minHeight;
            if (layers && layers.length > 0) {
                const calc = 40 + layers.length * 25;
                bubbleHeight = Math.min(maxHeight, Math.max(minHeight, calc));
            }
            const bubble = document.createElement('div');
            bubble.className = 'product-hover-bubble';
            bubble.style.cssText = `
                position: fixed;
                width: 320px;
                height: ${bubbleHeight}px;
                background-color: #FFFFFF;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.2);
                z-index: 10000;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.3s ease;
                padding: 0;
                box-sizing: border-box;
                display: flex;
                overflow: hidden;
            `;
            const leftSide = document.createElement('div');
            leftSide.style.cssText = `
                width: 160px;
                height: ${bubbleHeight}px;
                background-image: url('/assets/${productType}_product.png');
                background-size: 154px 138px;
                background-position: center top 10px;
                background-repeat: no-repeat;
                border-radius: 12px 0 0 12px;
                flex-shrink: 0;
            `;
            const rightSide = document.createElement('div');
            rightSide.style.cssText = `
                width: 160px;
                height: ${bubbleHeight}px;
                overflow-y: auto;
                padding: 10px;
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
                scrollbar-width: thin;
            `;
            if (layers && layers.length > 0) {
                const title = document.createElement('div');
                title.textContent = 'Layers (Outside to Inside):';
                title.style.cssText = `
                    font-family: 'Poppins', sans-serif;
                    font-size: 11px;
                    font-weight: 600;
                    color: #2AACFD;
                    margin-bottom: 8px;
                    border-bottom: 1px solid #E0E0E0;
                    padding-bottom: 4px;
                `;
                rightSide.appendChild(title);
                layers.forEach(layer => {
                    const div = document.createElement('div');
                    div.textContent = layer;
                    div.style.cssText = `
                        font-family: 'Poppins', sans-serif;
                        font-size: 8px;
                        line-height: 1.4;
                        color: #333;
                        margin-bottom: 3px;
                        padding: 4px 6px;
                        background-color: rgba(42, 172, 253, 0.08);
                        border-radius: 4px;
                        border-left: 2px solid #2AACFD;
                        word-wrap: break-word;
                        white-space: normal;
                        min-height: 18px;
                        box-sizing: border-box;
                    `;
                    rightSide.appendChild(div);
                });
            } else {
                const noLayers = document.createElement('div');
                noLayers.textContent = 'No layer information available';
                noLayers.style.cssText = `
                    font-family: 'Poppins', sans-serif;
                    font-size: 10px;
                    color: #999;
                    font-style: italic;
                    text-align: center;
                    padding-top: 50px;
                `;
                rightSide.appendChild(noLayers);
            }
            bubble.appendChild(leftSide);
            bubble.appendChild(rightSide);
            const rect = element.getBoundingClientRect();
            const tbody = element.closest('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const rowIndex = rows.indexOf(element.closest('tr'));
            const totalRows = rows.length;
            const isBottom = rowIndex >= Math.max(0, totalRows - 3);
            let top, left;
            if (isBottom) top = rect.top - bubbleHeight - 10;
            else top = rect.bottom + 10;
            left = rect.left + rect.width / 2 - 160;
            const vw = window.innerWidth;
            const vh = window.innerHeight;
            if (left + 320 > vw) left = vw - 320 - 10;
            if (left < 10) left = 10;
            if (top < 10) top = rect.bottom + 10;
            if (top + bubbleHeight > vh) top = rect.top - bubbleHeight - 10;
            bubble.style.top = top + 'px';
            bubble.style.left = left + 'px';
            document.body.appendChild(bubble);
            setTimeout(() => bubble.style.opacity = '1', 10);
            return bubble;
        };
        window.removeProductBubble = function() {
            const bubble = document.querySelector('.product-hover-bubble');
            if (bubble) {
                bubble.style.opacity = '0';
                setTimeout(() => bubble.parentNode && bubble.parentNode.removeChild(bubble), 300);
            }
        };
        return null;
    }
    """,
    Output('tur-market-optimized-hover-state', 'data', allow_duplicate=True),
    Input('tur-market-optimized-instance-table', 'data'),
    prevent_initial_call=True,
)


