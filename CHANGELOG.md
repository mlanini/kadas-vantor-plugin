# Changelog

All notable changes to the KADAS Vantor Open Data Plugin.

## [0.2.0] - 2026-02-13

### Rebranding
- ✅ Complete rebrand from Maxar to Vantor across all documentation
- ✅ Updated metadata.txt with new brand
- ✅ Updated tags: vantor, maxar (for backward compatibility)
- ✅ Translated all documentation to English (en_US)

### Architecture
- ✅ Migration from STAC to GitHub dataset (opengeos/maxar-open-data)
- ✅ Data source: datasets.csv for events + {event}.geojson for footprints
- ✅ Network with QgsNetworkAccessManager (proxy-aware)
- ✅ Configurable timeouts: 120s events, 180s footprints
- ✅ Automatic timeout migration from 30s to 120s/180s

### Features
- ✅ Interactive map selection with custom FootprintSelectionTool
- ✅ Ctrl+Click for multiple selection
- ✅ Bidirectional map ↔ table synchronization
- ✅ Quadkey-based mapping (sort-safe, replaces catalog_id)
- ✅ Universal CRS support via PROJ (QgsCoordinateTransform)
- ✅ Auto-zoom with WGS84 → canvas CRS coordinate transformation
- ✅ Filters for cloud cover (0-100%) and date range
- ✅ COG loading: visual, ms_analytic, pan_analytic
- ✅ Zoom to Selected with automatic CRS transformation
- ✅ Clear All Layers (batch removal of Vantor layers)

### Critical Fixes
- ✅ FootprintSelectionTool lifecycle management (recreation on activation)
- ✅ Tool invalidation when layer removed/recreated
- ✅ GeoJSON parsing with json.loads() for strings
- ✅ Correct geometry creation with QgsPointXY
- ✅ QgsFeature initialization with fields to avoid KeyError
- ✅ COG field name correction (removed _cog_url suffix)
- ✅ Layer extent transformation for auto-zoom (EPSG:4326 → canvas CRS)
- ✅ Adaptive buffer for feature selection (geographic vs projected)

### UI/UX
- ✅ Custom "EO" ribbon tab in KADAS
- ✅ Footprints layer styling: semi-transparent cyan
- ✅ Numeric column sorting (GSD, Cloud %)
- ✅ Selection highlighted in yellow on map
- ✅ Status label with informative messages
- ✅ Progress bar for async operations
- ✅ Separate Settings panel

### Logging & Debug
- ✅ Custom logging system with CriticalFileHandler
- ✅ Log file: `~/.kadas/maxar.log` (configurable via `KADAS_MAXAR_LOG`)
- ✅ Levels: STANDARD, DEBUG, ERRORS
- ✅ Complete stacktraces for CRITICAL errors
- ✅ Menu action "Open log file"

### Testing
- ✅ Test suite with pytest
- ✅ Qt/QGIS stubs in conftest.py
- ✅ Tests for UI, entry point, network, geometries
- ✅ Coverage tracking with pytest-cov

### Documentation
- ✅ README.md with complete overview (English)
- ✅ INSTALL.md with multi-platform instructions (English)
- ✅ QUICKSTART.md with example workflows (English)
- ✅ CONTRIBUTING.md with developer guidelines (English)
- ✅ CHANGELOG.md (this file)
- ✅ .github/copilot-instructions.md for AI agents

---

**Crediti**:
- Basato su [qgis-maxar-plugin](https://github.com/opengeos/qgis-maxar-plugin) di Qiusheng Wu
- Dati da [Vantor Open Data Program](https://www.maxar.com/open-data) (precedentemente Maxar)
- Adattamento KADAS: Michael Lanini ([Intelligeo](https://www.intelligeo.ch))

**Licenza**: MIT
