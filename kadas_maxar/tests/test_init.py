import pytest
import sys
import types

# Provide a minimal fake 'qgis.PyQt' module for test environment if not available
if 'qgis' not in sys.modules:
    qgis_mod = types.ModuleType('qgis')
    pyqt_mod = types.ModuleType('qgis.PyQt')
    # minimal QtCore, QtGui, QtWidgets
    QtCore = types.ModuleType('qgis.PyQt.QtCore')
    QtCore.Qt = types.SimpleNamespace(RightDockWidgetArea=1)
    class QObject:
        def __init__(self, *a, **k):
            pass
        def tr(self, s):
            return s
    QtCore.QObject = QObject
    QtGui = types.ModuleType('qgis.PyQt.QtGui')
    def _QIcon(*a, **k):
        return None
    QtGui.QIcon = _QIcon

    # simple widget classes
    class _QAction:
        def __init__(self, *a, **k):
            self.triggered = types.SimpleNamespace(connect=lambda cb: None)
            self._checkable = False
            self._checked = False
        def setCheckable(self, v):
            self._checkable = v
        def setStatusTip(self, v):
            pass
        def setChecked(self, v):
            self._checked = v
    class _QMenu:
        def __init__(self, *a, **k):
            pass
        def addAction(self, *a, **k):
            pass
    class _QMessageBox:
        @staticmethod
        def critical(*a, **k):
            pass
        @staticmethod
        def about(*a, **k):
            pass
        @staticmethod
        def information(*a, **k):
            pass

    QtWidgets = types.ModuleType('qgis.PyQt.QtWidgets')
    QtWidgets.QAction = _QAction
    QtWidgets.QMenu = _QMenu
    QtWidgets.QMessageBox = _QMessageBox

    pyqt_mod.QtCore = QtCore
    pyqt_mod.QtGui = QtGui
    pyqt_mod.QtWidgets = QtWidgets
    qgis_mod.PyQt = pyqt_mod

    # register submodules so "from qgis.PyQt.QtCore import Qt" works
    sys.modules['qgis'] = qgis_mod
    sys.modules['qgis.PyQt'] = pyqt_mod
    sys.modules['qgis.PyQt.QtCore'] = QtCore
    sys.modules['qgis.PyQt.QtGui'] = QtGui
    sys.modules['qgis.PyQt.QtWidgets'] = QtWidgets


class DummyIface:
    PLUGIN_MENU = object()
    MAPS_TAB = object()

    def __init__(self):
        self.add_action_menu_calls = []

    def addActionMenu(self, title, icon, menu, plugin_menu, maps_tab):
        self.add_action_menu_calls.append((title, plugin_menu, maps_tab))

    def mainWindow(self):
        # minimal main window stub
        class MW:
            def addDockWidget(self, area, dock):
                pass
        return MW()

# Provide a minimal fake 'kadas.kadasgui' module for tests
if 'kadas' not in sys.modules:
    kadas_mod = types.ModuleType('kadas')
    kadas_kadasgui = types.ModuleType('kadas.kadasgui')
    class KadasPluginInterface:
        ActionClassicMenuLocation = types.SimpleNamespace(PLUGIN_MENU=1)
        ActionRibbonTabLocation = types.SimpleNamespace(MAPS_TAB=1)
        PLUGIN_MENU = 1
        MAPS_TAB = 1
        @staticmethod
        def cast(iface):
            return iface
    kadas_kadasgui.KadasPluginInterface = KadasPluginInterface
    kadas_mod.kadasgui = kadas_kadasgui
    sys.modules['kadas'] = kadas_mod
    sys.modules['kadas.kadasgui'] = kadas_kadasgui


def test_init_registers_menu(monkeypatch):
    iface = DummyIface()
    # import the plugin module
    from kadas_maxar.kadas_maxar import KadasMaxar

    plugin = KadasMaxar(iface)
    plugin.initGui()

    assert len(iface.add_action_menu_calls) == 1
    assert iface.add_action_menu_calls[0][0] == "Maxar Open Data"
