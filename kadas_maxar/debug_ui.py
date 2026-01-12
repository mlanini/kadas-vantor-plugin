from kadas_maxar.dialogs.maxar_dock import MaxarDockWidget

class DummyMainWindow:
    def addDockWidget(self, area, dock):
        pass

class DummyIface:
    PLUGIN_MENU = 1
    MAPS_TAB = 1
    def __init__(self):
        self._main = DummyMainWindow()
    def mainWindow(self):
        return self._main
    def addActionMenu(self, *a, **k):
        pass

iface = DummyIface()
dock = MaxarDockWidget(iface, iface.mainWindow())
print('has_widget', hasattr(dock, 'widget'))
print('has_search', hasattr(dock, 'search'))
print('has_events_list', hasattr(dock, 'events_list'))
print('ui_error', getattr(dock, '_ui_error', None))
print('widget_obj', getattr(dock, '_widget', None))
try:
    w = dock.widget()
    print('widget_layout', getattr(w, '_layout', None))
    if hasattr(w, '_layout'):
        print('layout_items', getattr(w._layout, '_items', None))
except Exception as e:
    print('widget call failed:', e)
