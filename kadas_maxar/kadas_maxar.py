# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import Qt, QObject
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu, QMessageBox
from qgis.PyQt.QtNetwork import QNetworkProxy
from qgis.core import QgsSettings
import os
import os as _os_env  # riuso per chiarezza

from kadas.kadasgui import *


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
        """Applica le impostazioni proxy definite in KADAS/QGIS a Qt e alle lib HTTP."""
        settings = QgsSettings()
        enabled = settings.value("proxy/enabled", False, type=bool)
        if not enabled:
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

        # Propaga anche a librerie esterne (es. requests)
        if host and port:
            cred = f"{user}:{password}@" if user else ""
            proxy_url = f"http://{cred}{host}:{port}"
            for var in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"):
                _os_env.environ[var] = proxy_url
            if excludes:
                _os_env.environ["NO_PROXY"] = excludes

    def initGui(self):
        self._apply_proxy_settings()
        # create menu
        self.menu = QMenu(self.tr("Vantor EO Data"))

        # icons
        icon_base = os.path.join(self.plugin_dir, "icons")
        main_icon = os.path.join(icon_base, "icon.svg")
        settings_icon = os.path.join(icon_base, "settings.svg")
        about_icon = os.path.join(icon_base, "about.svg")

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
