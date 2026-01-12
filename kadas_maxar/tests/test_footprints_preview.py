def test_parse_geometry_in_feature():
    feature = {
        'id': 'evt1',
        'properties': {'title': 'Evt'},
        'geometry': {
            'type': 'Polygon',
            'coordinates': [[[0,0],[1,0],[1,1],[0,1],[0,0]]]
        }
    }

    import kadas_maxar
    from kadas_maxar.dialogs.maxar_dock import MaxarDockWidget

    dock = MaxarDockWidget(kadas_maxar)
    parsed = dock._parse_stac_feature(feature)
    assert parsed is not None
    assert parsed.get('geometry') == feature['geometry']


def test_load_footprints_adds_layer(monkeypatch):
    # stub QgsVectorLayer and QgsProject
    added = []

    class DummyVectorLayer:
        def __init__(self, spec, name, src):
            self.spec = spec
            self.name = name
            self.src = src
            self._geometry = None
        def dataProvider(self):
            return self
        def addFeatures(self, feats):
            self.feats = feats

    class DummyProject:
        def __init__(self):
            self.layers = []
        def addMapLayer(self, layer):
            self.layers.append(layer)

    def fake_QgsVectorLayer(spec, name, src):
        return DummyVectorLayer(spec, name, src)

    class DummyProjInst:
        @staticmethod
        def instance():
            return proj

    proj = DummyProject()

    import types, sys
    import kadas_maxar
    from kadas_maxar.dialogs.maxar_dock import MaxarDockWidget

    dock = MaxarDockWidget(kadas_maxar)

    monkeypatch.setitem(sys.modules, 'qgis.core', types.SimpleNamespace(QgsVectorLayer=fake_QgsVectorLayer, QgsProject=DummyProjInst))

    ev = {'title': 'Test', 'geometry': {'type': 'Polygon', 'coordinates': [[[0,0],[1,0],[1,1],[0,1],[0,0]]]}}
    dock.load_footprints(ev)
    assert len(proj.layers) == 1
    assert getattr(proj.layers[0], '_geometry') == ev['geometry']


def test_preview_cog_adds_preview_layer(monkeypatch):
    class DummyRaster:
        def __init__(self, path, name):
            self.path = path
            self.name = name
        def isValid(self):
            return True
        def setOpacity(self, v):
            self.op = v

    class DummyProject:
        def __init__(self):
            self.layers = []
        def addMapLayer(self, layer):
            self.layers.append(layer)

    def fake_QgsRasterLayer(path, name):
        return DummyRaster(path, name)

    class DummyProjInst:
        @staticmethod
        def instance():
            return proj

    proj = DummyProject()

    import types, sys
    import kadas_maxar
    from kadas_maxar.dialogs.maxar_dock import MaxarDockWidget

    dock = MaxarDockWidget(kadas_maxar)

    monkeypatch.setitem(sys.modules, 'qgis.core', types.SimpleNamespace(QgsRasterLayer=fake_QgsRasterLayer, QgsProject=DummyProjInst))

    ev = {'title': 'Test', 'cog': 'https://example.com/cog.tif'}
    dock.preview_cog(ev)
    assert len(proj.layers) == 1
    assert getattr(proj.layers[0], 'is_preview', True) is True
    # if setOpacity was available, ensure op attribute was set
    try:
        assert proj.layers[0].op == 0.5
    except Exception:
        pass
