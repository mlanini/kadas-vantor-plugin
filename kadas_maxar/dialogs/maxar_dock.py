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
# GITHUB_RAW_URL = "https://raw.githubusercontent.com/opengeos/maxar-open-data/refs/heads/master"
# DATASETS_CSV_URL = f"{GITHUB_RAW_URL}/datasets.csv"
# GEOJSON_URL_TEMPLATE = f"{GITHUB_RAW_URL}/datasets/{{event}}.geojson"

# Usa solo il catalogo STAC come sorgente eventi:
DEFAULT_STAC_CATALOG_URL = "https://maxar-opendata.s3.dualstack.us-west-2.amazonaws.com/events/catalog.json"


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


from qgis.PyQt.QtCore import QUrl, QEventLoop, QByteArray
from qgis.core import QgsNetworkAccessManager

class DataFetchWorker(QThread):
    """Worker thread for fetching data from GitHub."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, data_type="text"):
        super().__init__()
        self.url = url
        self.data_type = data_type

    def run(self):
        """Fetch data in background using QGIS network manager (proxy aware)."""
        try:
            nam = QgsNetworkAccessManager.instance()
            req = QUrl(self.url)
            reply = nam.get(nam.createRequest(QgsNetworkAccessManager.GetOperation, req, QByteArray()))
            loop = QEventLoop()
            reply.finished.connect(loop.quit)
            loop.exec_()
            if reply.error():
                raise Exception(reply.errorString())
            data = reply.readAll().data().decode('utf-8')
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
        """Carica gli eventi disponibili dai child del catalogo STAC."""
        self.refresh_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Caricamento eventi dal catalogo STAC...")
        self.status_label.setStyleSheet("color: blue; font-size: 10px;")

        self.fetch_worker = DataFetchWorker(DEFAULT_STAC_CATALOG_URL, data_type="json")
        self.fetch_worker.finished.connect(self._on_stac_events_loaded)
        self.fetch_worker.error.connect(self._on_events_error)
        self.fetch_worker.start()

    def _on_stac_events_loaded(self, catalog_str):
        """Gestisce il caricamento degli eventi dai child del catalogo STAC."""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)

        import json
        try:
            catalog_data = json.loads(catalog_str)
        except Exception as e:
            self._on_events_error(f"Impossibile leggere il catalogo STAC: {str(e)}")
            return

        # Estrai gli eventi dai link di tipo 'child'
        self.events = []
        links = catalog_data.get("links", [])
        for link in links:
            if link.get("rel") == "child":
                href = link.get("href")
                title = link.get("title") or href.split("/")[-1]
                self.events.append((title, href))

        # Ordina per nome evento
        self.events.sort(key=lambda x: x[0].lower())

        # Popola la combo box
        self.event_combo.clear()
        self.event_combo.addItem("-- Seleziona un evento --", None)
        for event_name, href in self.events:
            self.event_combo.addItem(event_name, href)

        self.status_label.setText(f"Caricati {len(self.events)} eventi dal catalogo STAC")
        self.status_label.setStyleSheet("color: #00ffbf; font-size: 10px;")

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
        """Gestisce la selezione di un evento."""
        event_href = self.event_combo.currentData()
        self.load_footprints_btn.setEnabled(event_href is not None)
        self.apply_filters_btn.setEnabled(False)
        if event_href:
            self.status_label.setText(f"Selezionato: {self.event_combo.currentText()}")
            self.status_label.setStyleSheet("color: gray; font-size: 10px;")
    
    def _on_date_filter_changed(self, state):
        """Abilita/disabilita i campi data in base allo stato della checkbox."""
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
        """Carica i footprints per l'evento selezionato (GeoJSON STAC)."""
        event_href = self.event_combo.currentData()
        if not event_href:
            return

        self.load_footprints_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText(f"Caricamento footprints per {self.event_combo.currentText()}...")
        self.status_label.setStyleSheet("color: blue; font-size: 10px;")

        self.fetch_worker = DataFetchWorker(event_href, data_type="json")
        self.fetch_worker.finished.connect(self._on_footprints_loaded)
        self.fetch_worker.error.connect(self._on_footprints_error)
        self.fetch_worker.start()

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


from qgis.PyQt.QtCore import QUrl, QEventLoop, QByteArray
from qgis.core import QgsNetworkAccessManager

class DataFetchWorker(QThread):
    """Worker thread for fetching data from GitHub."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, data_type="text"):
        super().__init__()
        self.url = url
        self.data_type = data_type

    def run(self):
        """Fetch data in background using QGIS network manager (proxy aware)."""
        try:
            nam = QgsNetworkAccessManager.instance()
            req = QUrl(self.url)
            reply = nam.get(nam.createRequest(QgsNetworkAccessManager.GetOperation, req, QByteArray()))
            loop = QEventLoop()
            reply.finished.connect(loop.quit)
            loop.exec_()
            if reply.error():
                raise Exception(reply.errorString())
            data = reply.readAll().data().decode('utf-8')
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
        """Carica gli eventi disponibili dai child del catalogo STAC."""
        self.refresh_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Caricamento eventi dal catalogo STAC...")
        self.status_label.setStyleSheet("color: blue; font-size: 10px;")

        self.fetch_worker = DataFetchWorker(DEFAULT_STAC_CATALOG_URL, data_type="json")
        self.fetch_worker.finished.connect(self._on_stac_events_loaded)
        self.fetch_worker.error.connect(self._on_events_error)
        self.fetch_worker.start()

    def _on_stac_events_loaded(self, catalog_str):
        """Gestisce il caricamento degli eventi dai child del catalogo STAC."""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)

        import json
        try:
            catalog_data = json.loads(catalog_str)
        except Exception as e:
            self._on_events_error(f"Impossibile leggere il catalogo STAC: {str(e)}")
            return

        # Estrai gli eventi dai link di tipo 'child'
        self.events = []
        links = catalog_data.get("links", [])
        for link in links:
            if link.get("rel") == "child":
                href = link.get("href")
                title = link.get("title") or href.split("/")[-1]
                self.events.append((title, href))

        # Ordina per nome evento
        self.events.sort(key=lambda x: x[0].lower())

        # Popola la combo box
        self.event_combo.clear()
        self.event_combo.addItem("-- Seleziona un evento --", None)
        for event_name, href in self.events:
            self.event_combo.addItem(event_name, href)

        self.status_label.setText(f"Caricati {len(self.events)} eventi dal catalogo STAC")
        self.status_label.setStyleSheet("color: #00ffbf; font-size: 10px;")

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
        """Gestisce la selezione di un evento."""
        event_href = self.event_combo.currentData()
        self.load_footprints_btn.setEnabled(event_href is not None)
        self.apply_filters_btn.setEnabled(False)
        if event_href:
            self.status_label.setText(f"Selezionato: {self.event_combo.currentText()}")
            self.status_label.setStyleSheet("color: gray; font-size: 10px;")
    
    def _on_date_filter_changed(self, state):
        """Abilita/disabilita i campi data in base allo stato della checkbox."""
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
        """Carica i footprints per l'evento selezionato (GeoJSON STAC)."""
        event_href = self.event_combo.currentData()
        if not event_href:
            return

        self.load_footprints_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText(f"Caricamento footprints per {self.event_combo.currentText()}...")
        self.status_label.setStyleSheet("color: blue; font-size: 10px;")

        self.fetch_worker = DataFetchWorker(event_href, data_type="json")
        self.fetch_worker.finished.connect(self._on_footprints_loaded)
        self.fetch_worker.error.connect(self._on_footprints_error)
        self.fetch_worker.start()

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


from qgis.PyQt.QtCore import QUrl, QEventLoop, QByteArray
from qgis.core import QgsNetworkAccessManager

class DataFetchWorker(QThread):
    """Worker thread for fetching data from GitHub."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, data_type="text"):
        super().__init__()
        self.url = url
        self.data_type = data_type

    def run(self):
        """Fetch data in background using QGIS network manager (proxy aware)."""
        try:
            nam = QgsNetworkAccessManager.instance()
            req = QUrl(self.url)
            reply = nam.get(nam.createRequest(QgsNetworkAccessManager.GetOperation, req, QByteArray()))
            loop = QEventLoop()
            reply.finished.connect(loop.quit)
            loop.exec_()
            if reply.error():
                raise Exception(reply.errorString())
            data = reply.readAll().data().decode('utf-8')
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
        """Carica gli eventi disponibili dai child del catalogo STAC."""
        self.refresh_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Caricamento eventi dal catalogo STAC...")
        self.status_label.setStyleSheet("color: blue; font-size: 10px;")

        self.fetch_worker = DataFetchWorker(DEFAULT_STAC_CATALOG_URL, data_type="json")
        self.fetch_worker.finished.connect(self._on_stac_events_loaded)
        self.fetch_worker.error.connect(self._on_events_error)
        self.fetch_worker.start()

    def _on_stac_events_loaded(self, catalog_str):
        """Gestisce il caricamento degli eventi dai child del catalogo STAC."""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)

        import json
        try:
            catalog_data = json.loads(catalog_str)
        except Exception as e:
            self._on_events_error(f"Impossibile leggere il catalogo STAC: {str(e)}")
            return

        # Estrai gli eventi dai link di tipo 'child'
        self.events = []
        links = catalog_data.get("links", [])
        for link in links:
            if link.get("rel") == "child":
                href = link.get("href")
                title = link.get("title") or href.split("/")[-1]
                self.events.append((title, href))

        # Ordina per nome evento
        self.events.sort(key=lambda x: x[0].lower())

        # Popola la combo box
        self.event_combo.clear()
        self.event_combo.addItem("-- Seleziona un evento --", None)
        for event_name, href in self.events:
            self.event_combo.addItem(event_name, href)

        self.status_label.setText(f"Caricati {len(self.events)} eventi dal catalogo STAC")
        self.status_label.setStyleSheet("color: #00ffbf; font-size: 10px;")

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
        """Gestisce la selezione di un evento."""
        event_href = self.event_combo.currentData()
        self.load_footprints_btn.setEnabled(event_href is not None)
        self.apply_filters_btn.setEnabled(False)
        if event_href:
            self.status_label.setText(f"Selezionato: {self.event_combo.currentText()}")
            self.status_label.setStyleSheet("color: gray; font-size: 10px;")
    
    def _on_date_filter_changed(self, state):
        """Abilita/disabilita i campi data in base allo stato della checkbox."""
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
        """Carica i footprints per l'evento selezionato (GeoJSON STAC)."""
        event_href = self.event_combo.currentData()
        if not event_href:
            return

        self.load_footprints_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText(f"Caricamento footprints per {self.event_combo.currentText()}...")
        self.status_label.setStyleSheet("color: blue; font-size: 10px;")

        self.fetch_worker = DataFetchWorker(event_href, data_type="json")
        self.fetch_worker.finished.connect(self._on_footprints_loaded)
        self.fetch_worker.error.connect(self._on_footprints_error)
        self.fetch_worker.start()