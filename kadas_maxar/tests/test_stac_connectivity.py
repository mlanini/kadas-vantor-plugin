# test_stac_connectivity.py
"""
Test di connettività per il catalogo STAC Maxar Open Data.
Questo script diagnostica problemi di connessione, proxy e timeout.

Uso:
    python kadas_maxar/tests/test_stac_connectivity.py
"""
import os
import sys
import json
import time

from qgis.PyQt.QtCore import QCoreApplication, QEventLoop, QUrl, QByteArray, QTimer
from qgis.PyQt.QtNetwork import QNetworkProxy, QNetworkProxyFactory, QNetworkRequest
from qgis.core import QgsSettings, QgsNetworkAccessManager

STAC_URL = "https://maxar-opendata.s3.dualstack.us-west-2.amazonaws.com/events/catalog.json"
ALTERNATIVE_URL = "https://maxar-opendata.s3.amazonaws.com/events/catalog.json"

def print_section(title):
    """Stampa una sezione formattata."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def apply_kadas_proxy_settings():
    """Applica le impostazioni proxy di KADAS/QGIS come in kadas-albireo2."""
    settings = QgsSettings()
    enabled = settings.value("proxy/enabled", False, type=bool)
    
    print(f"Proxy enabled in settings: {enabled}")
    
    if not enabled:
        QNetworkProxyFactory.setUseSystemConfiguration(True)
        print("✓ Proxy disabilitato: uso configurazione di sistema")
        return

    proxy_type = settings.value("proxy/type", "HttpProxy")
    host = settings.value("proxy/host", "", type=str)
    port = settings.value("proxy/port", 0, type=int)
    user = settings.value("proxy/user", "", type=str)
    password = settings.value("proxy/password", "", type=str)
    excludes = settings.value("proxy/excludes", "", type=str)

    print(f"Proxy type: {proxy_type}")
    print(f"Proxy host: {host}")
    print(f"Proxy port: {port}")
    print(f"Proxy user: {user if user else '(none)'}")
    print(f"Proxy excludes: {excludes if excludes else '(none)'}")

    qt_type_map = {
        "HttpProxy": QNetworkProxy.HttpProxy,
        "HttpCachingProxy": QNetworkProxy.HttpCachingProxy,
        "Socks5Proxy": QNetworkProxy.Socks5Proxy,
        "FtpCachingProxy": QNetworkProxy.FtpCachingProxy,
    }
    qproxy = QNetworkProxy(qt_type_map.get(proxy_type, QNetworkProxy.HttpProxy), host, port, user, password)
    QNetworkProxy.setApplicationProxy(qproxy)
    QNetworkProxyFactory.setUseSystemConfiguration(False)
    print(f"✓ Proxy applicato: {proxy_type}://{host}:{port}")

    # Propaga anche a librerie esterne
    if host and port:
        scheme = "socks5h" if proxy_type.startswith("Socks5") else "http"
        cred = f"{user}:{password}@" if user else ""
        proxy_url = f"{scheme}://{cred}{host}:{port}"
        for var in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
            os.environ[var] = proxy_url
            print(f"  Set env var: {var}={proxy_url[:50]}...")
        if excludes:
            os.environ["NO_PROXY"] = excludes
            os.environ["no_proxy"] = excludes
            print(f"  Set NO_PROXY: {excludes}")

def fetch_stac_catalog(url, timeout=30):
    """Scarica il catalogo STAC usando QgsNetworkAccessManager (proxy aware)."""
    print(f"\nTentativo di connessione a: {url}")
    print(f"Timeout: {timeout} secondi")
    
    start_time = time.time()
    
    nam = QgsNetworkAccessManager.instance()
    req = QNetworkRequest(QUrl(url))
    
    # Headers per debugging
    req.setRawHeader(b"User-Agent", b"KADAS-Vantor-Plugin-Test/0.1.0")
    req.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork)
    
    print("Invio richiesta HTTP...")
    reply = nam.get(req)
    
    loop = QEventLoop()
    reply.finished.connect(loop.quit)
    
    # Timeout timer
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    timer.start(timeout * 1000)
    
    loop.exec_()
    
    elapsed = time.time() - start_time
    print(f"Tempo trascorso: {elapsed:.2f} secondi")
    
    # Verifica timeout
    if not reply.isFinished():
        reply.abort()
        raise Exception(f"⚠️  REQUEST TIMEOUT dopo {timeout} secondi")
    
    # Verifica errori
    if reply.error():
        error_code = reply.error()
        error_msg = reply.errorString()
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        
        error_detail = f"Network error code: {error_code}\n"
        error_detail += f"Error message: {error_msg}\n"
        if status_code:
            error_detail += f"HTTP status code: {status_code}"
        
        raise Exception(f"⚠️  NETWORK ERROR:\n{error_detail}")
    
    # Status code
    status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
    print(f"✓ HTTP Status Code: {status_code}")
    
    # Leggi dati
    data = reply.readAll().data().decode('utf-8')
    print(f"✓ Ricevuti {len(data)} bytes")
    
    return data

def test_basic_connectivity():
    """Test connettività base senza proxy."""
    print_section("Test 1: Connettività Base (senza proxy)")
    
    # Disabilita temporaneamente il proxy
    QNetworkProxyFactory.setUseSystemConfiguration(True)
    QNetworkProxy.setApplicationProxy(QNetworkProxy(QNetworkProxy.NoProxy))
    
    try:
        data = fetch_stac_catalog(STAC_URL, timeout=15)
        catalog = json.loads(data)
        links = catalog.get("links", [])
        child_links = [l for l in links if l.get("rel") == "child"]
        print(f"✓ SUCCESS: Trovati {len(child_links)} eventi nel catalogo")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

def test_with_proxy():
    """Test connettività con proxy configurato."""
    print_section("Test 2: Connettività con Proxy KADAS")
    
    apply_kadas_proxy_settings()
    
    try:
        data = fetch_stac_catalog(STAC_URL, timeout=30)
        catalog = json.loads(data)
        links = catalog.get("links", [])
        child_links = [l for l in links if l.get("rel") == "child"]
        print(f"✓ SUCCESS: Trovati {len(child_links)} eventi nel catalogo")
        
        # Mostra primi 5 eventi
        print("\nPrimi 5 eventi:")
        for i, link in enumerate(child_links[:5], 1):
            event_name = link.get("title", "N/A")
            href = link.get("href", "N/A")
            print(f"  {i}. {event_name}")
            print(f"     URL: {href[:80]}...")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

def test_alternative_url():
    """Test con URL alternativo (senza dualstack)."""
    print_section("Test 3: URL Alternativo (non-dualstack)")
    
    try:
        data = fetch_stac_catalog(ALTERNATIVE_URL, timeout=30)
        catalog = json.loads(data)
        links = catalog.get("links", [])
        child_links = [l for l in links if l.get("rel") == "child"]
        print(f"✓ SUCCESS: Trovati {len(child_links)} eventi nel catalogo")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

if __name__ == "__main__":
    # Avvia una QCoreApplication se non già presente
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication(sys.argv)

    print_section("KADAS Vantor Plugin - Test di Connettività STAC")
    print("Questo script testa la connettività al catalogo STAC Maxar Open Data")
    
    # Esegui tutti i test
    results = {
        "basic": test_basic_connectivity(),
        "proxy": test_with_proxy(),
        "alternative": test_alternative_url()
    }
    
    # Riepilogo
    print_section("RIEPILOGO RISULTATI")
    print(f"Test connettività base:      {'✓ PASS' if results['basic'] else '✗ FAIL'}")
    print(f"Test con proxy KADAS:        {'✓ PASS' if results['proxy'] else '✗ FAIL'}")
    print(f"Test URL alternativo:        {'✓ PASS' if results['alternative'] else '✗ FAIL'}")
    
    if not any(results.values()):
        print("\n⚠️  TUTTI I TEST FALLITI!")
        print("\nPossibili cause:")
        print("  1. Nessuna connessione internet")
        print("  2. Firewall che blocca le connessioni")
        print("  3. Proxy configurato incorrettamente")
        print("  4. Endpoint STAC non raggiungibile")
        print("\nVerifica:")
        print("  - Connessione internet attiva")
        print("  - Impostazioni proxy in KADAS (Settings → Options → Network)")
        print("  - File di log del plugin: ~/.kadas/maxar.log")
    elif results['basic'] and not results['proxy']:
        print("\n⚠️  PROBLEMA CON CONFIGURAZIONE PROXY!")
        print("\nIl test base funziona ma non con il proxy configurato.")
        print("Verifica le impostazioni proxy in KADAS:")
        print("  Settings → Options → Network → Proxy")
    else:
        print("\n✓ Almeno un test è riuscito - la connettività di base funziona")
    
    sys.exit(0 if any(results.values()) else 1)