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

import json
from kadas_maxar.logger import get_logger

# GitHub URLs per i dati Maxar Open Data (stesso pattern del plugin originale)
GITHUB_RAW_URL = "https://raw.githubusercontent.com/opengeos/maxar-open-data/master"
DATASETS_CSV_URL = f"{GITHUB_RAW_URL}/datasets.csv"
GEOJSON_URL_TEMPLATE = f"{GITHUB_RAW_URL}/datasets/{{event}}.geojson"


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


from qgis.PyQt.QtCore import QUrl, QEventLoop, QByteArray, QTimer
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.core import QgsNetworkAccessManager

class DataFetchWorker(QThread):
    """Worker thread for fetching data from STAC endpoint."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, data_type="text", timeout=120):
        super().__init__()
        self.url = url
        self.data_type = data_type
        self.timeout = timeout

    def run(self):
        """Fetch data in background using QGIS network manager (proxy aware)."""
        try:
            # Validazione URL prima di procedere
            if not self.url:
                raise Exception("URL is empty or None")
            
            if not isinstance(self.url, str):
                raise Exception(f"URL must be a string, got {type(self.url)}")
            
            if not self.url.startswith(('http://', 'https://')):
                raise Exception(f"Invalid URL protocol. URL must start with http:// or https://, got: {self.url}")
            
            get_logger().info(f"Fetching STAC data from: {self.url}")
            
            nam = QgsNetworkAccessManager.instance()
            req = QNetworkRequest(QUrl(self.url))
            
            # Configura headers per compatibilità
            req.setRawHeader(b"User-Agent", b"KADAS-Vantor-Plugin/0.1.0")
            req.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork)
            
            get_logger().debug(f"Network request created for: {req.url().toString()}")
            
            reply = nam.get(req)
            loop = QEventLoop()
            reply.finished.connect(loop.quit)
            
            # Timeout timer
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(loop.quit)
            timer.start(self.timeout * 1000)
            
            get_logger().debug(f"Waiting for network response (timeout: {self.timeout}s)...")
            loop.exec_()
            
            # Verifica timeout
            if not reply.isFinished():
                reply.abort()
                error_msg = f"Request timeout after {self.timeout} seconds"
                get_logger().error(error_msg)
                raise Exception(error_msg)
            
            # Verifica errori di rete
            if reply.error():
                error_code = reply.error()
                error_msg = reply.errorString()
                status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
                
                detailed_error = f"Network error ({error_code}): {error_msg}"
                if status_code:
                    detailed_error += f" - HTTP {status_code}"
                
                get_logger().error(f"{detailed_error} for URL: {self.url}")
                raise Exception(detailed_error)
            
            # Verifica status code HTTP
            status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            get_logger().debug(f"HTTP Status Code: {status_code}")
            
            if status_code and status_code >= 400:
                error_msg = f"HTTP error {status_code} from {self.url}"
                get_logger().error(error_msg)
                raise Exception(error_msg)
            
            # Leggi i dati
            data = reply.readAll().data().decode('utf-8')
            get_logger().info(f"Successfully fetched {len(data)} bytes from STAC endpoint")
            
            self.finished.emit(data)
            
        except Exception as e:
            error_msg = str(e)
            get_logger().error(f"Error in DataFetchWorker: {error_msg}", exc_info=True)
            self.error.emit(error_msg)


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

        # Max cloud cover (SLIDER)
        cloud_label = QLabel("Max Cloud Cover:")
        cloud_label.setStyleSheet("color: #f0f0f0; font-weight: 500;")
        from qgis.PyQt.QtWidgets import QSlider
        self.cloud_slider = QSlider(Qt.Horizontal)
        self.cloud_slider.setRange(0, 100)
        self.cloud_slider.setValue(100)
        self.cloud_slider.setTickInterval(10)
        self.cloud_slider.setTickPosition(QSlider.TicksBelow)
        self.cloud_slider.setToolTip("Max cloud cover (%)")
        self.cloud_slider.setMinimumWidth(120)
        self.cloud_slider.valueChanged.connect(lambda v: self.cloud_value_label.setText(f"{v} %"))
        self.cloud_value_label = QLabel("100 %")
        self.cloud_value_label.setStyleSheet("color: #f0f0f0; font-size: 10px;")
        cloud_slider_layout = QHBoxLayout()
        cloud_slider_layout.addWidget(self.cloud_slider)
        cloud_slider_layout.addWidget(self.cloud_value_label)
        filter_layout.addRow(cloud_label, cloud_slider_layout)

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
        self.load_footprints_btn.setEnabled(True)
        load_btn_layout.addWidget(self.load_footprints_btn)
        
        # Apply filters button
        self.apply_filters_btn = QPushButton("Apply Filters")
        self.apply_filters_btn.clicked.connect(self._apply_current_filters)
        self.apply_filters_btn.setEnabled(True)
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
        self.select_from_map_btn.setEnabled(True)
        actions_inner.addWidget(self.select_from_map_btn)

        # Zoom button
        self.zoom_btn = QPushButton("Zoom to Selected")
        self.zoom_btn.clicked.connect(self._zoom_to_selected)
        self.zoom_btn.setEnabled(True)
        actions_inner.addWidget(self.zoom_btn)

        # Load imagery buttons
        imagery_layout = QHBoxLayout()

        self.load_visual_btn = QPushButton("Load Visual")
        self.load_visual_btn.setToolTip("Load visual (RGB) imagery as COG")
        self.load_visual_btn.clicked.connect(lambda: self._load_imagery("visual"))
        self.load_visual_btn.setEnabled(True)
        imagery_layout.addWidget(self.load_visual_btn)

        self.load_ms_btn = QPushButton("Load MS")
        self.load_ms_btn.setToolTip("Load multispectral imagery as COG")
        self.load_ms_btn.clicked.connect(lambda: self._load_imagery("ms_analytic"))
        self.load_ms_btn.setEnabled(True)
        imagery_layout.addWidget(self.load_ms_btn)

        self.load_pan_btn = QPushButton("Load Pan")
        self.load_pan_btn.setToolTip("Load panchromatic imagery as COG")
        self.load_pan_btn.clicked.connect(lambda: self._load_imagery("pan_analytic"))
        self.load_pan_btn.setEnabled(True)
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
        """Carica gli eventi disponibili da GitHub (CSV)."""
        self.refresh_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Caricamento eventi...")
        self.status_label.setStyleSheet("color: blue; font-size: 10px;")

        # Ottieni timeout dalle impostazioni (default 120 secondi)
        timeout = self.settings.value("MaxarOpenData/timeout", 120, type=int)
        
        # Migrazione: se timeout è ancora il vecchio default (30), usa il nuovo (120)
        if timeout == 30:
            timeout = 120
            get_logger().info(f"Migrated old timeout (30s) to new default (120s)")
        
        self.fetch_worker = DataFetchWorker(DATASETS_CSV_URL, data_type="text", timeout=timeout)
        self.fetch_worker.finished.connect(self._on_events_loaded)
        self.fetch_worker.error.connect(self._on_events_error)
        self.fetch_worker.start()

    def _on_events_loaded(self, csv_content):
        """Gestisce il caricamento eventi da CSV GitHub."""
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
        self.event_combo.addItem("-- Seleziona un evento --", None)
        for event_name, count in self.events:
            self.event_combo.addItem(f"{event_name} ({count} tiles)", event_name)

        self.status_label.setText(f"Caricati {len(self.events)} eventi")
        self.status_label.setStyleSheet("color: #00ffbf; font-size: 10px;")

    def _on_events_error(self, error_msg):
        """Handle events loading error."""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
        self.status_label.setStyleSheet("color: red; font-size: 10px;")

        QMessageBox.warning(
            self,
            "Errore caricamento eventi",
            f"Impossibile caricare gli eventi da GitHub:\n\n{error_msg}\n\n"
            "Verifica la connessione internet e riprova.",
        )

    def _on_event_changed(self, index):
        """Gestisce la selezione di un evento."""
        event_name = self.event_combo.currentData()
        self.load_footprints_btn.setEnabled(event_name is not None)
        self.apply_filters_btn.setEnabled(True)
        self.footprints_layer = None  # Reset layer quando cambi evento
        if event_name:
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
        """Carica i footprints per l'evento selezionato da GitHub GeoJSON."""
        event_name = self.event_combo.currentData()
        if not event_name:
            return

        self.load_footprints_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText(f"Caricamento footprints per {event_name}...")
        self.status_label.setStyleSheet("color: blue; font-size: 10px;")

        # Costruisci URL GeoJSON
        url = GEOJSON_URL_TEMPLATE.format(event=event_name)
        get_logger().info(f"Loading footprints from: {url}")
        
        # Ottieni timeout dalle impostazioni (default 180 secondi per i GeoJSON grandi)
        timeout = self.settings.value("MaxarOpenData/timeout", 180, type=int)
        
        # Migrazione: se timeout è ancora il vecchio default (30), usa il nuovo (180)
        if timeout == 30:
            timeout = 180
            get_logger().info(f"Migrated old timeout (30s) to new default for footprints (180s)")
        
        self.fetch_worker = DataFetchWorker(url, data_type="json", timeout=timeout)
        self.fetch_worker.finished.connect(self._on_footprints_loaded)
        self.fetch_worker.error.connect(self._on_footprints_error)
        self.fetch_worker.start()

    def _apply_current_filters(self):
        """Applica i filtri selezionati alla tabella dei footprints."""
        max_cloud = self.cloud_slider.value()
        use_date = self.date_check.isChecked()
        start_date = self.start_date_edit.date().toPyDate() if use_date else None
        end_date = self.end_date_edit.date().toPyDate() if use_date else None

        filtered = []
        for feat in self.all_features:
            props = feat.get("properties", {})
            cloud = props.get("cloud_cover", 0)
            date_str = props.get("datetime", "")
            try:
                from datetime import datetime
                date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date() if date_str else None
            except Exception:
                date = None

            if cloud is not None and cloud > max_cloud:
                continue
            if use_date and date:
                if (start_date and date < start_date) or (end_date and date > end_date):
                    continue
            filtered.append(feat)

        self._populate_footprints_table(filtered)
        self.status_label.setText(f"Filtrati {len(filtered)} footprints")
        self.status_label.setStyleSheet("color: #00ffbf; font-size: 10px;")

    def _on_footprint_selection_changed(self):
        """Gestisce la selezione delle righe nella tabella footprints."""
        if self._updating_selection:
            return
            
        selected = self.footprints_table.selectedItems()
        has_selection = bool(selected)
        self.zoom_btn.setEnabled(has_selection)
        self.load_visual_btn.setEnabled(has_selection)
        self.load_ms_btn.setEnabled(has_selection)
        self.load_pan_btn.setEnabled(has_selection)
        self.select_from_map_btn.setEnabled(self.footprints_layer is not None)
        self.status_label.setText(f"Selezionati {len(selected)//self.footprints_table.columnCount()} footprints")
        self.status_label.setStyleSheet("color: #00ffbf; font-size: 10px;")
        
        # Sincronizza selezione → layer
        if self.footprints_layer:
            selected_rows = set(idx.row() for idx in self.footprints_table.selectedIndexes())
            selected_fids = []
            for row in selected_rows:
                quadkey_item = self.footprints_table.item(row, 5)
                if quadkey_item:
                    quadkey = quadkey_item.text()
                    fid = self._quadkey_to_feature_id.get(quadkey)
                    if fid is not None:
                        selected_fids.append(fid)
            
            self._updating_selection = True
            self.footprints_layer.selectByIds(selected_fids)
            self._updating_selection = False

    def _on_layer_selection_changed(self):
        """Gestisce la selezione nel layer (mappa → tabella)."""
        if self._updating_selection or not self.footprints_layer:
            return
        
        self._updating_selection = True
        try:
            # Ottieni gli ID delle feature selezionate
            selected_fids = self.footprints_layer.selectedFeatureIds()
            
            # Converti in quadkeys
            selected_quadkeys = set()
            for fid in selected_fids:
                quadkey = self._feature_id_to_quadkey.get(fid)
                if quadkey:
                    selected_quadkeys.add(quadkey)
            
            # Seleziona le righe corrispondenti nella tabella
            self.footprints_table.clearSelection()
            for row in range(self.footprints_table.rowCount()):
                quadkey_item = self.footprints_table.item(row, 5)
                if quadkey_item and quadkey_item.text() in selected_quadkeys:
                    self.footprints_table.selectRow(row)
        finally:
            self._updating_selection = False

    def _populate_footprints_table(self, features):
        """Popola la tabella footprints con le feature fornite."""
        self.footprints_table.setRowCount(0)
        for feat in features:
            props = feat.get("properties", {})
            row = self.footprints_table.rowCount()
            self.footprints_table.insertRow(row)
            # Data
            self.footprints_table.setItem(row, 0, QTableWidgetItem(props.get("datetime", "")))
            # Platform
            self.footprints_table.setItem(row, 1, QTableWidgetItem(props.get("platform", "")))
            # GSD
            gsd = props.get("gsd", "")
            self.footprints_table.setItem(row, 2, NumericTableWidgetItem(str(gsd) if gsd is not None else ""))
            # Cloud cover
            cloud = props.get("cloud_cover", "")
            self.footprints_table.setItem(row, 3, NumericTableWidgetItem(str(cloud) if cloud is not None else ""))
            # Catalog ID
            self.footprints_table.setItem(row, 4, QTableWidgetItem(props.get("catalog_id", "")))
            # Quadkey
            self.footprints_table.setItem(row, 5, QTableWidgetItem(props.get("quadkey", "")))

    def _on_footprints_loaded(self, geojson_data):
        """Gestisce il caricamento dei footprints da GitHub GeoJSON."""
        self.progress_bar.setVisible(False)
        self.load_footprints_btn.setEnabled(True)
        self.apply_filters_btn.setEnabled(True)
        
        # Parse JSON string to dict
        try:
            geojson_dict = json.loads(geojson_data) if isinstance(geojson_data, str) else geojson_data
        except json.JSONDecodeError as e:
            get_logger().error(f"Failed to parse GeoJSON: {e}")
            self.status_label.setText("Errore: GeoJSON non valido")
            self.status_label.setStyleSheet("color: red; font-size: 10px;")
            return
        
        self.current_geojson = geojson_dict
        features = geojson_dict.get("features", [])
        
        self.all_features = features
        self._populate_footprints_table(features)
        self.status_label.setText(f"Caricati {len(features)} footprints")
        self.status_label.setStyleSheet("color: #00ffbf; font-size: 10px;")
        
        # Crea il layer footprints (se serve per selezione da mappa)
        if features:
            # Crea un layer temporaneo per la selezione da mappa
            from qgis.core import (
                QgsVectorLayer, QgsProject, QgsFeature, QgsGeometry, 
                QgsFields, QgsField, QgsPointXY
            )
            from qgis.PyQt.QtCore import QVariant

            # Crea un layer temporaneo per footprints
            layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "Footprints", "memory")
            pr = layer.dataProvider()

            # Definisci i campi
            fields = QgsFields()
            fields.append(QgsField("datetime", QVariant.String))
            fields.append(QgsField("platform", QVariant.String))
            fields.append(QgsField("gsd", QVariant.Double))
            fields.append(QgsField("cloud_cover", QVariant.Double))
            fields.append(QgsField("catalog_id", QVariant.String))
            fields.append(QgsField("quadkey", QVariant.String))
            pr.addAttributes(fields)
            layer.updateFields()

            self._feature_id_to_quadkey = {}
            self._quadkey_to_feature_id = {}

            for feat in features:
                props = feat.get("properties", {})
                geom = feat.get("geometry", {})
                qgs_geom = None
                
                if geom and geom.get("type") == "Polygon":
                    # Coordinates format: [[[lon, lat], [lon, lat], ...]]
                    coords = geom.get("coordinates", [])
                    if coords and len(coords) > 0:
                        # Outer ring
                        points = [QgsPointXY(pt[0], pt[1]) for pt in coords[0]]
                        qgs_geom = QgsGeometry.fromPolygonXY([points])
                        
                elif geom and geom.get("type") == "MultiPolygon":
                    # Coordinates format: [[[[lon, lat], [lon, lat], ...]], ...]
                    coords = geom.get("coordinates", [])
                    polygons = []
                    for polygon in coords:
                        if polygon and len(polygon) > 0:
                            # Outer ring of each polygon
                            points = [QgsPointXY(pt[0], pt[1]) for pt in polygon[0]]
                            polygons.append([points])
                    if polygons:
                        qgs_geom = QgsGeometry.fromMultiPolygonXY(polygons)

                if qgs_geom:
                    feature = QgsFeature(fields)  # Inizializza con i campi
                    feature.setGeometry(qgs_geom)
                    
                    # Imposta i valori dei campi usando gli indici
                    feature.setAttribute("datetime", props.get("datetime", ""))
                    feature.setAttribute("platform", props.get("platform", ""))
                    feature.setAttribute("gsd", props.get("gsd", 0.0))
                    feature.setAttribute("cloud_cover", props.get("cloud_cover", 0.0))
                    feature.setAttribute("catalog_id", props.get("catalog_id", ""))
                    feature.setAttribute("quadkey", props.get("quadkey", ""))
                    
                    pr.addFeature(feature)

                    # Mappa gli ID delle feature ai quadkey (per selezione da mappa)
                    fid = feature.id()
                    quadkey = props.get("quadkey")
                    if quadkey:
                        self._feature_id_to_quadkey[fid] = quadkey
                        self._quadkey_to_feature_id[quadkey] = fid

            # Update layer extent
            layer.updateExtents()
            
            # Apply styling to layer
            from qgis.core import QgsSimpleFillSymbolLayer, QgsFillSymbol
            from qgis.PyQt.QtGui import QColor
            
            symbol = QgsFillSymbol.createSimple({
                'color': '0,255,191,50',  # Semi-transparent cyan
                'outline_color': '0,255,191,255',  # Solid cyan border
                'outline_width': '0.5'
            })
            layer.renderer().setSymbol(symbol)
            
            # Rimuovi layer precedente se esiste
            existing_layers = QgsProject.instance().mapLayersByName("Footprints")
            for existing_layer in existing_layers:
                QgsProject.instance().removeMapLayer(existing_layer.id())
            
            # Invalida selection tool perché il vecchio layer è stato rimosso
            if self.selection_tool is not None:
                self.selection_tool = None
            
            # Aggiungi il nuovo layer al progetto
            QgsProject.instance().addMapLayer(layer)
            
            # Connetti selezione layer → tabella
            layer.selectionChanged.connect(self._on_layer_selection_changed)
            
            # Zoom to layer extent if auto_zoom enabled
            auto_zoom = self.settings.value("MaxarOpenData/auto_zoom", True, type=bool)
            if auto_zoom and layer.extent().isFinite():
                from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform
                
                # Ottieni extent del layer (in WGS84)
                layer_extent = layer.extent()
                
                # Trasforma da WGS84 al CRS del canvas
                source_crs = QgsCoordinateReferenceSystem("EPSG:4326")
                dest_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
                
                if source_crs.isValid() and dest_crs.isValid() and source_crs != dest_crs:
                    try:
                        transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
                        transformed_extent = transform.transformBoundingBox(layer_extent)
                        self.iface.mapCanvas().setExtent(transformed_extent)
                        get_logger().debug(f"Auto-zoom: transformed extent from {layer_extent.toString()} to {transformed_extent.toString()}")
                    except Exception as e:
                        get_logger().error(f"Failed to transform extent for auto-zoom: {e}")
                        # Fallback: usa extent non trasformato
                        self.iface.mapCanvas().setExtent(layer_extent)
                else:
                    self.iface.mapCanvas().setExtent(layer_extent)
                
                self.iface.mapCanvas().refresh()
            
            self.footprints_layer = layer
            get_logger().info(f"Footprints layer created with {len(features)} features")
            get_logger().debug(f"Layer extent: {layer.extent().toString()}")
        else:
            get_logger().warning("No features found in GeoJSON")

    def _on_footprints_error(self, error_msg):
        """Gestisce errori nel caricamento footprints."""
        self.progress_bar.setVisible(False)
        self.load_footprints_btn.setEnabled(True)
        self.apply_filters_btn.setEnabled(False)
        self.status_label.setText(f"Errore: {error_msg}")
        self.status_label.setStyleSheet("color: red; font-size: 10px;")
        QMessageBox.warning(
            self,
            "Errore caricamento footprints",
            f"Impossibile caricare i footprints:\n\n{error_msg}\n\n"
            "Verifica la connessione internet e riprova.",
        )

    def _on_selection_mode_toggled(self, checked):
        """Abilita/disabilita la selezione interattiva sulla mappa."""
        if checked:
            if self.footprints_layer is not None:
                # Ricrea sempre il tool per evitare problemi con layer rimossi/ricreati
                self.selection_tool = FootprintSelectionTool(self.iface.mapCanvas(), self.footprints_layer)
                self.selection_tool.selectionModeChanged.connect(self.select_from_map_btn.setChecked)
                
                self._previous_map_tool = self.iface.mapCanvas().mapTool()
                self.iface.mapCanvas().setMapTool(self.selection_tool)
                self.status_label.setText("Modalità selezione da mappa attiva")
        else:
            if self.selection_tool and self._previous_map_tool:
                self.iface.mapCanvas().setMapTool(self._previous_map_tool)
                self.status_label.setText("Modalità selezione da mappa disattivata")

    def _zoom_to_selected(self):
        """Zoom sulla selezione corrente nella tabella footprints.
        
        Supporta qualsiasi sistema di riferimento del map canvas tramite PROJ.
        Le coordinate GeoJSON (WGS84/EPSG:4326) vengono automaticamente trasformate
        nel CRS del canvas usando QgsCoordinateTransform che si basa su PROJ.
        
        Sistemi di riferimento supportati (esempi):
        - EPSG:4326 (WGS84) - Geographic
        - EPSG:3857 (Web Mercator) - Google Maps, OpenStreetMap
        - EPSG:2056 (CH1903+ / LV95) - Switzerland
        - EPSG:3395 (World Mercator)
        - EPSG:32632 (WGS84 / UTM zone 32N)
        - Qualsiasi altro CRS supportato da PROJ
        """
        selected_rows = set(idx.row() for idx in self.footprints_table.selectedIndexes())
        if not selected_rows:
            self.status_label.setText("Nessun footprint selezionato")
            return
            
        # Calcola bounding box dalle geometrie originali (in WGS84)
        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")
        
        for row in selected_rows:
            if row < len(self.all_features):
                feature = self.all_features[row]
                geom = feature.get("geometry", {})
                coords = geom.get("coordinates", [])
                
                if coords:
                    # Per Polygon o MultiPolygon
                    if geom.get("type") == "Polygon":
                        for point in coords[0]:  # Primo anello
                            min_x = min(min_x, point[0])
                            max_x = max(max_x, point[0])
                            min_y = min(min_y, point[1])
                            max_y = max(max_y, point[1])
                    elif geom.get("type") == "MultiPolygon":
                        for polygon in coords:
                            for point in polygon[0]:  # Primo anello di ogni poligono
                                min_x = min(min_x, point[0])
                                max_x = max(max_x, point[0])
                                min_y = min(min_y, point[1])
                                max_y = max(max_y, point[1])
        
        if min_x != float("inf"):
            from qgis.core import QgsRectangle, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
            
            # Crea extent in WGS84 (EPSG:4326)
            extent_wgs84 = QgsRectangle(min_x, min_y, max_x, max_y)
            
            # Ottieni CRS sorgente (GeoJSON è sempre WGS84) e destinazione (canvas)
            source_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            dest_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
            
            get_logger().debug(f"Zoom: WGS84 extent = {extent_wgs84.toString()}")
            get_logger().debug(f"Source CRS: {source_crs.authid()} - {source_crs.description()}")
            get_logger().debug(f"Dest CRS: {dest_crs.authid()} - {dest_crs.description()}")
            
            # Trasforma coordinate se necessario (usa PROJ internamente)
            if source_crs.isValid() and dest_crs.isValid() and source_crs != dest_crs:
                try:
                    # QgsCoordinateTransform usa PROJ per supportare qualsiasi CRS
                    transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
                    extent = transform.transformBoundingBox(extent_wgs84)
                    get_logger().debug(f"Transformed extent = {extent.toString()}")
                except Exception as e:
                    get_logger().error(f"Failed to transform coordinates: {e}")
                    # Fallback: usa extent WGS84 non trasformato
                    extent = extent_wgs84
                    self.status_label.setText(f"Avviso: impossibile trasformare coordinate da {source_crs.authid()} a {dest_crs.authid()}")
                    self.status_label.setStyleSheet("color: orange; font-size: 10px;")
            else:
                extent = extent_wgs84
                if not source_crs.isValid():
                    get_logger().warning("Source CRS (EPSG:4326) is not valid")
                if not dest_crs.isValid():
                    get_logger().warning(f"Destination CRS is not valid: {dest_crs.authid()}")
            
            # Applica zoom
            self.iface.mapCanvas().setExtent(extent)
            self.iface.mapCanvas().refresh()
            self.status_label.setText("Zoom effettuato sulla selezione")
            self.status_label.setStyleSheet("color: #00ffbf; font-size: 10px;")
        else:
            self.status_label.setText("Impossibile calcolare l'estensione della selezione")
            self.status_label.setStyleSheet("color: orange; font-size: 10px;")

    def _load_imagery(self, imagery_type):
        """Carica l'immagine selezionata (visual, ms_analytic, pan_analytic) come COG."""
        selected_rows = set(idx.row() for idx in self.footprints_table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Nessuna selezione", "Seleziona almeno un footprint dalla tabella.")
            return
            
        imagery_label = imagery_type.replace("_", " ").title()
        
        loaded_count = 0
        not_available_count = 0
        
        for row in selected_rows:
            if row >= len(self.all_features):
                continue
                
            feature = self.all_features[row]
            props = feature.get("properties", {})
            
            # Il GeoJSON ha campi "visual", "ms_analytic", "pan_analytic" (senza _cog_url)
            cog_url = props.get(imagery_type)
            
            if not cog_url:
                not_available_count += 1
                get_logger().debug(f"No {imagery_type} URL for quadkey {props.get('quadkey')}")
                continue
                
            # Costruisci nome layer
            catalog_id = props.get("catalog_id", "unknown")
            quadkey = props.get("quadkey", "")
            date = props.get("datetime", "")[:10] if props.get("datetime") else "no-date"
            layer_name = f"Maxar {imagery_type} - {catalog_id} - {quadkey} ({date})"
            
            # Carica COG con GDAL vsicurl
            cog_path = f"/vsicurl/{cog_url}"
            raster_layer = QgsRasterLayer(cog_path, layer_name, "gdal")
            
            if raster_layer.isValid():
                QgsProject.instance().addMapLayer(raster_layer)
                loaded_count += 1
                get_logger().info(f"Loaded COG: {layer_name}")
            else:
                get_logger().error(f"Failed to load COG: {cog_url}")
                QMessageBox.warning(self, "Errore caricamento", f"Impossibile caricare il COG:\n{cog_url}")
        
        if loaded_count > 0:
            self.status_label.setText(f"Caricate {loaded_count} immagini {imagery_label}")
            self.status_label.setStyleSheet("color: #00ffbf; font-size: 10px;")
        elif not_available_count > 0:
            QMessageBox.warning(
                self, 
                "Immagini non disponibili", 
                f"{imagery_label} non disponibile per i footprints selezionati.\n"
                f"Questo evento potrebbe avere solo immagini Visual."
            )
            self.status_label.setText(f"{imagery_label} non disponibile")
            self.status_label.setStyleSheet("color: orange; font-size: 10px;")

    def _clear_layers(self):
        """Rimuove tutti i layer caricati dal plugin."""
        project = QgsProject.instance()
        layers_to_remove = []
        for lyr in project.mapLayers().values():
            if lyr.name().startswith("Event_") or lyr.name().startswith("Vantor") or "COG" in lyr.name() or lyr.name() == "Footprints":
                layers_to_remove.append(lyr.id())
        for lid in layers_to_remove:
            project.removeMapLayer(lid)
        self.status_label.setText("Tutti i layer caricati sono stati rimossi.")