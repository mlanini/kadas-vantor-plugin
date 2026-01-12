"""KADAS Maxar plugin package entry point."""

from .kadas_maxar import KadasMaxar


def classFactory(iface):
    """Entry point used by the KADAS/QGIS plugin loader.

    The loader calls `package.classFactory(iface)` and expects an object
    exposing the plugin interface (initGui/unload, etc.).
    """
    return KadasMaxar(iface)
