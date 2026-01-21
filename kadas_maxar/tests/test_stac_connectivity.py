# test_stac_connectivity.py
import os
import sys
import json

from qgis.PyQt.QtCore import QCoreApplication, QEventLoop, QUrl, QByteArray
from qgis.PyQt.QtNetwork import QNetworkProxy, QNetworkProxyFactory
from qgis.core import QgsSettings, QgsNetworkAccessManager

STAC_URL = "https://maxar-opendata.s3.dualstack.us-west-2.amazonaws.com/events/catalog.json"

def apply_kadas_proxy_settings():
    """Applica le impostazioni proxy di KADAS/QGIS come in kadas-albireo2."""
    settings = QgsSettings()
    enabled = settings.value("proxy/enabled", False, type=bool)
    if not enabled:
        QNetworkProxyFactory.setUseSystemConfiguration(True)
        print("Proxy disabilitato: uso configurazione di sistema")
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
    QNetworkProxyFactory.setUseSystemConfiguration(False)
    print(f"Proxy applicato: {proxy_type}://{host}:{port}")

    # Propaga anche a librerie esterne
    if host and port:
        scheme = "socks5h" if proxy_type.startswith("Socks5") else "http"
        cred = f"{user}:{password}@" if user else ""
        proxy_url = f"{scheme}://{cred}{host}:{port}"
        for var in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
            os.environ[var] = proxy_url
        if excludes:
            os.environ["NO_PROXY"] = excludes

def fetch_stac_catalog(url):
    """Scarica il catalogo STAC usando QgsNetworkAccessManager (proxy aware)."""
    nam = QgsNetworkAccessManager.instance()
    req = QUrl(url)
    reply = nam.get(nam.createRequest(QgsNetworkAccessManager.GetOperation, req, QByteArray()))
    loop = QEventLoop()
    reply.finished.connect(loop.quit)
    loop.exec_()
    if reply.error():
        raise Exception(reply.errorString())
    data = reply.readAll().data().decode('utf-8')
    return data

if __name__ == "__main__":
    # Avvia una QCoreApplication se non già presente
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication(sys.argv)

    print("Applico impostazioni proxy KADAS/QGIS...")
    apply_kadas_proxy_settings()

    print(f"Scarico catalogo STAC da {STAC_URL} ...")
    try:
        catalog_str = fetch_stac_catalog(STAC_URL)
        catalog = json.loads(catalog_str)
        features = catalog.get("features", [])
        print(f"Catalogo STAC scaricato correttamente. Eventi trovati: {len(features)}")
        for i, feat in enumerate(features[:5]):
            props = feat.get("properties", {})
            print(f"Evento {i+1}: {props.get('event_name') or props.get('title') or props.get('id')}")
    except Exception as e:
        print(f"Errore nel recupero del catalogo STAC: {e}")