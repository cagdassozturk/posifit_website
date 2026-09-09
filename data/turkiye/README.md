# Turkiye Pilot Data Folder

Please upload the following CSV files to this directory:

1. **TUR_Training.csv** - Main training dataset for Turkiye (equivalent to LUX_2026_V6_Training.csv)
   - Required columns: wall_u, window_u, window_shgc, roof_u, transmittance, heating_load, cooling_load

2. **TUR_pareto_optimized.csv** - Pareto optimized dataset (equivalent to pareto_front_predicted_100_yeni.csv)
   - Use semicolon (;) as separator
   - Required columns: wall_u, window_u, window_shgc, roof_u, transmittance, heating_load, cooling_load

3. **TUR_combinations_with_predictions.csv** - Combinations with predictions for market search
   - Required columns: predicted_heating_load, predicted_cooling_load, wall_u, window_u, window_shgc, roof_u, transmittance, scenario

4. **TUR_products.xlsx** - Product information (equivalent to products.xlsx)
   - Sheet: Products with columns: scenario, wall_name_shorter, window_name_shorter, roof_name_shorter, wall_id, window_id, roof_id

5. **TUR_layers.xlsx** - Layer descriptions (equivalent to layers.xlsx)
   - Sheets: "External Wall", "Roof", "Window"
   - Columns: ID, Layer Description

## Plot Images (PNG files)

Upload these plot images to `/assets/turkiye/`:

1. plot_wall_u.png
2. plot_window_u.png
3. plot_window_shgc.png
4. plot_roof_u.png
5. plot_transmittance.png
6. fullPlot_wall_u.png (optional - high resolution version)
7. fullPlot_window_u.png (optional)
8. fullPlot_window_shgc.png (optional)
9. fullPlot_roof_u.png (optional)
10. fullPlot_transmittance.png (optional)

Note: If you don't have the high resolution versions, the regular versions will be used for both thumbnail and modal view.
