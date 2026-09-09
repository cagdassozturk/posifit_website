# Turkiye Plot Images

Please upload your Turkiye-specific plot images to this directory.

## Required Files (PNG format)

### Thumbnail Images (Required)
These images are shown in the main page:

1. **plot_wall_u.png**
   - Scatter plot: Heating Load vs Cooling Load
   - Colored by: Wall U-value
   - Recommended size: 800x600 pixels

2. **plot_window_u.png**
   - Scatter plot: Heating Load vs Cooling Load
   - Colored by: Window U-value
   - Recommended size: 800x600 pixels

3. **plot_window_shgc.png**
   - Scatter plot: Heating Load vs Cooling Load
   - Colored by: Window SHGC
   - Recommended size: 800x600 pixels

4. **plot_roof_u.png**
   - Scatter plot: Heating Load vs Cooling Load
   - Colored by: Roof U-value
   - Recommended size: 800x600 pixels

5. **plot_transmittance.png**
   - Scatter plot: Heating Load vs Cooling Load
   - Colored by: Transmittance
   - Recommended size: 800x600 pixels

### Full-Size Images (Optional)
These images are shown when user clicks on a plot for full-screen view:

6. **fullPlot_wall_u.png** (optional)
7. **fullPlot_window_u.png** (optional)
8. **fullPlot_window_shgc.png** (optional)
9. **fullPlot_roof_u.png** (optional)
10. **fullPlot_transmittance.png** (optional)

*Note: If full-size images are not provided, the regular plot images will be used for modal view as well.*

## Upload Methods

### Using SCP/SFTP
```bash
scp plot_*.png user@server:/var/www/legofit-explorer.com/assets/turkiye/
```

### Using File Manager
Navigate to this directory and drag-and-drop your PNG files.

### Setting Permissions
After upload, ensure proper permissions:
```bash
chmod 644 /var/www/legofit-explorer.com/assets/turkiye/*.png
```

## Current Status

Check uploaded files:
```bash
ls -lh /var/www/legofit-explorer.com/assets/turkiye/
```

Expected output after upload:
```
plot_wall_u.png
plot_window_u.png
plot_window_shgc.png
plot_roof_u.png
plot_transmittance.png
```
