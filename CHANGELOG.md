# Changelog

All notable changes to the KADAS Vantor Open Data Plugin.

## [0.1.0] - 2026-01-12

### Added
- ✅ Interactive footprint selection from map with custom QgsMapTool
- ✅ Ctrl+Click multi-selection support
- ✅ Bidirectional map ↔ table selection sync
- ✅ Quadkey-based mapping system (sort-safe)
- ✅ CRS transformation for click detection (canvas → layer CRS)
- ✅ Adaptive buffer for feature detection (geographic vs projected)
- ✅ Cloud cover filtering (0-100%)
- ✅ Date range filtering
- ✅ COG loading for visual, multispectral, and panchromatic imagery
- ✅ Zoom to selected footprints
- ✅ Comprehensive logging system
- ✅ Event list refresh from GitHub
- ✅ Dynamic filter application

### Fixed
- ✅ Feature selection detection with buffered intersection
- ✅ Tool lifecycle management (recreation on activation)
- ✅ Selection sync with sorted tables
- ✅ Catalog ID mapping issue (replaced with unique quadkey)
- ✅ Loop prevention in bidirectional sync

### Technical Details
- Custom FootprintSelectionTool extending QgsMapTool
- Signal-based selection sync (no callbacks)
- QgsFeatureRequest with bounding box optimization
- Robust layer validity checking
- Comprehensive test suite with pytest

---

**Credits**:
- Based on [qgis-maxar-plugin](https://github.com/opengeos/qgis-maxar-plugin) by Qiusheng Wu.
- Imagery credits &copy; Vantor Open Data Program.

**Author**: Michael Lanini

**License**: MIT
