# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import Qt, QObject
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu, QMessageBox
from qgis.PyQt.QtNetwork import QNetworkProxy, QNetworkProxyFactory
from qgis.core import QgsSettings
import os
import os as _os_env  # riuso per chiarezza
import socket

from kadas.kadasgui import *
from .logger import get_logger
import subprocess
import sys

DEFAULT_STAC_CATALOG_URL = "https://maxar-opendata.s3.dualstack.us-west-2.amazonaws.com/events/catalog.json"


class KadasMaxar(QObject):
    """KADAS-compatible wrapper for Maxar Open Data functionality."""

    def __init__(self, iface):
        QObject.__init__(self)
        self.iface = KadasPluginInterface.cast(iface)
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = None
        self._maxar_dock = None
        self._settings_dock = None
        # Imposta livello di log desiderato: "STANDARD", "DEBUG", "ERRORS"
        self.log = get_logger(level="STANDARD")
        self.log.info("Logger inizializzato (livello: STANDARD)")

    def add_action(self, icon_path, text, callback, add_to_menu=True, status_tip=None, checkable=False, parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setCheckable(checkable)
        if status_tip is not None:
            action.setStatusTip(status_tip)
        if add_to_menu and self.menu is not None:
            self.menu.addAction(action)
        self.actions.append(action)
        return action

    def _apply_proxy_settings(self):
        """Applica le impostazioni proxy definite in KADAS/QGIS a Qt e alle librerie HTTP."""
        settings = QgsSettings()
        enabled = settings.value("proxy/enabled", False, type=bool)
        proxy_vars = (
            "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy",
            "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy"
        )

        if not enabled:
            QNetworkProxyFactory.setUseSystemConfiguration(True)
            QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.NoProxy))
            self.log.info("Proxy disabilitato: uso configurazione di sistema")
            # Rimuovi tutte le variabili d'ambiente proxy
            for var in proxy_vars:
                if var in _os_env.environ:
                    del _os_env.environ[var]
                    self.log.debug(f"Variabile d'ambiente rimossa: {var}")
            return

        proxy_type = settings.value("proxy/type", "HttpProxy")
        host = settings.value("proxy/host", "", type=str)
        port = settings.value("proxy/port", 0, type=int)
        user = settings.value("proxy/user", "", type=str)
        password = settings.value("proxy/password", "", type=str)
        excludes = settings.value("proxy/excludes", "", type=str)

        qt_type_map = {
            "HttpProxy": QNetworkProxy.HttpProxy,
            "HttpCachingProxy": QNetworkProxy.HttpCachingProxy,
            "Socks5Proxy": QNetworkProxy.Socks5Proxy,
            "FtpCachingProxy": QNetworkProxy.FtpCachingProxy,
        }
        qproxy = QNetworkProxy(qt_type_map.get(proxy_type, QNetworkProxy.HttpProxy), host, port, user, password)
        QNetworkProxy.setApplicationProxy(qproxy)
        QNetworkProxyFactory.setUseSystemConfiguration(False)
        self.log.info(f"Proxy applicato: {proxy_type}://{host}:{port} (user: {user})")

        # Propaga anche a librerie esterne (requests/urllib, ecc.)
        if host and port:
            scheme = "socks5h" if proxy_type.startswith("Socks5") else "http"
            cred = f"{user}:{password}@" if user else ""
            proxy_url = f"{scheme}://{cred}{host}:{port}"
            for var in proxy_vars:
                if var.lower().startswith("no_proxy"):
                    continue
                _os_env.environ[var] = proxy_url
                self.log.debug(f"Variabile d'ambiente impostata: {var}={proxy_url}")
            if excludes:
                _os_env.environ["NO_PROXY"] = excludes
                _os_env.environ["no_proxy"] = excludes
                self.log.debug(f"NO_PROXY impostato: {excludes}")
        else:
            # Rimuovi variabili d'ambiente se host/port non validi
            for var in proxy_vars:
                if var in _os_env.environ:
                    del _os_env.environ[var]
                    self.log.debug(f"Variabile d'ambiente rimossa: {var}")

        # VPN detection (come in kadas-albireo2 e swisstopo)
        try:
            gw = socket.gethostbyname(socket.gethostname())
            if gw.startswith("10.") or gw.startswith("172.") or gw.startswith("192.168."):
                self.log.info("Connessione probabilmente NON tramite VPN (rete privata rilevata)")
            else:
                self.log.info("Connessione probabilmente tramite VPN o pubblica")
        except Exception as e:
            self.log.warning(f"Impossibile determinare lo stato VPN: {e}")

    def open_log_window(self):
        """Apre il file di log con l'editor di testo di sistema."""
        log_path = os.environ.get('KADAS_MAXAR_LOG', os.path.expanduser('~/.kadas/maxar.log'))
        try:
            if sys.platform.startswith('win'):
                os.startfile(log_path)
            elif sys.platform.startswith('darwin'):
                subprocess.Popen(['open', log_path])
            else:
                subprocess.Popen(['xdg-open', log_path])
        except Exception as e:
            QMessageBox.warning(self.iface.mainWindow(), "Errore apertura log", f"Impossibile aprire il file di log:\n{e}")

    def initGui(self):
        self._apply_proxy_settings()
        # create menu
        self.menu = QMenu(self.tr("Vantor EO Data"))

        # icons
        icon_base = os.path.join(self.plugin_dir, "icons")
        main_icon = os.path.join(icon_base, "icon.svg")
        settings_icon = os.path.join(icon_base, "settings.svg")
        about_icon = os.path.join(icon_base, "about.svg")
        log_icon = os.path.join(icon_base, "log.svg") if os.path.exists(os.path.join(icon_base, "log.svg")) else None

        # Add panel actions
        self.maxar_action = self.add_action(
            main_icon,
            self.tr("Vantor EO Data Panel"),
            self.toggle_maxar_dock,
            status_tip=self.tr("Toggle Vantor EO Data Panel"),
            checkable=True,
            parent=self.iface.mainWindow(),
        )

        self.settings_action = self.add_action(
            settings_icon,
            self.tr("Settings"),
            self.toggle_settings_dock,
            status_tip=self.tr("Toggle Settings Panel"),
            checkable=True,
            parent=self.iface.mainWindow(),
        )

        # Log window opener
        self.add_action(
            log_icon,
            self.tr("Apri file di log"),
            self.open_log_window,
            add_to_menu=True,
            status_tip=self.tr("Visualizza il file di log del plugin"),
            parent=self.iface.mainWindow(),
        )

        # Update and About
        update_icon = None
        self.add_action(
            update_icon,
            self.tr("Check for Updates..."),
            self.show_update_checker,
            add_to_menu=True,
            status_tip=self.tr("Check for plugin updates from GitHub"),
            parent=self.iface.mainWindow(),
        )

        self.add_action(
            about_icon,
            self.tr("About Vantor EO Data Plugin"),
            self.show_about,
            add_to_menu=True,
            status_tip=self.tr("About Vantor EO Data Plugin"),
            parent=self.iface.mainWindow(),
        )

        # Register menu with KADAS interface - create custom "EO" tab
        self.iface.addActionMenu(self.tr("Vantor EO Data"), QIcon(main_icon), self.menu, self.iface.PLUGIN_MENU, self.iface.CUSTOM_TAB, "EO")

    def unload(self):
        """Clean up and unload the plugin."""
        # Close dock widgets
        if self._maxar_dock is not None:
            self._maxar_dock.close()
            self._maxar_dock = None
        
        if self._settings_dock is not None:
            self._settings_dock.close()
            self._settings_dock = None
        
        # Remove menu
        if self.menu:
            self.iface.removeActionMenu(self.menu, self.iface.PLUGIN_MENU, self.iface.CUSTOM_TAB, "EO")
            self.menu = None
        
        # Clear actions
        for action in self.actions:
            if action:
                action.triggered.disconnect()
        self.actions.clear()

    def toggle_maxar_dock(self):
        if self._maxar_dock is None:
            try:
                try:
                    from .dialogs.maxar_dock import MaxarDockWidget
                except Exception:
                    from kadas_maxar.dialogs.maxar_dock import MaxarDockWidget

                self._maxar_dock = MaxarDockWidget(self.iface, self.iface.mainWindow())
                self._maxar_dock.setObjectName("MaxarOpenDataDock")
                self._maxar_dock.visibilityChanged.connect(self._on_maxar_visibility_changed)
                # Add as dock widget to main window
                self.iface.mainWindow().addDockWidget(Qt.RightDockWidgetArea, self._maxar_dock)
                self._maxar_dock.show()
                self._maxar_dock.raise_()
                return

            except Exception as e:
                QMessageBox.critical(self.iface.mainWindow(), "Error", f"Failed to create Maxar Open Data panel:\n{str(e)}")
                self.maxar_action.setChecked(False)
                return

        if self._maxar_dock.isVisible():
            self._maxar_dock.hide()
        else:
            self._maxar_dock.show()
            self._maxar_dock.raise_()

    def _on_maxar_visibility_changed(self, visible):
        self.maxar_action.setChecked(visible)

    def toggle_settings_dock(self):
        if self._settings_dock is None:
            try:
                try:
                    from .dialogs.settings_dock import SettingsDockWidget
                except Exception:
                    from kadas_maxar.dialogs.settings_dock import SettingsDockWidget

                self._settings_dock = SettingsDockWidget(self.iface, self.iface.mainWindow())
                self._settings_dock.setObjectName("MaxarOpenDataSettingsDock")
                self._settings_dock.visibilityChanged.connect(self._on_settings_visibility_changed)
                self.iface.mainWindow().addDockWidget(Qt.RightDockWidgetArea, self._settings_dock)
                self._settings_dock.show()
                self._settings_dock.raise_()
                return

            except Exception as e:
                QMessageBox.critical(self.iface.mainWindow(), "Error", f"Failed to create Settings panel:\n{str(e)}")
                self.settings_action.setChecked(False)
                return

        if self._settings_dock.isVisible():
            self._settings_dock.hide()
        else:
            self._settings_dock.show()
            self._settings_dock.raise_()

    def _on_settings_visibility_changed(self, visible):
        self.settings_action.setChecked(visible)

    def show_about(self):
        about_text = """<h3>Vantor EO Data Plugin for KADAS</h3>
<p><b>Version 0.1.0</b></p>
<p>First developed by <a href="https://www.linkedin.com/in/giswqs">Qiusheng Wu</a> as a <a href="https://plugins.qgis.org/plugins/maxar_open_data/">QGIS 3.x Plugin</a>.</p>
<p>This plugin is privately maintained and adapted by <a href="https://www.linkedin.com/in/mlanini">Michael Lanini</a>.<br>
Plugin repository: <a href="https://github.com/mlanini/kadas-vantor-plugin">github.com/mlanini/kadas-vantor-plugin</a><br>
Contributions are welcome! Please feel free to submit Issues and Pull Requests.</p>
<p>Imagery credits &copy; <a href="https://vantor.com/company/open-data-program/">Vantor Open Data Program</a></p>
"""
        QMessageBox.about(self.iface.mainWindow(), "About Vantor Open Data Plugin for KADAS", about_text)

    def show_update_checker(self):
        QMessageBox.information(self.iface.mainWindow(), "Update", "Update checker not implemented yet")

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
