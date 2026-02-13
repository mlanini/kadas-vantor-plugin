# Quick Start Guide

## 1. Installation
Download and install the plugin (see [INSTALL.md](INSTALL.md) for details).

## 2. Open the Panel
- Menu: `View → Panels → Vantor Open Data`
- Or click the satellite icon in the "EO" ribbon tab

## 3. Browse Events
1. Select an event from the dropdown menu
2. Click "Load Footprints"
3. Footprints appear as semi-transparent blue polygons on the map

## 4. Filter Data
- **Cloud Cover**: Set maximum acceptable cloud cover (0-100%)
- **Date Range**: Enable date filter and select start/end dates
- Click "Apply Filters" to update

## 5. Select Footprints

### From Map
1. Click the "Select from Map" button
2. Click on footprints directly on the map
3. Hold Ctrl and click for multiple selection
4. Selected footprints are highlighted in yellow on map and in table

### From Table
- Click rows in the table
- Hold Ctrl for multiple selection
- Selection automatically syncs with the map

## 6. Load Imagery
1. Select one or more footprints
2. Click:
   - **Load Visual**: RGB imagery
   - **Load MS**: Multispectral imagery
   - **Load Pan**: Panchromatic imagery
3. Images are loaded as COG layers

## 7. Useful Buttons
- **Zoom to Selected**: Zoom map to selected footprints (with automatic CRS transformation)
- **Clear All Layers**: Remove all Vantor layers from project
- **Refresh Events**: Update event list from GitHub
- **Settings**: Configure timeout, debug, auto-zoom

## Tips

### Interactive Selection
- Single click = select one footprint (deselects others)
- Ctrl+Click = add/remove from selection
- Works even after sorting table columns

### Performance
- Use filters to reduce the number of displayed footprints
- Cloud cover filter is most effective
- Date filter is useful for temporal analysis

### Sorting
- Double-click column headers to sort
- Selection synchronization works with sorted tables
- Numeric columns (GSD, Cloud %) are sorted numerically

### Troubleshooting
- Footprints not loading? Check internet connection and log (`~/.kadas/maxar.log`)
- Selection not working? Try deactivating/reactivating "Select from Map"
- Images not loading? Verify GDAL COG support
- Zoom goes to 0°,0°? Check that layer is valid and canvas CRS is configured

## Example Workflow

1. Select event "Emilia-Romagna-Italy-flooding-may23"
2. Click "Load Footprints"
3. Set maximum cloud cover to 20%
4. Click "Apply Filters"
5. Activate "Select from Map"
6. Click on a footprint with low cloud cover
7. Click "Load Visual" to view the image
8. Analyze the loaded visual layer

## Next Steps
- See [README.md](README.md) for detailed documentation
- Report issues at [GitHub Issues](https://github.com/mlanini/kadas-vantor-plugin/issues)
- Check the log at `~/.kadas/maxar.log` for debugging
