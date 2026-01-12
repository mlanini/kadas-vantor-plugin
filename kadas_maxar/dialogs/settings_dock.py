try:
    from qgis.PyQt.QtWidgets import (
        QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
        QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox, QComboBox,
        QTabWidget, QGroupBox, QFileDialog, QMessageBox
    )
    from qgis.PyQt.QtCore import QSettings, Qt
    from qgis.PyQt.QtGui import QFont
except Exception:
    # Minimal fallbacks for environments without PyQt available (tests)
    class QDockWidget(object):
        def __init__(self, *a, **k):
            self._widget = None
            self._objectName = None
            self._visible = False
            self.visibilityChanged = type("S", (), {"connect": lambda self, cb: None})()
        def setObjectName(self, name):
            self._objectName = name
        def setWidget(self, w):
            self._widget = w
        def show(self):
            self._visible = True
        def hide(self):
            self._visible = False
        def isVisible(self):
            return self._visible
        def raise_(self):
            pass
    class QWidget(object):
        def __init__(self, *a, **k):
            self._layout = None
        def setLayout(self, layout):
            self._layout = layout
    class QVBoxLayout(object):
        def __init__(self, *a, **k):
            self._items = []
        def addWidget(self, w):
            self._items.append(w)
        def addLayout(self, layout):
            self._items.append(layout)
        def count(self):
            return len(self._items)
    class QLabel(object):
        def __init__(self, text):
            self.text = text


class SettingsDockWidget(QDockWidget):
    """Dock widget for plugin settings adapted for KADAS/QGIS."""
    
    SETTINGS_PREFIX = "MaxarOpenData/"

    def __init__(self, iface, parent=None):
        try:
            super().__init__("Settings", parent)
        except Exception:
            try:
                super().__init__()
            except Exception:
                pass

        try:
            self.setObjectName("MaxarOpenDataSettingsDock")
        except Exception:
            self._objectName = "MaxarOpenDataSettingsDock"

        try:
            self.iface = iface
            self.settings = QSettings()
            
            widget = QWidget()
            self.setWidget(widget)
            
            layout = QVBoxLayout(widget)
            layout.setSpacing(10)
            
            # Header
            header_label = QLabel("Plugin Settings")
            try:
                header_font = QFont()
                header_font.setPointSize(12)
                header_font.setBold(True)
                header_label.setFont(header_font)
                header_label.setAlignment(Qt.AlignCenter)
                header_label.setStyleSheet("color: #ffffff;")
            except Exception:
                pass
            layout.addWidget(header_label)
            
            # Tab widget for organized settings
            tab_widget = QTabWidget()
            layout.addWidget(tab_widget)
            
            # Data settings tab
            data_tab = self._create_data_tab()
            tab_widget.addTab(data_tab, "Data")
            
            # Display settings tab
            display_tab = self._create_display_tab()
            tab_widget.addTab(display_tab, "Display")
            
            # Advanced settings tab
            advanced_tab = self._create_advanced_tab()
            tab_widget.addTab(advanced_tab, "Advanced")
            
            # Buttons
            button_layout = QHBoxLayout()
            
            self.save_btn = QPushButton("Save Settings")
            try:
                self.save_btn.clicked.connect(self._save_settings)
            except Exception:
                pass
            button_layout.addWidget(self.save_btn)
            
            self.reset_btn = QPushButton("Reset Defaults")
            try:
                self.reset_btn.clicked.connect(self._reset_defaults)
            except Exception:
                pass
            button_layout.addWidget(self.reset_btn)
            
            layout.addLayout(button_layout)
            
            # Stretch at the end
            layout.addStretch()
            
            # Status label
            self.status_label = QLabel("Settings loaded")
            try:
                self.status_label.setStyleSheet("color: gray; font-size: 10px;")
            except Exception:
                pass
            layout.addWidget(self.status_label)
            
            # Load current settings
            self._load_settings()
        except Exception as e:
            # If settings UI fails to build, show placeholder, log traceback and notify
            err_msg = f"Failed to build Settings UI: {str(e)}"
            try:
                try:
                    from kadas_maxar.logger import get_logger
                    logger = get_logger()
                    # log at WARNING level but preserve traceback for diagnostics
                    logger.warning(err_msg, exc_info=True)
                except Exception:
                    pass
                import qgis.PyQt.QtWidgets as _qtw
                try:
                    _qtw.QMessageBox.critical(self.iface.mainWindow(), "Error", err_msg)
                except Exception:
                    pass
            except Exception:
                pass
            try:
                widget = QWidget()
                lbl = None
                try:
                    v = QVBoxLayout()
                    try:
                        widget.setLayout(v)
                    except Exception:
                        pass
                    lbl = QLabel(f"Error loading Settings UI: {str(e)}")
                    try:
                        try:
                            self._style_label(lbl)
                        except Exception:
                            pass
                        v.addWidget(lbl)
                    except Exception:
                        setattr(widget, '_error_label', lbl)
                except Exception:
                    try:
                        lbl = QLabel(f"Error loading Settings UI: {str(e)}")
                        try:
                            self._style_label(lbl)
                        except Exception:
                            pass
                        setattr(widget, '_error_label', lbl)
                    except Exception:
                        setattr(widget, '_error_text', str(e))
                try:
                    self.setWidget(widget)
                except Exception:
                    self._widget = widget
                self._ui_error = str(e)
            except Exception:
                if not hasattr(self, 'visibilityChanged'):
                    self.visibilityChanged = type("S", (), {"connect": lambda self, cb: None})()

    def _create_data_tab(self):
        """Create the data settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Data source group
        source_group = QGroupBox("Data Source")
        source_layout = QFormLayout(source_group)
        
        # Use local data checkbox
        self.use_local_check = QCheckBox()
        try:
            self.use_local_check.setChecked(False)
            self.use_local_check.stateChanged.connect(self._on_local_data_changed)
        except Exception:
            pass
        source_layout.addRow("Use local data copy:", self.use_local_check)
        
        # Local data path
        path_layout = QHBoxLayout()
        self.local_path_input = QLineEdit()
        try:
            self.local_path_input.setEnabled(False)
        except Exception:
            pass
        path_layout.addWidget(self.local_path_input)
        
        self.browse_btn = QPushButton("Browse...")
        try:
            self.browse_btn.setEnabled(False)
            self.browse_btn.clicked.connect(self._browse_local_path)
        except Exception:
            pass
        path_layout.addWidget(self.browse_btn)
        
        source_layout.addRow("Local path:", path_layout)
        
        layout.addWidget(source_group)
        
        # STAC settings group
        stac_group = QGroupBox("STAC Catalog")
        stac_layout = QFormLayout(stac_group)
        
        self.catalog_input = QLineEdit()
        stac_layout.addRow("STAC Catalog URL:", self.catalog_input)
        
        layout.addWidget(stac_group)
        
        layout.addStretch()
        return widget
    
    def _create_display_tab(self):
        """Create the display settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Layer settings group
        layer_group = QGroupBox("Layer Settings")
        layer_layout = QFormLayout(layer_group)
        
        # Auto-zoom to footprints
        self.auto_zoom_check = QCheckBox()
        try:
            self.auto_zoom_check.setChecked(True)
        except Exception:
            pass
        layer_layout.addRow("Auto-zoom to footprints:", self.auto_zoom_check)
        
        # Add layers to group
        self.group_layers_check = QCheckBox()
        try:
            self.group_layers_check.setChecked(True)
        except Exception:
            pass
        layer_layout.addRow("Group layers by event:", self.group_layers_check)
        
        # Default imagery type
        self.default_imagery_combo = QComboBox()
        try:
            self.default_imagery_combo.addItems(
                ["Visual (RGB)", "Multispectral", "Panchromatic"]
            )
        except Exception:
            pass
        layer_layout.addRow("Default imagery type:", self.default_imagery_combo)
        
        layout.addWidget(layer_group)
        
        # Footprint styling group
        style_group = QGroupBox("Footprint Styling")
        style_layout = QFormLayout(style_group)
        
        # Footprint opacity
        self.opacity_spin = QSpinBox()
        try:
            self.opacity_spin.setRange(0, 100)
            self.opacity_spin.setValue(50)
            self.opacity_spin.setSuffix(" %")
        except Exception:
            pass
        style_layout.addRow("Fill opacity:", self.opacity_spin)
        
        # Show labels
        self.show_labels_check = QCheckBox()
        try:
            self.show_labels_check.setChecked(False)
        except Exception:
            pass
        style_layout.addRow("Show footprint labels:", self.show_labels_check)
        
        layout.addWidget(style_group)
        
        layout.addStretch()
        return widget
    
    def _create_advanced_tab(self):
        """Create the advanced settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Network settings group
        network_group = QGroupBox("Network")
        network_layout = QFormLayout(network_group)
        
        # Timeout
        self.timeout_spin = QSpinBox()
        try:
            self.timeout_spin.setRange(5, 300)
            self.timeout_spin.setValue(30)
            self.timeout_spin.setSuffix(" seconds")
        except Exception:
            pass
        network_layout.addRow("Request timeout:", self.timeout_spin)
        
        # Max concurrent downloads
        self.max_downloads_spin = QSpinBox()
        try:
            self.max_downloads_spin.setRange(1, 10)
            self.max_downloads_spin.setValue(3)
        except Exception:
            pass
        network_layout.addRow("Max concurrent downloads:", self.max_downloads_spin)
        
        layout.addWidget(network_group)
        
        # Debug settings group
        debug_group = QGroupBox("Debug")
        debug_layout = QFormLayout(debug_group)
        
        # Enable debug mode
        self.debug_check = QCheckBox()
        try:
            self.debug_check.setChecked(False)
        except Exception:
            pass
        debug_layout.addRow("Enable debug mode:", self.debug_check)
        
        # Show URLs in messages
        self.show_urls_check = QCheckBox()
        try:
            self.show_urls_check.setChecked(False)
        except Exception:
            pass
        debug_layout.addRow("Show URLs in messages:", self.show_urls_check)
        
        layout.addWidget(debug_group)
        
        layout.addStretch()
        return widget
    
    def _on_local_data_changed(self, state):
        """Handle local data checkbox change."""
        try:
            enabled = (state == Qt.Checked) if hasattr(Qt, 'Checked') else bool(state)
            self.local_path_input.setEnabled(enabled)
            self.browse_btn.setEnabled(enabled)
        except Exception:
            pass
    
    def _browse_local_path(self):
        """Open directory browser for local data path."""
        try:
            directory = QFileDialog.getExistingDirectory(
                self,
                "Select Local Data Directory",
                self.local_path_input.text() or ""
            )
            if directory:
                self.local_path_input.setText(directory)
        except Exception:
            pass
    
    def _load_settings(self):
        """Load settings from QSettings."""
        try:
            # Data
            self.use_local_check.setChecked(
                self.settings.value(f"{self.SETTINGS_PREFIX}use_local", False, type=bool)
            )
            self.local_path_input.setText(
                self.settings.value(f"{self.SETTINGS_PREFIX}local_path", "")
            )
            self.catalog_input.setText(
                self.settings.value(
                    f"{self.SETTINGS_PREFIX}stac_catalog_url",
                    "https://maxar-opendata.s3.amazonaws.com/events/catalog.json"
                )
            )
            
            # Display
            self.auto_zoom_check.setChecked(
                self.settings.value(f"{self.SETTINGS_PREFIX}auto_zoom", True, type=bool)
            )
            self.group_layers_check.setChecked(
                self.settings.value(f"{self.SETTINGS_PREFIX}group_layers", True, type=bool)
            )
            self.default_imagery_combo.setCurrentIndex(
                self.settings.value(f"{self.SETTINGS_PREFIX}default_imagery", 0, type=int)
            )
            self.opacity_spin.setValue(
                self.settings.value(f"{self.SETTINGS_PREFIX}opacity", 50, type=int)
            )
            self.show_labels_check.setChecked(
                self.settings.value(f"{self.SETTINGS_PREFIX}show_labels", False, type=bool)
            )
            
            # Advanced
            self.timeout_spin.setValue(
                self.settings.value(f"{self.SETTINGS_PREFIX}timeout", 30, type=int)
            )
            self.max_downloads_spin.setValue(
                self.settings.value(f"{self.SETTINGS_PREFIX}max_downloads", 3, type=int)
            )
            self.debug_check.setChecked(
                self.settings.value(f"{self.SETTINGS_PREFIX}debug", False, type=bool)
            )
            self.show_urls_check.setChecked(
                self.settings.value(f"{self.SETTINGS_PREFIX}show_urls", False, type=bool)
            )
            
            # Update enabled states
            try:
                state = Qt.Checked if self.use_local_check.isChecked() else Qt.Unchecked
                self._on_local_data_changed(state)
            except Exception:
                pass
            
            self.status_label.setText("Settings loaded")
            try:
                self.status_label.setStyleSheet("color: gray; font-size: 10px;")
            except Exception:
                pass
        except Exception as e:
            try:
                self.status_label.setText(f"Error loading settings: {e}")
                self.status_label.setStyleSheet("color: red; font-size: 10px;")
            except Exception:
                pass
    
    def _reset_defaults(self):
        """Reset all settings to defaults."""
        try:
            # Data
            self.use_local_check.setChecked(False)
            self.local_path_input.setText("")
            self.catalog_input.setText(
                "https://maxar-opendata.s3.amazonaws.com/events/catalog.json"
            )
            
            # Display
            self.auto_zoom_check.setChecked(True)
            self.group_layers_check.setChecked(True)
            self.default_imagery_combo.setCurrentIndex(0)
            self.opacity_spin.setValue(50)
            self.show_labels_check.setChecked(False)
            
            # Advanced
            self.timeout_spin.setValue(30)
            self.max_downloads_spin.setValue(3)
            self.debug_check.setChecked(False)
            self.show_urls_check.setChecked(False)
            
            self.status_label.setText("Settings reset to defaults")
            try:
                self.status_label.setStyleSheet("color: blue; font-size: 10px;")
            except Exception:
                pass
        except Exception as e:
            try:
                self.status_label.setText(f"Error resetting: {e}")
                self.status_label.setStyleSheet("color: red; font-size: 10px;")
            except Exception:
                pass

    def _style_label(self, label):
        """Apply a white text color style to a QLabel when possible."""
        try:
            label.setStyleSheet("color: white;")
        except Exception:
            try:
                setattr(label, '_style', 'color: white;')
            except Exception:
                pass

    def _save_settings(self):
        """Save settings to QSettings."""
        try:
            # Data
            self.settings.setValue(
                f"{self.SETTINGS_PREFIX}use_local",
                self.use_local_check.isChecked()
            )
            self.settings.setValue(
                f"{self.SETTINGS_PREFIX}local_path",
                self.local_path_input.text()
            )
            self.settings.setValue(
                f"{self.SETTINGS_PREFIX}stac_catalog_url",
                self.catalog_input.text()
            )
            
            # Display
            self.settings.setValue(
                f"{self.SETTINGS_PREFIX}auto_zoom",
                self.auto_zoom_check.isChecked()
            )
            self.settings.setValue(
                f"{self.SETTINGS_PREFIX}group_layers",
                self.group_layers_check.isChecked()
            )
            self.settings.setValue(
                f"{self.SETTINGS_PREFIX}default_imagery",
                self.default_imagery_combo.currentIndex()
            )
            self.settings.setValue(
                f"{self.SETTINGS_PREFIX}opacity",
                self.opacity_spin.value()
            )
            self.settings.setValue(
                f"{self.SETTINGS_PREFIX}show_labels",
                self.show_labels_check.isChecked()
            )
            
            # Advanced
            self.settings.setValue(
                f"{self.SETTINGS_PREFIX}timeout",
                self.timeout_spin.value()
            )
            self.settings.setValue(
                f"{self.SETTINGS_PREFIX}max_downloads",
                self.max_downloads_spin.value()
            )
            self.settings.setValue(
                f"{self.SETTINGS_PREFIX}debug",
                self.debug_check.isChecked()
            )
            self.settings.setValue(
                f"{self.SETTINGS_PREFIX}show_urls",
                self.show_urls_check.isChecked()
            )
            
            # Sync settings
            self.settings.sync()
            
            self.status_label.setText("Settings saved successfully")
            try:
                self.status_label.setStyleSheet("color: green; font-size: 10px;")
            except Exception:
                pass
            
            try:
                QMessageBox.information(
                    self,
                    "Settings Saved",
                    "Settings have been saved successfully."
                )
            except Exception:
                pass
        except Exception as e:
            try:
                self.status_label.setText(f"Error saving: {e}")
                self.status_label.setStyleSheet("color: red; font-size: 10px;")
            except Exception:
                pass

    def show(self):
        try:
            super().show()
        except Exception:
            self._visible = True

    def hide(self):
        try:
            super().hide()
        except Exception:
            self._visible = False

    def isVisible(self):
        try:
            return super().isVisible()
        except Exception:
            return getattr(self, '_visible', False)

    def raise_(self):
        try:
            super().raise_()
        except Exception:
            pass
