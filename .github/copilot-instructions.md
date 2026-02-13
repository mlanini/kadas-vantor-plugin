# KADAS Vantor Open Data Plugin - AI Agent Instructions

## Project Overview

This is a **KADAS Albireo 2.x plugin** (fork adapted from QGIS) for browsing and loading Maxar/Vantor satellite imagery from disaster events via STAC catalogs. The plugin provides interactive footprint selection, cloud cover filtering, and Cloud Optimized GeoTIFF (COG) loading.

**Critical distinction**: KADAS != QGIS. While KADAS is based on QGIS 3.x, it uses `KadasPluginInterface` instead of `QgisInterface`. Always use `from kadas.kadasgui import *` and cast the interface: `self.iface = KadasPluginInterface.cast(iface)`.

## Architecture

### Core Components

1. **`kadas_maxar.py`** - Main plugin class (`KadasMaxar(QObject)`)
   - Manages menu actions, proxy settings, logging
   - Creates custom "EO" ribbon tab: `iface.addActionMenu(..., iface.CUSTOM_TAB, "EO")`
   - **Proxy handling**: Reads QGIS settings (`QgsSettings`) and propagates to both Qt (`QNetworkProxy`) AND environment variables for external libraries (requests/urllib)

2. **`dialogs/maxar_dock.py`** - Main UI dock widget (`MaxarDockWidget`)
   - STAC catalog browsing and event selection
   - Footprints table with bidirectional map↔table selection sync
   - Interactive map selection tool (`FootprintSelectionTool`)
   - Uses `QgsNetworkAccessManager` for proxy-aware network requests

3. **`dialogs/settings_dock.py`** - Settings panel
   - Network timeouts, debug mode, display preferences
   - Uses `QSettings` with `MaxarOpenData/` prefix

4. **`logger.py`** - Custom logging system
   - Logs to `~/.kadas/maxar.log` (configurable via `KADAS_MAXAR_LOG` env var)
   - Levels: `STANDARD`, `DEBUG`, `ERRORS` (not typical Python levels)
   - `CriticalFileHandler` writes full stacktraces for CRITICAL errors

### Data Flow

```
GitHub (opengeos/maxar-open-data)
  ↓ DataFetchWorker (QThread + QgsNetworkAccessManager)
  ↓ CSV parsing → Extract events + tile counts
  ↓ Event selection
  ↓ GeoJSON URL construction ({event}.geojson)
  ↓ Load GeoJSON directly (single request)
  ↓ GeoJSON features parsing
  ↓ QgsVectorLayer (Polygon, EPSG:4326)
  ↓ Interactive selection (FootprintSelectionTool)
  ↓ COG imagery loading (QgsRasterLayer, "gdal" provider)
```

**Data Source**: GitHub-hosted dataset from `opengeos/maxar-open-data` repository  
**Events**: `datasets.csv` with event names and tile counts  
**Footprints**: Direct GeoJSON files at `datasets/{event}.geojson`

**Network requests MUST use `QgsNetworkAccessManager`** (not requests/urllib) to respect KADAS proxy settings automatically.

## Critical Patterns

### 1. KADAS-Specific Interface

```python
# ✅ Correct
from kadas.kadasgui import *
self.iface = KadasPluginInterface.cast(iface)
self.iface.addActionMenu(title, icon, menu, 
                         self.iface.PLUGIN_MENU, 
                         self.iface.CUSTOM_TAB, "EO")

# ❌ Wrong - QGIS pattern won't work
from qgis.gui import QgisInterface
```

### 2. Proxy Configuration (CRITICAL for network connectivity)

The plugin applies proxy settings in `_apply_proxy_settings()` at `initGui()`:

```python
def _apply_proxy_settings(self):
    settings = QgsSettings()
    enabled = settings.value("proxy/enabled", False, type=bool)
    
    # Sets QNetworkProxy for Qt
    qproxy = QNetworkProxy(...)
    QNetworkProxy.setApplicationProxy(qproxy)
    
    # Propagates to env vars for external libraries
    os.environ["HTTP_PROXY"] = proxy_url
    os.environ["HTTPS_PROXY"] = proxy_url
```

**Network requests pattern**:
```python
# Use QgsNetworkAccessManager (proxy-aware)
nam = QgsNetworkAccessManager.instance()
req = QNetworkRequest(QUrl(url))
reply = nam.get(req)
loop = QEventLoop()
reply.finished.connect(loop.quit)
loop.exec_()
```

### 3. Map ↔ Table Selection Sync

Uses **quadkey-based mapping** (sort-safe):

```python
self._feature_id_to_quadkey = {}  # Layer feature IDs → quadkeys
self._quadkey_to_feature_id = {}  # Quadkeys → layer feature IDs

# Table → Map
def _on_footprint_selection_changed(self):
    if self._updating_selection:
        return  # Prevent feedback loop
    quadkeys = [feature["properties"]["quadkey"] for selected rows]
    fids = [self._quadkey_to_feature_id[qk] for qk in quadkeys]
    layer.selectByIds(fids)

# Map → Table
def _on_layer_selection_changed(self):
    self._updating_selection = True
    quadkeys = [self._feature_id_to_quadkey[fid] for selected fids]
    # Select matching table rows
    self._updating_selection = False
```

### 4. Testing with Stubs

All dialogs have **try/except fallbacks** for test environments without Qt:

```python
try:
    from qgis.PyQt.QtWidgets import QDockWidget
except Exception:
    class QDockWidget(object):  # Minimal stub
        def __init__(self, *a, **k):
            self.visibilityChanged = type("S", (), {"connect": lambda self, cb: None})()
```

Tests use `conftest.py` for comprehensive QGIS/KADAS module stubs.

## Development Workflows

### Running Tests

```powershell
# Run all tests
python -m pytest

# Specific test file
python -m pytest kadas_maxar/tests/test_ui.py -v

# With coverage
python -m pytest --cov=kadas_maxar
```

**Test discovery**: `pytest.ini` configures `python_files = tests/test_*.py`.

### Packaging for Distribution

```powershell
# Create plugin ZIP (excludes tests, __pycache__, dev files)
python package_plugin.py

# Output: kadas-vantor-plugin-0.1.0.zip
# Custom output location
python package_plugin.py --output dist/custom.zip
```

The script reads version from `metadata.txt` and creates QGIS-compatible ZIP structure.

### Manual Installation

```powershell
# Windows
cd $env:APPDATA\kadas-albireo2\python\plugins
git clone https://github.com/mlanini/kadas-vantor-plugin.git kadas_maxar
```

**Folder name MUST be `kadas_maxar`** to match Python package name.

### Debugging Network Issues

1. Check log file: `~/.kadas/maxar.log`
2. Use "Apri file di log" menu action (opens in system editor)
3. Run connectivity test:
   ```powershell
   python kadas_maxar/tests/test_stac_connectivity.py
   ```
4. Verify proxy settings in KADAS: `Settings → Options → Network`

## Conventions

### Logging

```python
from kadas_maxar.logger import get_logger

# In plugin class
self.log = get_logger(level="STANDARD")  # "DEBUG", "ERRORS"
self.log.info("Normal operation")
self.log.warning("Potential issue")
self.log.error("Error occurred", exc_info=True)  # Full stacktrace
```

### Settings Keys

All settings use `MaxarOpenData/` prefix:
- `use_local` - Use local data copy (bool)
- `stac_catalog_url` - STAC catalog URL (string)
- `auto_zoom` - Auto-zoom to footprints (bool, default: True)
- `timeout` - Network timeout seconds (int, default: 180 for footprints, 120 for events)
- `debug` - Debug mode (bool)

Access via: `QSettings().value("MaxarOpenData/timeout", 180, type=int)`

### Italian UI Strings

Plugin uses Italian for UI (targeting Swiss/Italian users):
- Status messages: "Caricamento eventi dal catalogo STAC..."
- Error messages: "Impossibile caricare il COG"
- Use `self.tr("...")` for translatable strings (though currently hardcoded IT)

### Imports Organization

```python
# 1. Qt/PyQt (with try/except for test stubs)
from qgis.PyQt.QtWidgets import ...
from qgis.PyQt.QtCore import ...

# 2. QGIS core
from qgis.core import QgsProject, QgsVectorLayer, ...

# 3. KADAS
from kadas.kadasgui import *

# 4. Internal
from kadas_maxar.logger import get_logger
```

## Common Pitfalls

1. **Using `requests` library**: Won't respect KADAS proxy → use `QgsNetworkAccessManager`
2. **Forgetting `KadasPluginInterface.cast(iface)`**: Interface methods won't work
3. **Selection sync infinite loops**: Always use `self._updating_selection` flag
4. **Wrong folder name**: Plugin folder MUST be `kadas_maxar` (not `kadas-vantor-plugin`)
5. **Hardcoded paths**: Use `os.path.join(self.plugin_dir, ...)` for icons/resources
6. **Missing cleanup in `unload()`**: Always disconnect signals, remove menus, close docks
7. **GitHub URL construction**: Use `GEOJSON_URL_TEMPLATE.format(event=event_name)` for footprints

## External Dependencies

- **GitHub Data**: `https://raw.githubusercontent.com/opengeos/maxar-open-data/master/datasets.csv`
- **GDAL COG support**: Required for raster layer loading
- **No pip dependencies**: Plugin uses only QGIS/KADAS built-in libraries

## Key Files for Reference

- **Entry point**: `__init__.py` → `classFactory(iface)` → `KadasMaxar(iface)`
- **Network layer**: `DataFetchWorker` class in `maxar_dock.py` (QThread)
- **Selection logic**: `FootprintSelectionTool` class (QgsMapTool)
- **Test stubs**: `tests/conftest.py` (comprehensive mocking)
- **Packaging**: `package_plugin.py` (exclude patterns, versioning)

## When Making Changes

1. **Network code**: Always test with proxy-enabled KADAS installation
2. **UI changes**: Test both with Qt available (runtime) and stub environment (tests)
3. **New settings**: Add to `MaxarOpenData/` namespace with default values
4. **Logging**: Use appropriate level (`self.log.debug/info/warning/error`)
5. **Before commit**: Run `python -m pytest` and verify `python package_plugin.py` succeeds
