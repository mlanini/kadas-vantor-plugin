import sys
import types
import os

# Ensure parent directory is on sys.path so package imports resolve correctly when tests
# are executed from the package folder
THIS_DIR = os.path.dirname(__file__)
PLUGIN_DIR = os.path.abspath(os.path.join(THIS_DIR, '..'))
PARENT_DIR = os.path.abspath(os.path.join(PLUGIN_DIR, '..'))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# minimal qgis.PyQt stubs
if 'qgis' not in sys.modules:
    qgis_mod = types.ModuleType('qgis')
    pyqt_mod = types.ModuleType('qgis.PyQt')
    QtCore = types.ModuleType('qgis.PyQt.QtCore')
    QtCore.Qt = types.SimpleNamespace(
        RightDockWidgetArea=1,
        LeftDockWidgetArea=2,
        UserRole=256,
        AscendingOrder=0,
        DescendingOrder=1,
        Vertical=2,
        AlignCenter=4,
        Checked=2,
        Unchecked=0,
        WaitCursor=3
    )
    class QObject:
        def __init__(self, *a, **k):
            pass
        def tr(self, s):
            return s
    QtCore.QObject = QObject
    class QSettings:
        def __init__(self, *a, **k):
            # simple per-process in-memory settings storage
            if not hasattr(QSettings, '_store'):
                QSettings._store = {}
        def value(self, key, default=None, type=None):
            v = QSettings._store.get(key, default)
            if type is not None:
                try:
                    return type(v) if v is not None else default
                except Exception:
                    return default
            return v
        def setValue(self, key, value):
            QSettings._store[key] = value
        def sync(self):
            # No-op in tests
            pass
        def sync(self):
            pass
    QtCore.QSettings = QSettings
    class QThread:
        def __init__(self):
            self._running = False
        def start(self):
            self._running = True
        def wait(self):
            self._running = False
        def isRunning(self):
            return self._running
    QtCore.QThread = QThread
    class pyqtSignal:
        def __init__(self, *args):
            self._cbs = []
        def connect(self, cb):
            self._cbs.append(cb)
        def emit(self, *args):
            for cb in self._cbs:
                cb(*args)
    QtCore.pyqtSignal = pyqtSignal
    class _QDate:
        def __init__(self, y, m, d):
            self.y = y
            self.m = m
            self.d = d
        @staticmethod
        def currentDate():
            import datetime
            now = datetime.datetime.now()
            return _QDate(now.year, now.month, now.day)
        def toString(self, fmt):
            return f"{self.y:04d}-{self.m:02d}-{self.d:02d}"
    QtCore.QDate = _QDate
    QtGui = types.ModuleType('qgis.PyQt.QtGui')
    def _QIcon(*a, **k):
        return None
    QtGui.QIcon = _QIcon
    
    class _QColor:
        def __init__(self, *a):
            pass
    QtGui.QColor = _QColor
    
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
    class _QDockWidget:
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
        def setAllowedAreas(self, areas):
            self._areas = areas
    class _QWidget:
        def __init__(self, *a, **k):
            self._layout = None
        def setLayout(self, layout):
            self._layout = layout
        def layout(self):
            return self._layout
        def setStyleSheet(self, sheet):
            pass
        def setEnabled(self, enabled):
            pass
        def setVisible(self, visible):
            pass
        def setToolTip(self, tooltip):
            pass
    class _QVBoxLayout:
        def __init__(self, *a, **k):
            self._items = []
        def addWidget(self, w):
            self._items.append(w)
        def addLayout(self, layout):
            self._items.append(layout)
        def count(self):
            return len(self._items)
        def setSpacing(self, s):
            pass
        def setContentsMargins(self, *args):
            pass
        def addRow(self, *args):
            # For QFormLayout compatibility
            pass
        def addStretch(self, *args):
            # For QVBoxLayout compatibility
            pass
    class _QHBoxLayout:
        def __init__(self, *a, **k):
            self._items = []
        def addWidget(self, w):
            self._items.append(w)
        def addLayout(self, layout):
            self._items.append(layout)
        def count(self):
            return len(self._items)
        def addStretch(self, *args):
            pass
        def setContentsMargins(self, *args):
            pass
    class _QLabel:
        def __init__(self, text=''):
            self.text = text
        def setFont(self, font):
            pass
        def setAlignment(self, alignment):
            pass
        def setWordWrap(self, wrap):
            pass
        def setStyleSheet(self, sheet):
            pass
        def setText(self, text):
            self.text = text
    class _QLineEdit:
        def __init__(self, *a, **k):
            self._text = ''
            self._callbacks = []
            self._placeholder = ''
            self._visible = True
        def setText(self, t):
            self._text = t
        def text(self):
            return self._text
        def setPlaceholderText(self, text):
            self._placeholder = text
        def setVisible(self, visible):
            self._visible = visible
        def textChanged_connect(self, cb):
            self._callbacks.append(cb)
        def textChanged(self, cb):
            self._callbacks.append(cb)
    class _QPushButton:
        def __init__(self, *a, **k):
            self._clicks = []
            self._enabled = True
            self._visible = True
            self.clicked = self
        def connect(self, cb):
            self._clicks.append(cb)
        def clicked_connect(self, cb):
            self._clicks.append(cb)
        def setEnabled(self, enabled):
            self._enabled = enabled
        def setVisible(self, visible):
            self._visible = visible
        def setToolTip(self, tooltip):
            pass
    class _QListWidget:
        def __init__(self, *a, **k):
            self._items = []
            self._selected = None
        def addItem(self, it):
            self._items.append(it)
        def clear(self):
            self._items = []
        def count(self):
            return len(self._items)
        def selectedItems(self):
            return [self._selected] if self._selected is not None else []
    class _QComboBox:
        def __init__(self, *a, **k):
            self._items = []
            self._current = -1
            self._callbacks = []
            self._min_width = None
            self._enabled = True
            self._visible = True
            self.currentIndexChanged = self
        def connect(self, cb):
            self._callbacks.append(cb)
        def addItem(self, it):
            self._items.append(it)
        def addItems(self, items):
            self._items.extend(items)
        def count(self):
            return len(self._items)
        def currentIndex(self):
            return self._current
        def setCurrentIndex(self, i):
            old = self._current
            self._current = i
            if old != i:
                for cb in self._callbacks:
                    cb(i)
        def currentIndexChanged_connect(self, cb):
            self._callbacks.append(cb)
        def setMinimumWidth(self, w):
            self._min_width = w
        def currentText(self):
            try:
                return self._items[self._current]
            except Exception:
                return ''
        def currentData(self):
            # Return the current text as data for tests
            return self.currentText()
        def setEnabled(self, enabled):
            self._enabled = enabled
        def setVisible(self, visible):
            self._visible = visible
        def clear(self):
            self._items = []
            self._current = -1
    class _QTableWidget:
        def __init__(self, *a, **k):
            self._columns = 0
            self._rows = []
            self._items = {}
            self._callbacks = []
            self.itemSelectionChanged = self
            self._horizontal_header = types.SimpleNamespace(
                sectionDoubleClicked=types.SimpleNamespace(connect=lambda cb: None), 
                setSectionResizeMode=lambda *a, **k: None, 
                setStretchLastSection=lambda *a, **k: None
            )
        def connect(self, cb):
            self._callbacks.append(cb)
        def horizontalHeader(self):
            return self._horizontal_header
        def setColumnCount(self, n):
            self._columns = n
        def setRowCount(self, n):
            pass
        def rowCount(self):
            return len(self._rows)
        def setHorizontalHeaderLabels(self, labels):
            self._labels = labels
        def setSelectionBehavior(self, *a, **k):
            pass
        def setSelectionMode(self, *a, **k):
            pass
        def setAlternatingRowColors(self, v):
            pass
        def setSortingEnabled(self, enabled):
            pass
        def setItem(self, row, col, item):
            self._items[(row, col)] = item
        def item(self, row, col):
            return self._items.get((row, col))
        def selectedItems(self):
            return []
        def selectionModel(self):
            return types.SimpleNamespace(selectedRows=lambda: [])
        def sortItems(self, col, order=None):
            pass
        def clearContents(self):
            self._items = {}
        def itemSelectionChanged_connect(self, cb):
            self._callbacks.append(cb)
    class _QDateEdit:
        def __init__(self, *a, **k):
            self._date = None
            self._visible = True
            self._enabled = True
        def date(self):
            return self._date
        def setDate(self, d):
            self._date = d
        def setCalendarPopup(self, popup):
            pass
        def setVisible(self, visible):
            self._visible = visible
        def setEnabled(self, enabled):
            self._enabled = enabled
    class _QSpinBox:
        def __init__(self, *a, **k):
            self._value = 0
        def value(self):
            return self._value
        def setValue(self, v):
            self._value = v
        def setRange(self, min_val, max_val):
            pass
        def setSuffix(self, s):
            pass
    
    class _QProgressBar:
        def __init__(self, *a, **k):
            self._value = 0
            self._visible = True
        def setValue(self, v):
            self._value = v
        def value(self):
            return self._value
        def setRange(self, min_val, max_val):
            pass
        def setVisible(self, visible):
            self._visible = visible
    
    class _QSplitter:
        def __init__(self, *a, **k):
            self._widgets = []
        def addWidget(self, widget):
            self._widgets.append(widget)
        def setOrientation(self, orientation):
            pass
        def setSizes(self, sizes):
            pass
    
    class _QGroupBox:
        def __init__(self, *a, **k):
            self._layout = None
            self._enabled = True
        def setLayout(self, layout):
            self._layout = layout
        def layout(self):
            return self._layout
        def setEnabled(self, enabled):
            self._enabled = enabled
    
    class _QCheckBox:
        def __init__(self, *a, **k):
            self._checked = False
            self._callbacks = []
            self._toggled_callbacks = []
            self._state_changed_callbacks = []
            self._enabled = True
            self.toggled = self
            self.stateChanged = self
        def connect(self, cb):
            # This is called for both toggled and stateChanged
            self._toggled_callbacks.append(cb)
            self._state_changed_callbacks.append(cb)
        def setChecked(self, checked):
            old_checked = self._checked
            self._checked = checked
            if old_checked != checked:
                for cb in self._toggled_callbacks:
                    cb(checked)
                for cb in self._state_changed_callbacks:
                    cb(2 if checked else 0)
        def isChecked(self):
            return self._checked
        def setCheckState(self, state):
            self._checked = (state == 2)  # Qt.Checked = 2
        def checkState(self):
            return 2 if self._checked else 0
        def setEnabled(self, enabled):
            self._enabled = enabled
        def setVisible(self, visible):
            pass
        def setToolTip(self, tooltip):
            pass
        def stateChanged_connect(self, cb):
            self._state_changed_callbacks.append(cb)
    
    class _QTableWidgetItem:
        def __init__(self, text=""):
            self._text = text
            self._data = {}
            self._selected = False
        def text(self):
            return self._text
        def setData(self, role, data):
            self._data[role] = data
        def data(self, role):
            return self._data.get(role)
        def setSelected(self, selected):
            self._selected = selected
    
    class _QTabWidget:
        def __init__(self, *a, **k):
            self._tabs = []
        def addTab(self, widget, label):
            self._tabs.append((widget, label))
        def count(self):
            return len(self._tabs)
    
    class _QFileDialog:
        @staticmethod
        def getExistingDirectory(parent, title, path):
            # Return empty string in tests
            return ""
    
    QtWidgets = types.ModuleType('qgis.PyQt.QtWidgets')
    QtWidgets.QAction = _QAction
    QtWidgets.QMenu = _QMenu
    QtWidgets.QMessageBox = _QMessageBox
    QtWidgets.QDockWidget = _QDockWidget
    QtWidgets.QWidget = _QWidget
    QtWidgets.QVBoxLayout = _QVBoxLayout
    QtWidgets.QHBoxLayout = _QHBoxLayout
    QtWidgets.QLabel = _QLabel
    QtWidgets.QLineEdit = _QLineEdit
    QtWidgets.QPushButton = _QPushButton
    QtWidgets.QListWidget = _QListWidget
    QtWidgets.QDateEdit = _QDateEdit
    QtWidgets.QSpinBox = _QSpinBox
    QtWidgets.QTableWidget = _QTableWidget
    QtWidgets.QTableWidgetItem = _QTableWidgetItem
    QtWidgets.QTabWidget = _QTabWidget
    QtWidgets.QFileDialog = _QFileDialog
    QtWidgets.QHeaderView = type('QHeaderView', (), {'ResizeToContents': 0})
    QtWidgets.QAbstractItemView = type('QAbstractItemView', (), {
        'SelectRows': 0,
        'ExtendedSelection': 0
    })
    QtWidgets.QSplitter = _QSplitter
    QtWidgets.QFormLayout = _QVBoxLayout
    QtWidgets.QGroupBox = _QGroupBox
    QtWidgets.QCheckBox = _QCheckBox
    QtWidgets.QComboBox = _QComboBox
    QtWidgets.QProgressBar = _QProgressBar
    QtWidgets.QApplication = type('QApplication', (), {
        'setOverrideCursor': lambda *a: None,
        'restoreOverrideCursor': lambda *a: None,
        'processEvents': lambda *a: None
    })
    QtGui.QFont = type('QFont', (), {
        '__init__': lambda self: None,
        'setPointSize': lambda self, s: None,
        'setBold': lambda self, b: None
    })

    pyqt_mod.QtCore = QtCore
    pyqt_mod.QtGui = QtGui
    pyqt_mod.QtWidgets = QtWidgets
    qgis_mod.PyQt = pyqt_mod

    sys.modules['qgis'] = qgis_mod
    sys.modules['qgis.PyQt'] = pyqt_mod
    sys.modules['qgis.PyQt.QtCore'] = QtCore
    sys.modules['qgis.PyQt.QtGui'] = QtGui
    sys.modules['qgis.PyQt.QtWidgets'] = QtWidgets

# minimal kadas.kadasgui stub
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


import pytest

@pytest.fixture(autouse=True)
def cleanup_module_patches():
    """Cleanup fixture to restore module state after each test (especially after monkeypatch tests)."""
    # Store original classes before tests run
    import kadas_maxar.dialogs.maxar_dock as md_module
    import kadas_maxar.dialogs.settings_dock as sd_module
    
    orig_maxar_vbox = md_module.QVBoxLayout
    orig_maxar_hbox = md_module.QHBoxLayout
    orig_maxar_label = md_module.QLabel
    orig_settings_vbox = sd_module.QVBoxLayout
    orig_settings_label = sd_module.QLabel
    
    yield
    
    # Restore after test
    md_module.QVBoxLayout = orig_maxar_vbox
    md_module.QHBoxLayout = orig_maxar_hbox
    md_module.QLabel = orig_maxar_label
    sd_module.QVBoxLayout = orig_settings_vbox
    sd_module.QLabel = orig_settings_label
