"""
Maxar Open Data Dock Widget for KADAS

Adapted from opengeos/qgis-maxar-plugin for KADAS compatibility.
"""

try:
    from qgis.PyQt.QtWidgets import (
        QDockWidget,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QFormLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QComboBox,
        QSpinBox,
        QCheckBox,
        QGroupBox,
        QProgressBar,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QSplitter,
        QMessageBox,
        QDateEdit,
        QApplication,
    )
    from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal, QSettings, QDate
    from qgis.PyQt.QtGui import QFont
except Exception:
    # If imports fail, use stub classes (test environment)
    from qgis.PyQt.QtCore import QSettings
    from qgis.PyQt.QtWidgets import (
        QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
        QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QCheckBox, QGroupBox,
        QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
        QAbstractItemView, QSplitter, QMessageBox, QDateEdit, QApplication
    )
    from qgis.PyQt.QtCore import Qt, QDate
    from qgis.PyQt.QtGui import QFont
    # Stub fallbacks
    class QThread:
        def __init__(self):
            pass
        def start(self):
            pass
        def wait(self):
            pass
        def isRunning(self):
            return False
    class pyqtSignal:
        def __init__(self, *args):
            pass
        def connect(self, cb):
            pass
        def emit(self, *args):
            pass

try:
    from qgis.core import (
        QgsProject,
        QgsRasterLayer,
        QgsVectorLayer,
        QgsCoordinateReferenceSystem,
        QgsCoordinateTransform,
        QgsRectangle,
        QgsFillSymbol,
        QgsFeature,
        QgsSingleSymbolRenderer
    )
    from qgis.gui import QgsMapTool
    from qgis.PyQt.QtGui import QColor
except Exception:
    # Stubs for test environment
    class QgsProject:
        @staticmethod
        def instance():
            return type('proj', (), {'addMapLayer': lambda self, l: None, 'removeMapLayer': lambda self, l: None, 'mapLayers': lambda self: {}})()
    class QgsRasterLayer:
        def __init__(self, *a, **k):
            pass
        def isValid(self):
            return True
    class QgsVectorLayer:
        def __init__(self, *a, **k):
            self._selected = []
        def isValid(self):
            return True
        def id(self):
            return 'layer_id'
        def setCrs(self, crs):
            pass
        def selectionChanged(self):
            return type('S', (), {'connect': lambda self, cb: None})()
        def willBeDeleted(self):
            return type('S', (), {'connect': lambda self, cb: None})()
        def selectByIds(self, ids):
            self._selected = ids
        def selectedFeatureIds(self):
            return self._selected
        def renderer(self):
            return type('R', (), {'setSymbol': lambda self, s: None})()
        def triggerRepaint(self):
            pass
    class QgsCoordinateReferenceSystem:
        def __init__(self, *a):
            pass
    class QgsCoordinateTransform:
        def __init__(self, *a, **k):
            pass
        def transformBoundingBox(self, bbox):
            return bbox
    class QgsRectangle:
        def __init__(self, *a):
            pass
    class QgsFillSymbol:
        @staticmethod
        def createSimple(props):
            return type('Symbol', (), {'setOpacity': lambda self, o: None})()
    class QgsFeature:
        pass
    class QColor:
        def __init__(self, *a):
            pass
    class QgsMapTool:
        def __init__(self, canvas):
            self.canvas = canvas
        def activate(self):
            pass
        def deactivate(self):
            pass
        def canvasPressEvent(self, e):
            pass
        def setCursor(self, cursor):
            pass
        def toMapCoordinates(self, pos):
            return type('Point', (), {'x': lambda: 0, 'y': lambda: 0})()
    class QgsSingleSymbolRenderer:
        def __init__(self, symbol):
            self.symbol = symbol

from kadas_maxar.logger import get_logger

# GitHub data sources
GITHUB_RAW_URL = "https://raw.githubusercontent.com/opengeos/maxar-open-data/master"
DATASETS_CSV_URL = f"{GITHUB_RAW_URL}/datasets.csv"
GEOJSON_URL_TEMPLATE = f"{GITHUB_RAW_URL}/datasets/{{event}}.geojson"

# STAC catalog URL
DEFAULT_STAC_CATALOG_URL = "https://maxar-opendata.s3.amazonaws.com/events/catalog.json"


class FootprintSelectionTool(QgsMapTool):
    """Custom map tool for selecting footprints interactively."""
    
    selectionModeChanged = pyqtSignal(bool)  # True when active, False when inactive
    
    def __init__(self, canvas, layer):
        """Initialize the selection tool.
        
        Args:
            canvas: The KADAS/QGIS map canvas
            layer: The footprints vector layer
        """
        super().__init__(canvas)
        self.layer = layer
        self.canvas = canvas
        self.setCursor(Qt.CrossCursor)
        self.is_active = False
        get_logger().info("FootprintSelectionTool initialized")
    
    def canvasPressEvent(self, e):
        """Handle mouse press on canvas."""
        if not self.layer:
            get_logger().warning("Layer is not set")
            return
        
        try:
            from qgis.core import (
                QgsCoordinateTransform,
                QgsFeatureRequest,
                QgsGeometry,
                QgsProject,
            )
            
            # Get point from mouse event in canvas CRS
            point_canvas = self.toMapCoordinates(e.pos())
            canvas_crs = self.canvas.mapSettings().destinationCrs()
            layer_crs = self.layer.crs()
            get_logger().info(
                f"Canvas click at: ({point_canvas.x():.6f}, {point_canvas.y():.6f}) in {canvas_crs.authid()}"
            )

            # Transform point to layer CRS if needed
            point_layer = point_canvas
            if canvas_crs != layer_crs:
                try:
                    to_layer = QgsCoordinateTransform(canvas_crs, layer_crs, QgsProject.instance())
                    point_layer = to_layer.transform(point_canvas)
                    get_logger().debug(
                        f"Transformed click to layer CRS {layer_crs.authid()}: ({point_layer.x():.6f}, {point_layer.y():.6f})"
                    )
                except Exception as transform_error:
                    get_logger().error(f"CRS transform failed: {transform_error}", exc_info=True)
                    return
            
            # Adaptive buffer size: ~10m in meters or ~0.0001 deg in geographic
            if layer_crs.isGeographic():
                buffer_size = 0.0001
            else:
                buffer_size = 10.0

            point_geom = QgsGeometry.fromPointXY(point_layer)
            buffered_point = point_geom.buffer(buffer_size, 8)
            
            # Search only nearby features using bounding box filter
            request = QgsFeatureRequest().setFilterRect(buffered_point.boundingBox())
            features_at_point = []
            min_distance = float("inf")
            closest_feature = None
            
            try:
                for feature in self.layer.getFeatures(request):
                    geom = feature.geometry()
                    if geom is None:
                        continue
                    
                    if geom.intersects(buffered_point):
                        fid = feature.id()
                        distance = geom.distance(point_geom)
                        get_logger().debug(f"Feature {fid} intersects buffer, distance: {distance}")
                        
                        if distance < min_distance:
                            min_distance = distance
                            closest_feature = fid
                
                if closest_feature is not None:
                    features_at_point = [closest_feature]
                    get_logger().info(
                        f"Found closest intersecting feature {closest_feature} at distance {min_distance}"
                    )
            except Exception as layer_error:
                get_logger().error(f"Error detecting features: {layer_error}", exc_info=True)
            
            get_logger().info(f"Features found at click point: {features_at_point}")
            
            if features_at_point:
                if e.modifiers() & Qt.ControlModifier:
                    current_selected = list(self.layer.selectedFeatureIds())
                    if features_at_point[0] in current_selected:
                        current_selected.remove(features_at_point[0])
                        get_logger().info(f"Removed from selection: {features_at_point[0]}")
                    else:
                        current_selected.append(features_at_point[0])
                        get_logger().info(f"Added to selection: {features_at_point[0]}")
                    self.layer.selectByIds(current_selected)
                else:
                    self.layer.selectByIds(features_at_point)
                    get_logger().info(f"Selected feature(s): {features_at_point}")
            else:
                self.layer.selectByIds([])
                get_logger().info("No feature at click point, cleared selection")
        except Exception as e:
            get_logger().error(f"Error in canvas press event: {e}", exc_info=True)
    
    def activate(self):
        """Activate the selection tool."""
        super().activate()
        self.is_active = True
        self.canvas.setCursor(Qt.CrossCursor)
        self.selectionModeChanged.emit(True)
        get_logger().info("Footprint selection tool activated")
    
    def deactivate(self):
        """Deactivate the selection tool."""
        super().deactivate()
        self.is_active = False
        self.selectionModeChanged.emit(False)
        get_logger().info("Footprint selection tool deactivated")


class DataFetchWorker(QThread):
    """Worker thread for fetching data from GitHub."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, data_type="text"):
        super().__init__()
        self.url = url
        self.data_type = data_type

    def run(self):
        """Fetch data in background."""
        try:
            from urllib.request import urlopen
            with urlopen(self.url, timeout=30) as response:
                data = response.read().decode('utf-8')
                self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))


class NumericTableWidgetItem(QTableWidgetItem):
    """Custom table item that sorts numerically."""
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return super().__lt__(other)


class MaxarDockWidget(QDockWidget):
    """Main dockable panel for browsing Maxar Open Data."""

    def __init__(self, iface, parent=None):
        """Initialize the dock widget."""
        super().__init__("Vantor EO Data", parent)
        self.iface = iface
        self.settings = QSettings()
        self.events = []
        self.current_geojson = None
        self.footprints_layer = None
        self.fetch_worker = None
        self._sort_order = {}
        self.all_features = []
        self._updating_selection = False  # Prevent selection feedback loops
        self._feature_id_to_quadkey = {}  # Map layer feature IDs to quadkeys
        self._quadkey_to_feature_id = {}  # Map quadkeys to layer feature IDs
        self.selection_tool = None  # Custom map tool for interactive selection
        self._previous_map_tool = None  # Store previous tool when entering selection mode

        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self._setup_ui()
        self._load_events()

    def _setup_ui(self):
        """Set up the dock widget UI."""
        main_widget = QWidget()
        self.setWidget(main_widget)

        layout = QVBoxLayout(main_widget)
        layout.setSpacing(10)

        # Header
        header_label = QLabel("Vantor EO Data")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(header_label)

        # Description
        desc_label = QLabel(
            "Browse and visualize high-resolution satellite imagery from the "
            "Vantor EO Data Program for disaster events."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #b0b0b0; font-size: 10px;")
        layout.addWidget(desc_label)

        # Event Selection Group
        event_group = QGroupBox("Event Selection")
        event_group.setStyleSheet("QGroupBox { color: #ffffff; font-weight: bold; }")
        event_layout = QFormLayout(event_group)

        # Event dropdown (GitHub)
        event_label = QLabel("Event:")
        event_label.setStyleSheet("color: #f0f0f0; font-weight: 500;")
        self.event_combo = QComboBox()
        self.event_combo.setMinimumWidth(200)
        self.event_combo.currentIndexChanged.connect(self._on_event_changed)
        event_layout.addRow(event_label, self.event_combo)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Events")
        self.refresh_btn.clicked.connect(self._load_events)
        refresh_layout.addWidget(self.refresh_btn)
        refresh_layout.addStretch()
        event_layout.addRow("", refresh_layout)

        layout.addWidget(event_group)

        # Filters Group
        filter_group = QGroupBox("Filters")
        filter_group.setStyleSheet("QGroupBox { color: #ffffff; font-weight: bold; }")
        filter_layout = QFormLayout(filter_group)

        # Max cloud cover
        cloud_label = QLabel("Max Cloud Cover:")
        cloud_label.setStyleSheet("color: #f0f0f0; font-weight: 500;")
        self.cloud_spin = QSpinBox()
        self.cloud_spin.setRange(0, 100)
        self.cloud_spin.setValue(100)
        self.cloud_spin.setSuffix(" %")
        filter_layout.addRow(cloud_label, self.cloud_spin)

        # Date filter checkbox
        self.date_check = QCheckBox("Filter by date range")
        self.date_check.setChecked(False)
        self.date_check.stateChanged.connect(self._on_date_filter_changed)
        filter_layout.addRow("", self.date_check)

        # Date range
        start_label = QLabel("Start Date:")
        start_label.setStyleSheet("color: #f0f0f0; font-weight: 500;")
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate(2020, 1, 1))
        self.start_date_edit.setEnabled(False)
        filter_layout.addRow(start_label, self.start_date_edit)

        end_label = QLabel("End Date:")
        end_label.setStyleSheet("color: #f0f0f0; font-weight: 500;")
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setEnabled(False)
        filter_layout.addRow(end_label, self.end_date_edit)

        layout.addWidget(filter_group)

        # Load footprints button
        load_btn_layout = QHBoxLayout()
        self.load_footprints_btn = QPushButton("Load Footprints")
        self.load_footprints_btn.clicked.connect(self._load_footprints)
        self.load_footprints_btn.setEnabled(False)
        load_btn_layout.addWidget(self.load_footprints_btn)
        
        # Apply filters button
        self.apply_filters_btn = QPushButton("Apply Filters")
        self.apply_filters_btn.clicked.connect(self._apply_current_filters)
        self.apply_filters_btn.setEnabled(False)
        load_btn_layout.addWidget(self.apply_filters_btn)
        
        layout.addLayout(load_btn_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Splitter for table and actions
        splitter = QSplitter(Qt.Vertical)

        # Footprints table
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)

        table_label = QLabel("Imagery Footprints:")
        table_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        table_layout.addWidget(table_label)

        self.footprints_table = QTableWidget()
        self.footprints_table.setColumnCount(6)
        self.footprints_table.setHorizontalHeaderLabels(
            ["Date", "Platform", "GSD", "Cloud %", "Catalog ID", "Quadkey"]
        )
        self.footprints_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.footprints_table.horizontalHeader().setStretchLastSection(True)
        self.footprints_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.footprints_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.footprints_table.setAlternatingRowColors(True)
        self.footprints_table.itemSelectionChanged.connect(
            self._on_footprint_selection_changed
        )
        self.footprints_table.horizontalHeader().sectionDoubleClicked.connect(
            self._on_header_double_clicked
        )
        table_layout.addWidget(self.footprints_table)

        splitter.addWidget(table_widget)

        # Actions group
        actions_widget = QWidget()
        actions_layout = QVBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)

        actions_group = QGroupBox("Actions")
        actions_group.setStyleSheet("QGroupBox { color: #ffffff; font-weight: bold; }")
        actions_inner = QVBoxLayout(actions_group)

        # Select from Map button
        self.select_from_map_btn = QPushButton("Select from Map")
        self.select_from_map_btn.setCheckable(True)
        self.select_from_map_btn.setToolTip("Click on map to select footprints. Ctrl+Click for multiple selection.")
        self.select_from_map_btn.toggled.connect(self._on_selection_mode_toggled)
        self.select_from_map_btn.setEnabled(False)
        actions_inner.addWidget(self.select_from_map_btn)

        # Zoom button
        self.zoom_btn = QPushButton("Zoom to Selected")
        self.zoom_btn.clicked.connect(self._zoom_to_selected)
        self.zoom_btn.setEnabled(False)
        actions_inner.addWidget(self.zoom_btn)

        # Load imagery buttons
        imagery_layout = QHBoxLayout()

        self.load_visual_btn = QPushButton("Load Visual")
        self.load_visual_btn.setToolTip("Load visual (RGB) imagery as COG")
        self.load_visual_btn.clicked.connect(lambda: self._load_imagery("visual"))
        self.load_visual_btn.setEnabled(False)
        imagery_layout.addWidget(self.load_visual_btn)

        self.load_ms_btn = QPushButton("Load MS")
        self.load_ms_btn.setToolTip("Load multispectral imagery as COG")
        self.load_ms_btn.clicked.connect(lambda: self._load_imagery("ms_analytic"))
        self.load_ms_btn.setEnabled(False)
        imagery_layout.addWidget(self.load_ms_btn)

        self.load_pan_btn = QPushButton("Load Pan")
        self.load_pan_btn.setToolTip("Load panchromatic imagery as COG")
        self.load_pan_btn.clicked.connect(lambda: self._load_imagery("pan_analytic"))
        self.load_pan_btn.setEnabled(False)
        imagery_layout.addWidget(self.load_pan_btn)

        actions_inner.addLayout(imagery_layout)

        # Clear layers button
        self.clear_btn = QPushButton("Clear All Layers")
        self.clear_btn.clicked.connect(self._clear_layers)
        actions_inner.addWidget(self.clear_btn)

        actions_layout.addWidget(actions_group)
        splitter.addWidget(actions_widget)

        # Set splitter sizes
        splitter.setSizes([300, 150])

        layout.addWidget(splitter)

        # Status label
        self.status_label = QLabel("Ready - Select an event to begin")
        self.status_label.setStyleSheet("color: #f0f0f0; font-size: 10px; font-weight: 500;")
        layout.addWidget(self.status_label)

    def _load_events(self):
        """Load available events from GitHub."""
        self.refresh_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Loading events...")
        self.status_label.setStyleSheet("color: blue; font-size: 10px;")

        self.fetch_worker = DataFetchWorker(DATASETS_CSV_URL)
        self.fetch_worker.finished.connect(self._on_events_loaded)
        self.fetch_worker.error.connect(self._on_events_error)
        self.fetch_worker.start()

    def _on_events_loaded(self, csv_content):
        """Handle successful events loading."""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)

        # Parse CSV
        self.events = []
        lines = csv_content.strip().split("\n")
        for line in lines[1:]:  # Skip header
            parts = line.split(",")
            if len(parts) >= 2:
                event_name = parts[0].strip()
                count = int(parts[1].strip())
                self.events.append((event_name, count))

        # Sort by name
        self.events.sort(key=lambda x: x[0].lower())

        # Populate combo box
        self.event_combo.clear()
        self.event_combo.addItem("-- Select an event --", None)
        for event_name, count in self.events:
            self.event_combo.addItem(f"{event_name} ({count} tiles)", event_name)

        self.status_label.setText(f"Loaded {len(self.events)} events")
        self.status_label.setStyleSheet("color: #00ffbf; font-size: 10px;")

    def _on_events_error(self, error_msg):
        """Handle events loading error."""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
        self.status_label.setStyleSheet("color: red; font-size: 10px;")

        QMessageBox.warning(
            self,
            "Error Loading Events",
            f"Failed to load events from GitHub:\n\n{error_msg}\n\n"
            "Please check your internet connection and try again.",
        )

    def _on_event_changed(self, index):
        """Handle event selection change."""
        event_name = self.event_combo.currentData()
        self.load_footprints_btn.setEnabled(event_name is not None)
        self.apply_filters_btn.setEnabled(False)
        if event_name:
            self.status_label.setText(f"Selected: {event_name}")
            self.status_label.setStyleSheet("color: gray; font-size: 10px;")
    
    def _on_date_filter_changed(self, state):
        """Handle date filter checkbox state change."""
        enabled = state == Qt.Checked
        self.start_date_edit.setEnabled(enabled)
        self.end_date_edit.setEnabled(enabled)

    def _on_header_double_clicked(self, column):
        """Handle table header double-click for sorting."""
        current_order = self._sort_order.get(column, Qt.DescendingOrder)
        new_order = (
            Qt.AscendingOrder
            if current_order == Qt.DescendingOrder
            else Qt.DescendingOrder
        )
        self._sort_order[column] = new_order
        self.footprints_table.sortItems(column, new_order)

    def _load_footprints(self):
        """Load footprints for the selected event."""
        event_name = self.event_combo.currentData()
        if not event_name:
            return

        self.load_footprints_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText(f"Loading footprints for {event_name}...")
        self.status_label.setStyleSheet("color: blue; font-size: 10px;")

        url = GEOJSON_URL_TEMPLATE.format(event=event_name)
        self.fetch_worker = DataFetchWorker(url, data_type="json")
        self.fetch_worker.finished.connect(self._on_footprints_loaded)
        self.fetch_worker.error.connect(self._on_footprints_error)
        self.fetch_worker.start()
    
    def _load_from_stac(self):
        """Load footprints directly from STAC catalog."""
        stac_url = DEFAULT_STAC_CATALOG_URL
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Loading STAC catalog...")
        self.status_label.setStyleSheet("color: blue; font-size: 10px;")
        
        self.fetch_worker = DataFetchWorker(stac_url, data_type="json")
        self.fetch_worker.finished.connect(self._on_stac_catalog_loaded)
        self.fetch_worker.error.connect(self._on_stac_error)
        self.fetch_worker.start()
    
    def _on_stac_catalog_loaded(self, catalog_str):
        """Handle successful STAC catalog loading."""
        try:
            import json
            catalog_data = json.loads(catalog_str)
        except Exception as e:
            self._on_stac_error(f"Failed to parse STAC catalog: {str(e)}")
            return
        
        self.progress_bar.setVisible(False)
        self.apply_filters_btn.setEnabled(True)
        
        # Parse STAC catalog features
        features = catalog_data.get('features', [])
        if not features:
            # Try links for child collections
            links = catalog_data.get('links', [])
            for link in links:
                if link.get('rel') in ('item', 'child'):
                    QMessageBox.information(
                        self,
                        "STAC Catalog",
                        "This catalog contains multiple collections. "
                        "Please use a specific collection URL or event GeoJSON.",
                    )
                    return
        
        # Store features
        self.all_features = features
        self.current_geojson = catalog_data
        
        # Apply filters and populate
        filtered_features = self._apply_filters_to_features(features)
        self._populate_table(filtered_features)
        
        # Add layer to QGIS (use filtered geojson)
        filtered_geojson = {"type": "FeatureCollection", "features": filtered_features}
        if catalog_data.get("crs"):
            filtered_geojson["crs"] = catalog_data["crs"]
        
        self._add_footprints_layer(filtered_geojson)
        
        self.status_label.setText(
            f"Loaded {len(filtered_features)} of {len(features)} footprints from STAC"
        )
        self.status_label.setStyleSheet("color: green; font-size: 10px;")
    
    def _on_stac_error(self, error_msg):
        """Handle STAC loading error."""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"STAC Error: {error_msg}")
        self.status_label.setStyleSheet("color: red; font-size: 10px;")
        
        QMessageBox.warning(
            self,
            "Error Loading STAC",
            f"Failed to load STAC catalog:\n\n{error_msg}\n\n"
            "Please check the URL and try again.",
        )

    def _on_footprints_loaded(self, geojson_str):
        """Handle successful footprints loading."""
        try:
            import json
            geojson_data = json.loads(geojson_str)
        except Exception as e:
            self._on_footprints_error(f"Failed to parse GeoJSON: {str(e)}")
            return

        self.progress_bar.setVisible(False)
        self.load_footprints_btn.setEnabled(True)
        self.apply_filters_btn.setEnabled(True)
        self.current_geojson = geojson_data

        # Store all features
        self.all_features = geojson_data.get("features", [])
        
        # Apply filters and populate table
        filtered_features = self._apply_filters_to_features(self.all_features)

        self._populate_table(filtered_features)
        
        # Add layer to QGIS (use filtered geojson)
        filtered_geojson = {"type": "FeatureCollection", "features": filtered_features}
        if geojson_data.get("crs"):
            filtered_geojson["crs"] = geojson_data["crs"]
        
        self._add_footprints_layer(filtered_geojson)

        self.status_label.setText(
            f"Loaded {len(filtered_features)} of {len(self.all_features)} footprints"
        )
        self.status_label.setStyleSheet("color: green; font-size: 10px;")

    def _on_footprints_error(self, error_msg):
        """Handle footprints loading error."""
        self.progress_bar.setVisible(False)
        self.load_footprints_btn.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
        self.status_label.setStyleSheet("color: red; font-size: 10px;")

        QMessageBox.warning(
            self,
            "Error Loading Footprints",
            f"Failed to load footprints:\n\n{error_msg}",
        )

    def _apply_filters_to_features(self, features):
        """Apply cloud and date filters to features."""
        filtered = []
        max_cloud = self.cloud_spin.value()
        date_filter = self.date_check.isChecked()

        for feature in features:
            props = feature.get("properties", {})

            # Cloud filter
            cloud = props.get("eo:cloud_cover")
            if cloud is not None and cloud > max_cloud:
                continue

            # Date filter
            if date_filter:
                datetime_str = props.get("datetime", "")
                if not self._is_date_in_range(
                    datetime_str,
                    self.start_date_edit.date().toString("yyyy-MM-dd"),
                    self.end_date_edit.date().toString("yyyy-MM-dd"),
                ):
                    continue

            filtered.append(feature)

        return filtered

    def _is_date_in_range(self, datetime_str, start_date, end_date):
        """Check if datetime string is within date range."""
        if not datetime_str:
            return False
        try:
            date_part = datetime_str[:10]
            return start_date <= date_part <= end_date
        except (IndexError, TypeError):
            return False
    
    def _apply_current_filters(self):
        """Reapply filters to currently loaded features."""
        if not hasattr(self, 'all_features'):
            return
        
        filtered_features = self._apply_filters_to_features(self.all_features)
        self._populate_table(filtered_features)

        # Refresh footprints layer to reflect filtered subset
        filtered_geojson = {"type": "FeatureCollection", "features": filtered_features}
        if getattr(self, "current_geojson", None) and isinstance(self.current_geojson, dict):
            if self.current_geojson.get("crs"):
                filtered_geojson["crs"] = self.current_geojson["crs"]
        self._add_footprints_layer(filtered_geojson)
        
        self.status_label.setText(
            f"Showing {len(filtered_features)} of {len(self.all_features)} footprints"
        )
        self.status_label.setStyleSheet("color: green; font-size: 10px;")

    def _populate_table(self, features):
        """Populate table with footprint features."""
        # Disable sorting while populating
        self.footprints_table.setSortingEnabled(False)
        self.footprints_table.setRowCount(0)
        self.footprints_table.setRowCount(len(features))

        for row, feature in enumerate(features):
            props = feature.get("properties", {})

            # Date
            datetime_str = props.get("datetime", "")
            date_str = datetime_str[:10] if datetime_str else ""
            self.footprints_table.setItem(row, 0, QTableWidgetItem(date_str))

            # Platform
            platform = props.get("platform", "")
            self.footprints_table.setItem(row, 1, QTableWidgetItem(platform))

            # GSD
            gsd = props.get("gsd", "")
            gsd_item = NumericTableWidgetItem(str(gsd))
            self.footprints_table.setItem(row, 2, gsd_item)

            # Cloud %
            cloud = props.get("eo:cloud_cover", "")
            cloud_item = NumericTableWidgetItem(str(cloud))
            self.footprints_table.setItem(row, 3, cloud_item)

            # Catalog ID
            catalog_id = props.get("catalog_id", "")
            self.footprints_table.setItem(row, 4, QTableWidgetItem(catalog_id))

            # Quadkey
            quadkey = props.get("quadkey", "")
            self.footprints_table.setItem(row, 5, QTableWidgetItem(quadkey))

            # Store row index and feature object for mapping
            # Row index is used locally; we'll map to layer feature IDs later
            self.footprints_table.item(row, 0).setData(Qt.UserRole, row)
            self.footprints_table.item(row, 0).setData(Qt.UserRole + 1, feature)

        # Clear feature ID mapping (will be updated when layer is created)
        self._feature_id_to_quadkey = {}
        self._quadkey_to_feature_id = {}

        # Re-enable sorting
        self.footprints_table.setSortingEnabled(True)

    def _build_feature_id_mapping(self):
        """Build mapping between layer feature IDs and quadkeys."""
        self._feature_id_to_quadkey = {}
        self._quadkey_to_feature_id = {}
        
        if not self._is_footprints_layer_valid():
            get_logger().warning("Cannot build feature mapping: layer is invalid")
            return
        
        try:
            # Iterate through all features in the layer and build mapping
            for feature in self.footprints_layer.getFeatures():
                fid = feature.id()
                # Get quadkey from feature attributes (unique per tile)
                quadkey = feature.attribute('quadkey')
                if quadkey:
                    self._feature_id_to_quadkey[fid] = quadkey
                    self._quadkey_to_feature_id[quadkey] = fid
            
            get_logger().info(f"Built feature ID mapping: {len(self._feature_id_to_quadkey)} features mapped")
            get_logger().debug(f"Feature ID to Quadkey mapping sample: {dict(list(self._feature_id_to_quadkey.items())[:3])}")
        except Exception as e:
            get_logger().error(f"Failed to build feature ID mapping: {e}", exc_info=True)

    def _is_footprints_layer_valid(self):
        """Check if the cached footprints layer reference is still valid."""
        if self.footprints_layer is None:
            return False
        try:
            _ = self.footprints_layer.id()
            return True
        except RuntimeError:
            self.footprints_layer = None
            return False

    def _on_footprints_layer_deleted(self):
        """Clear cached reference when the layer is deleted externally."""
        self.footprints_layer = None
        self._feature_id_to_quadkey = {}
        self._quadkey_to_feature_id = {}
        
        # Disable selection mode button and deactivate if active
        self.select_from_map_btn.setEnabled(False)
        if self.select_from_map_btn.isChecked():
            self.select_from_map_btn.setChecked(False)

    def _add_footprints_layer(self, geojson_data):
        """Create and add a footprints vector layer to the project."""
        try:
            import json
            import os
            import tempfile

            # Remove previous footprints layer if it exists
            if self._is_footprints_layer_valid():
                try:
                    QgsProject.instance().removeMapLayer(self.footprints_layer.id())
                except Exception:
                    pass
                self.footprints_layer = None

            event_name = self.event_combo.currentText().split(" (")[0] if hasattr(self, "event_combo") else "Event"

            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"maxar_{event_name}_footprints.geojson")

            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(geojson_data, f)

            layer_name = f"Vantor - {event_name} Footprints"
            self.footprints_layer = QgsVectorLayer(temp_file, layer_name, "ogr")

            if not self.footprints_layer or not self.footprints_layer.isValid():
                get_logger().warning(f"Failed to create footprints layer for {event_name}")
                return

            # Set CRS to WGS84
            try:
                self.footprints_layer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
            except Exception:
                pass

            # Apply styling
            self._apply_footprints_style(self.footprints_layer)

            # Connect signals for selection sync and cleanup
            try:
                self.footprints_layer.selectionChanged.connect(self._on_layer_selection_changed)
            except Exception:
                pass
            try:
                self.footprints_layer.willBeDeleted.connect(self._on_footprints_layer_deleted)
            except Exception:
                pass

            # Add to project and zoom
            QgsProject.instance().addMapLayer(self.footprints_layer)
            
            # Build mapping between feature IDs and table rows
            self._build_feature_id_mapping()
            
            # Enable selection mode button now that we have footprints
            self.select_from_map_btn.setEnabled(True)
            
            self._zoom_to_layer_extent(self.footprints_layer)
        except Exception as e:
            get_logger().error(f"Error creating footprints layer: {e}")

    def _apply_footprints_style(self, layer):
        """Apply semi-transparent styling to footprints layer."""
        try:
            if layer is None or layer.renderer() is None:
                return
            
            opacity = self.settings.value("MaxarOpenData/opacity", 50, type=int)
            symbol = QgsFillSymbol.createSimple(
                {
                    "color": "31,120,180,128",
                    "outline_color": "0,0,255,255",
                    "outline_width": "0.5",
                }
            )
            try:
                symbol.setOpacity(opacity / 100.0)
            except Exception:
                pass

            renderer = layer.renderer()
            if renderer is not None:
                renderer.setSymbol(symbol)
            layer.triggerRepaint()
        except Exception as e:
            get_logger().warning(f"Failed to apply footprints style: {e}")

    def _zoom_to_layer_extent(self, layer):
        """Zoom map canvas to the extent of the layer respecting CRS."""
        try:
            if not self.settings.value("MaxarOpenData/auto_zoom", True, type=bool):
                return

            extent = layer.extent()
            canvas = self.iface.mapCanvas()
            layer_crs = layer.crs()
            canvas_crs = canvas.mapSettings().destinationCrs()

            if layer_crs != canvas_crs:
                transform = QgsCoordinateTransform(layer_crs, canvas_crs, QgsProject.instance())
                extent = transform.transformBoundingBox(extent)

            canvas.setExtent(extent)
            canvas.refresh()
        except Exception as e:
            get_logger().warning(f"Failed to zoom to layer extent: {e}")

    def _on_layer_selection_changed(self):
        """Sync map selection to table selection (map -> table)."""
        if self._updating_selection or not self._is_footprints_layer_valid():
            return

        self._updating_selection = True
        try:
            selected_ids = set(self.footprints_layer.selectedFeatureIds())
            get_logger().info(f"Layer selection changed: {len(selected_ids)} features selected")
            get_logger().debug(f"Selected feature IDs: {selected_ids}")
            
            if not selected_ids:
                self.footprints_table.clearSelection()
                return

            # Use the pre-built mapping if available, otherwise build it
            if not self._feature_id_to_quadkey:
                get_logger().warning("Feature ID mapping is empty, rebuilding...")
                self._build_feature_id_mapping()

            # Convert feature IDs to quadkeys
            selected_quadkeys = set()
            for fid in selected_ids:
                quadkey = self._feature_id_to_quadkey.get(fid)
                if quadkey:
                    selected_quadkeys.add(str(quadkey))
                    get_logger().debug(f"Feature ID {fid} -> Quadkey '{quadkey}'")
                else:
                    get_logger().warning(f"Feature ID {fid} not found in mapping")
            
            get_logger().info(f"Selected quadkeys: {selected_quadkeys}")

            # Find rows with matching quadkeys and select them
            self.footprints_table.clearSelection()
            first_row = None
            matched_rows = []
            
            for row_idx in range(self.footprints_table.rowCount()):
                quadkey_item = self.footprints_table.item(row_idx, 5)  # Column 5 is Quadkey
                if quadkey_item:
                    table_quadkey = str(quadkey_item.text()).strip()
                    if table_quadkey in selected_quadkeys:
                        get_logger().debug(f"Row {row_idx}: quadkey '{table_quadkey}' MATCHES")
                        self.footprints_table.selectRow(row_idx)
                        matched_rows.append(row_idx)
                        if first_row is None:
                            first_row = row_idx
                    else:
                        get_logger().debug(f"Row {row_idx}: quadkey '{table_quadkey}' does not match")
            
            get_logger().info(f"Matched {len(matched_rows)} rows: {matched_rows}")

            # Scroll to first selected row
            if first_row is not None:
                try:
                    self.footprints_table.scrollToItem(
                        self.footprints_table.item(first_row, 0),
                        QTableWidget.PositionAtCenter
                    )
                    get_logger().debug(f"Scrolled to row {first_row}")
                except Exception as scroll_error:
                    get_logger().warning(f"Failed to scroll to row {first_row}: {scroll_error}")
        except Exception as e:
            get_logger().error(f"Error in layer selection sync: {e}", exc_info=True)
        finally:
            self._updating_selection = False

    def _on_footprint_selection_changed(self):
        """Handle footprint selection change in table."""
        selected_rows = self.footprints_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0

        # Update button states
        self.zoom_btn.setEnabled(has_selection)
        self.load_visual_btn.setEnabled(has_selection)
        self.load_ms_btn.setEnabled(has_selection)
        self.load_pan_btn.setEnabled(has_selection)
        
        # Update status
        if has_selection:
            self.status_label.setText(f"{len(selected_rows)} footprint(s) selected")
            self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        else:
            self.status_label.setText("No footprints selected")
            self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        
        # Sync selection to map layer (table -> map)
        if not self._updating_selection and self._is_footprints_layer_valid():
            self._updating_selection = True
            try:
                # Get quadkeys from selected rows
                selected_quadkeys = []
                for model_index in selected_rows:
                    row = model_index.row()
                    quadkey_item = self.footprints_table.item(row, 5)  # Column 5 is Quadkey
                    if quadkey_item:
                        quadkey = quadkey_item.text()
                        if quadkey:
                            selected_quadkeys.append(quadkey)
                
                get_logger().debug(f"Table selected quadkeys: {selected_quadkeys}")
                
                # Convert quadkeys to feature IDs using mapping
                selected_feature_ids = []
                for quadkey in selected_quadkeys:
                    feature_id = self._quadkey_to_feature_id.get(quadkey)
                    if feature_id is not None:
                        selected_feature_ids.append(feature_id)
                    else:
                        get_logger().warning(f"Quadkey {quadkey} not found in reverse mapping")
                
                get_logger().debug(f"Mapped to feature IDs: {selected_feature_ids}")
                
                # Select features on the map layer
                if selected_feature_ids:
                    self.footprints_layer.selectByIds(selected_feature_ids)
                else:
                    # No valid feature IDs found, deselect all
                    self.footprints_layer.selectByIds([])
            except Exception as e:
                get_logger().error(f"Error syncing table selection to map: {e}", exc_info=True)
            finally:
                self._updating_selection = False

    def _get_selected_features(self):
        """Get selected features from table."""
        features = []
        selected_rows = self.footprints_table.selectionModel().selectedRows()

        for model_index in selected_rows:
            row = model_index.row()
            item = self.footprints_table.item(row, 0)
            if item:
                feature = item.data(Qt.UserRole + 1)
                if feature:
                    features.append(feature)

        return features

    def _on_selection_mode_toggled(self, checked):
        """Handle selection mode toggle."""
        if not self._is_footprints_layer_valid():
            self.select_from_map_btn.setChecked(False)
            QMessageBox.warning(self.iface.mainWindow(), "Warning", "No footprints layer loaded. Load footprints first.")
            return
        
        if checked:
            self._activate_selection_mode()
        else:
            self._deactivate_selection_mode()
    
    def _activate_selection_mode(self):
        """Activate interactive selection mode from map."""
        try:
            canvas = self.iface.mapCanvas()
            
            # Verify layer validity
            if not self.footprints_layer or not self.footprints_layer.isValid():
                get_logger().error("Footprints layer is not valid, cannot activate selection mode")
                self.select_from_map_btn.setChecked(False)
                return
            
            # Always create a new selection tool (old one may have been deleted by QGIS)
            self.selection_tool = FootprintSelectionTool(
                canvas,
                self.footprints_layer
            )
            get_logger().info(f"FootprintSelectionTool created with layer: {self.footprints_layer.name()}")
            get_logger().info(f"Layer feature count: {sum(1 for _ in self.footprints_layer.getFeatures())}")
            
            # Store previous tool and activate selection tool
            self._previous_map_tool = canvas.mapTool()
            canvas.setMapTool(self.selection_tool)
            get_logger().info("Selection tool set as active map tool")
            
            self.select_from_map_btn.setText("✓ Selecting from Map")
            self.select_from_map_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
            get_logger().info("Selection mode activated")
        except Exception as e:
            get_logger().error(f"Error activating selection mode: {e}", exc_info=True)
            self.select_from_map_btn.setChecked(False)
    
    def _deactivate_selection_mode(self):
        """Deactivate interactive selection mode."""
        try:
            canvas = self.iface.mapCanvas()
            
            # Restore previous tool (check if it still exists)
            if self._previous_map_tool:
                try:
                    # Try to set the previous tool, but it might have been deleted
                    canvas.setMapTool(self._previous_map_tool)
                    get_logger().info("Restored previous map tool")
                except RuntimeError:
                    # Previous tool was deleted, just unset the current tool
                    canvas.unsetMapTool(self.selection_tool)
                    get_logger().warning("Previous map tool was deleted, unset current tool")
                self._previous_map_tool = None
            
            self.select_from_map_btn.setText("Select from Map")
            self.select_from_map_btn.setStyleSheet("")
            get_logger().info("Selection mode deactivated")
        except Exception as e:
            get_logger().error(f"Error deactivating selection mode: {e}", exc_info=True)
    
    def _zoom_to_selected(self):
        """Zoom to selected footprints."""
        features = self._get_selected_features()
        if not features:
            return

        # Calculate bounding box
        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")

        for feature in features:
            coords = feature.get("geometry", {}).get("coordinates", [[]])
            if coords:
                for ring in coords:
                    for coord in ring:
                        min_x = min(min_x, coord[0])
                        max_x = max(max_x, coord[0])
                        min_y = min(min_y, coord[1])
                        max_y = max(max_y, coord[1])

        if min_x != float("inf"):
            from qgis.core import QgsRectangle, QgsCoordinateTransform, QgsCoordinateReferenceSystem

            canvas = self.iface.mapCanvas()
            extent = QgsRectangle(min_x, min_y, max_x, max_y)

            # Transform from WGS84 if needed
            source_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            dest_crs = canvas.mapSettings().destinationCrs()

            if source_crs != dest_crs:
                transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
                extent = transform.transformBoundingBox(extent)

            canvas.setExtent(extent)
            canvas.refresh()

    def _load_imagery(self, imagery_type):
        """Load imagery for selected footprints."""
        features = self._get_selected_features()
        if not features:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select one or more footprints from the table.",
            )
            return

        imagery_label = imagery_type.replace("_", " ").title()
        get_logger().info(f"Loading {imagery_type} imagery for {len(features)} selected footprint(s)")

        # Disable buttons during loading
        self.load_visual_btn.setEnabled(False)
        self.load_ms_btn.setEnabled(False)
        self.load_pan_btn.setEnabled(False)

        QApplication.setOverrideCursor(Qt.WaitCursor)

        loaded_count = 0
        not_available_count = 0
        failed_count = 0

        for idx, feature in enumerate(features):
            props = feature.get("properties", {})
            url = props.get(imagery_type)

            if not url:
                not_available_count += 1
                get_logger().debug(f"Feature {idx+1}: No {imagery_type} URL available")
                continue

            # Create layer name
            catalog_id = props.get("catalog_id", "unknown")
            quadkey = props.get("quadkey", "")
            date = props.get("datetime", "")[:10]
            layer_name = f"Vantor {imagery_type} - {catalog_id} - {quadkey} ({date})"

            # Load as COG using GDAL vsicurl
            cog_url = f"/vsicurl/{url}"
            get_logger().debug(f"Loading layer {idx+1}/{len(features)}: {layer_name}")
            get_logger().debug(f"COG URL: {cog_url}")
            
            layer = QgsRasterLayer(cog_url, layer_name, "gdal")

            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
                loaded_count += 1
                get_logger().info(f"Successfully loaded layer: {layer_name}")
            else:
                failed_count += 1
                get_logger().warning(f"Failed to load layer: {layer_name} - Layer is not valid")

        QApplication.restoreOverrideCursor()

        # Re-enable buttons
        self.load_visual_btn.setEnabled(True)
        self.load_ms_btn.setEnabled(True)
        self.load_pan_btn.setEnabled(True)

        # Refresh canvas to show new layers
        self.iface.mapCanvas().refresh()

        # Report results
        get_logger().info(
            f"Imagery loading complete: {loaded_count} loaded, "
            f"{not_available_count} not available, {failed_count} failed"
        )
        
        if loaded_count > 0:
            self.status_label.setText(f"Loaded {loaded_count} {imagery_label} layer(s)")
            self.status_label.setStyleSheet("color: green; font-size: 10px;")
            self.iface.messageBar().pushSuccess(
                "Vantor EO Data", f"Loaded {loaded_count} {imagery_label} layer(s)"
            )

        if not_available_count > 0:
            self.iface.messageBar().pushInfo(
                "Vantor EO Data",
                f"{not_available_count} footprint(s) don't have {imagery_label} imagery",
            )
        
        if failed_count > 0:
            self.iface.messageBar().pushWarning(
                "Vantor EO Data",
                f"{failed_count} layer(s) failed to load - check layer validity",
            )

    def _clear_layers(self):
        """Clear all Vantor layers from the project."""
        layers_to_remove = []

        for layer_id, layer in QgsProject.instance().mapLayers().items():
            if layer.name().startswith("Vantor"):
                layers_to_remove.append(layer_id)

        for layer_id in layers_to_remove:
            QgsProject.instance().removeMapLayer(layer_id)

        self.footprints_layer = None
        self.current_geojson = None
        self.footprints_table.setRowCount(0)

        self.iface.mapCanvas().refresh()

        # Disable action buttons
        self.zoom_btn.setEnabled(False)
        self.load_visual_btn.setEnabled(False)
        self.load_ms_btn.setEnabled(False)
        self.load_pan_btn.setEnabled(False)

        self.status_label.setText("Cleared all Vantor layers")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")

    def cleanup(self):
        """Cleanup resources when closing the dock widget."""
        try:
            # Deactivate selection mode if active
            if self.select_from_map_btn.isChecked():
                self.select_from_map_btn.setChecked(False)
            
            # Stop worker thread
            if self.fetch_worker:
                if self.fetch_worker.isRunning():
                    self.fetch_worker.quit()
                    self.fetch_worker.wait(1000)  # Wait up to 1 second
                self.fetch_worker = None
            
            # Disconnect layer signals to prevent errors
            if self.footprints_layer is not None:
                try:
                    self.footprints_layer.selectionChanged.disconnect(self._on_layer_selection_changed)
                except (RuntimeError, TypeError):
                    pass
                try:
                    self.footprints_layer.willBeDeleted.disconnect(self._on_footprints_layer_deleted)
                except (RuntimeError, TypeError):
                    pass
                self.footprints_layer = None
        except Exception as e:
            get_logger().debug(f"Error during cleanup: {e}")

    def closeEvent(self, event):
        """Handle dock widget close event."""
        self.cleanup()
        event.accept()
