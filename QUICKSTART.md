# Quick Start Guide

## 1. Installation
Download and install the plugin (see [INSTALL.md](INSTALL.md) for details).

## 2. Open the Panel
- Menu: `View → Panels → Vantor EO Data`
- Or click the Vantor icon in the toolbar

## 3. Browse Events
1. Select an event from the dropdown menu
2. Click "Load Footprints"
3. Footprints appear as blue polygons on the map

## 4. Filter Data
- **Cloud Cover**: Set maximum acceptable cloud cover (0-100%)
- **Date Range**: Enable date filter and select start/end dates
- Click "Apply Filters" to refresh

## 5. Select Footprints

### From Map
1. Click "Select from Map" button
2. Click on footprints directly on the map
3. Hold Ctrl and click to select multiple
4. Selected footprints highlight in yellow on map and in table

### From Table
- Click rows in the table
- Hold Ctrl for multiple selection
- Selection syncs automatically with map

## 6. Load Imagery
1. Select one or more footprints
2. Click:
   - **Load Visual**: RGB imagery
   - **Load MS**: Multispectral imagery
   - **Load Pan**: Panchromatic imagery
3. Images load as COG layers

## 7. Useful Buttons
- **Zoom to Selected**: Zoom map to selected footprints
- **Clear All Layers**: Remove all Vantor layers from project
- **Refresh Events**: Update event list from GitHub

## Tips

### Interactive Selection
- Single click = select one footprint (deselects others)
- Ctrl+Click = add/remove from selection
- Works even after sorting table columns

### Performance
- Use filters to reduce number of footprints
- Cloud cover filter is most effective
- Date range useful for temporal analysis

### Sorting
- Double-click column headers to sort
- Selection sync works with sorted tables
- Numeric columns (GSD, Cloud %) sort numerically

### Troubleshooting
- No footprints loading? Check internet connection
- Selection not working? Try deactivating/reactivating "Select from Map"
- Images not loading? Check GDAL COG support

## Example Workflow

1. Select "Iceland-Volcano_Eruption-Dec-2023" event
2. Load footprints
3. Set max cloud cover to 20%
4. Click "Apply Filters"
5. Activate "Select from Map"
6. Click on a clear footprint
7. Click "Load Visual" to see imagery
8. Analyze the visual layer

## Next Steps
- See [README.md](README.md) for detailed documentation
- Report issues at [GitHub Issues](https://github.com/mlanini/kadas-vantor-plugin/issues)
