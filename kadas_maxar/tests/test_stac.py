import types


def test_fetch_and_parse(monkeypatch):
    # sample STAC response
    stac = {
        'features': [
            {
                'id': 'evt1',
                'properties': {'title': 'Flood Event A', 'datetime': '2020-01-01', 'eo:cloud_cover': 5},
                'assets': {'cog': {'href': 'https://example.com/a.tif'}},
            },
            {
                'id': 'evt2',
                'properties': {'title': 'Flood B', 'datetime': '2021-05-12', 'eo:cloud_cover': 20},
                'assets': {'visual': {'href': 'https://example.com/b.jpg'}, 'cog': {'href': 'https://example.com/b.tif'}},
            },
        ]
    }

    class DummyResp:
        status_code = 200
        def json(self):
            return stac

    def fake_get(url, params=None, timeout=0):
        return DummyResp()

    import kadas_maxar
    from kadas_maxar.dialogs.maxar_dock import MaxarDockWidget

    dock = MaxarDockWidget(kadas_maxar)
    # inject fake requests
    dock._requests = types.SimpleNamespace(get=fake_get)

    events = dock.fetch_stac('https://example.com/stac')
    assert events is not None
    assert len(events) == 2
    assert events[0]['title'] == 'Flood Event A'
    assert events[0]['cog'].endswith('a.tif')


def test_fetch_failure(monkeypatch):
    def fake_get_fail(url, params=None, timeout=0):
        class R:
            status_code = 500
            def json(self):
                return {}
        return R()

    import kadas_maxar
    from kadas_maxar.dialogs.maxar_dock import MaxarDockWidget

    dock = MaxarDockWidget(kadas_maxar)
    dock._requests = types.SimpleNamespace(get=fake_get_fail)

    events = dock.fetch_stac('https://example.com/stac')
    assert events is None
