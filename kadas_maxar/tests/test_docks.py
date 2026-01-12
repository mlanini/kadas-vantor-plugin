def test_toggle_maxar_dock(monkeypatch):
    class DummyMainWindow:
        def __init__(self):
            self.added = []
        def addDockWidget(self, area, dock):
            self.added.append((area, dock))

    class DummyIface:
        PLUGIN_MENU = 1
        MAPS_TAB = 1
        def __init__(self):
            self._main = DummyMainWindow()
            self.add_action_menu_calls = []
        def addActionMenu(self, title, icon, menu, plugin_menu, maps_tab):
            self.add_action_menu_calls.append(title)
        def mainWindow(self):
            return self._main

    iface = DummyIface()
    from kadas_maxar.kadas_maxar import KadasMaxar

    plugin = KadasMaxar(iface)
    plugin.initGui()

    # direct import sanity check
    from kadas_maxar.dialogs.maxar_dock import MaxarDockWidget
    m = MaxarDockWidget(iface, iface.mainWindow())
    assert m is not None

    # Toggle to create dock
    plugin.toggle_maxar_dock()
    assert plugin._maxar_dock is not None
    assert len(iface._main.added) == 1

    # When Qt is available, ensure the object is a QDockWidget
    try:
        from qgis.PyQt.QtWidgets import QDockWidget
        assert isinstance(plugin._maxar_dock, QDockWidget)
    except Exception:
        # If Qt is not available, just ensure the object exposes the expected attributes
        assert hasattr(plugin._maxar_dock, 'visibilityChanged')

    # Toggle hide/show
    plugin.toggle_maxar_dock()
    assert plugin._maxar_dock is not None


def test_toggle_settings_dock(monkeypatch):
    class DummyMainWindow:
        def __init__(self):
            self.added = []
        def addDockWidget(self, area, dock):
            self.added.append((area, dock))

    class DummyIface:
        PLUGIN_MENU = 1
        MAPS_TAB = 1
        def __init__(self):
            self._main = DummyMainWindow()
            self.add_action_menu_calls = []
        def addActionMenu(self, title, icon, menu, plugin_menu, maps_tab):
            self.add_action_menu_calls.append(title)
        def mainWindow(self):
            return self._main

    iface = DummyIface()
    from kadas_maxar import KadasMaxar

    plugin = KadasMaxar(iface)
    plugin.initGui()

    plugin.toggle_settings_dock()
    assert plugin._settings_dock is not None
    assert len(iface._main.added) == 1

    plugin.toggle_settings_dock()
    assert plugin._settings_dock is not None
