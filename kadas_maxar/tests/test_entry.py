def test_package_exposes_classFactory():
    # import package (should import __init__.py)
    import kadas_maxar

    assert hasattr(kadas_maxar, 'classFactory')

    # Minimal iface stub
    class DummyIface:
        PLUGIN_MENU = 1
        MAPS_TAB = 1
        def __init__(self):
            self._main = type('MW', (), {'addDockWidget': lambda self, a, d: None})()
        def addActionMenu(self, title, icon, menu, plugin_menu, maps_tab):
            pass
        def mainWindow(self):
            return self._main

    iface = DummyIface()
    plugin_instance = kadas_maxar.classFactory(iface)

    # basic contract checks
    assert hasattr(plugin_instance, 'initGui')
    assert hasattr(plugin_instance, 'unload')
