def test_load_cog_success(monkeypatch):
    # stub QgsRasterLayer and QgsProject
    added = {}

    class DummyLayer:
        def __init__(self, path, name):
            self._path = path
            self._name = name
        def isValid(self):
            return True

    class DummyProject:
        def __init__(self):
            self.layers = []
        def addMapLayer(self, layer):
            self.layers.append(layer)

    def fake_QgsRasterLayer(path, name):
        return DummyLayer(path, name)

    class DummyProjInst:
        @staticmethod
        def instance():
            return proj

    proj = DummyProject()

    import types
    import kadas_maxar
    from kadas_maxar.dialogs.maxar_dock import MaxarDockWidget

    dock = MaxarDockWidget(kadas_maxar)

    # monkeypatch qgis.core
    monkeypatch.setitem(__import__('sys').modules, 'qgis.core', types.SimpleNamespace(QgsRasterLayer=fake_QgsRasterLayer, QgsProject=DummyProjInst))

    ev = {'title': 'Test', 'cog': 'https://example.com/cog.tif'}
    dock.load_event(ev)
    assert len(proj.layers) == 1


def test_load_cog_invalid(monkeypatch):
    class DummyLayer:
        def __init__(self, path, name):
            pass
        def isValid(self):
            return False

    class DummyProject:
        def __init__(self):
            self.layers = []
        def addMapLayer(self, layer):
            self.layers.append(layer)

    def fake_QgsRasterLayer(path, name):
        return DummyLayer(path, name)

    class DummyProjInst:
        @staticmethod
        def instance():
            return proj

    proj = DummyProject()

    import types
    import kadas_maxar
    from kadas_maxar.dialogs.maxar_dock import MaxarDockWidget

    dock = MaxarDockWidget(kadas_maxar)

    monkeypatch.setitem(__import__('sys').modules, 'qgis.core', types.SimpleNamespace(QgsRasterLayer=fake_QgsRasterLayer, QgsProject=DummyProjInst))

    ev = {'title': 'Test', 'cog': 'https://example.com/invalid.tif'}
    dock.load_event(ev)
    assert len(proj.layers) == 0
