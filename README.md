# KADAS Vantor Open Data Plugin

Plugin KADAS per visualizzare e scaricare immagini satellitari ad alta risoluzione dal programma Maxar Open Data.

![KADAS Vantor Plugin](kadas_maxar/icons/icon.svg) 
Vector icon by [SVG Repo](https://www.svgrepo.com)

## Caratteristiche

- **Browsing Eventi**: Esplora eventi di disastro naturale con immagini satellitari Maxar disponibili
- **Selezione Interattiva**: Seleziona footprints direttamente dalla mappa con sincronizzazione bidirezionale mappa-tabella
- **Filtri Avanzati**: Filtra per copertura nuvolosa, intervallo temporale e altre proprietà
- **Caricamento COG**: Carica immagini come Cloud Optimized GeoTIFF (visual, multispectral, panchromatic)
- **Integrazione KADAS**: Completamente integrato nell'interfaccia KADAS Albireo

## Funzionalità Principali

### Selezione Interattiva
- Click sulla mappa per selezionare footprints individuali
- Ctrl+Click per selezione multipla
- Sincronizzazione automatica tra mappa e tabella
- Funziona anche con tabella ordinata

### Filtri
- Copertura nuvolosa massima (0-100%)
- Intervallo di date personalizzabile
- Applicazione dinamica dei filtri

### Gestione Immagini
- Visualizzazione metadati (data, piattaforma, GSD, cloud cover)
- Caricamento immagini visual (RGB)
- Caricamento immagini multispettrali
- Caricamento immagini pancromatiche
- Zoom automatico su selezione

## Installazione

### Da File ZIP
1. Scarica l'ultima release da [GitHub Releases](https://github.com/mlanini/kadas-vantor-plugin/releases)
2. In KADAS, vai a `Plugins → Manage and Install Plugins → Install from ZIP`
3. Seleziona il file ZIP scaricato
4. Riavvia KADAS

### Da Repository Git
```bash
cd %APPDATA%/kadas-albireo2/python/plugins
git clone https://github.com/mlanini/kadas-vantor-plugin.git kadas_maxar
```

### Installazione Manuale
1. Copia la cartella `kadas_maxar` in:
   - Windows: `%APPDATA%/kadas-albireo2/python/plugins/`
   - Linux: `~/.local/share/kadas-albireo2/python/plugins/`
   - macOS: `~/Library/Application Support/kadas-albireo2/python/plugins/`
2. Riavvia KADAS
3. Abilita il plugin da `Plugins → Manage and Install Plugins`

## Utilizzo

### 1. Aprire il Panel
- Menu: `View → Panels → Vantor EO Data`
- Oppure toolbar: click sull'icona Vantor

### 2. Selezionare un Evento
- Usa il menu a tendina "Event Selection"
- Clicca "Refresh Events" per aggiornare la lista
- Seleziona un evento di interesse

### 3. Caricare Footprints
- Clicca "Load Footprints" per caricare i poligoni sulla mappa
- I footprints vengono visualizzati come layer vettoriale blu semitrasparente

### 4. Filtrare e Selezionare
- Imposta filtri (cloud cover, date range)
- Clicca "Apply Filters" per applicare
- Usa "Select from Map" per selezione interattiva dalla mappa
- Oppure seleziona righe dalla tabella

### 5. Caricare Immagini
- Seleziona uno o più footprints
- Clicca su "Load Visual", "Load MS" o "Load Pan"
- Le immagini vengono caricate come layer raster COG

## Requisiti

- KADAS Albireo 2.x
- QGIS 3.x core libraries
- Python 3.7+
- Connessione internet per scaricare dati da GitHub e AWS S3

## Sviluppo

### Setup Ambiente di Test
```bash
cd kadas_maxar
python -m pytest
```

### Creazione Pacchetto per Distribuzione

Per creare un file ZIP pronto per il caricamento sul repository plugin QGIS:

#### Usando Python (raccomandato)
```bash
# Crea kadas-vantor-plugin-0.1.0.zip
python package_plugin.py

# Opzioni
python package_plugin.py --output dist/myplugin.zip
python package_plugin.py --no-version
python package_plugin.py --help
```

#### Usando Bash (Linux/macOS)
```bash
# Crea kadas-vantor-plugin-0.1.0.zip
chmod +x package_plugin.sh
./package_plugin.sh

# Opzioni
./package_plugin.sh --output dist/
./package_plugin.sh --no-version
./package_plugin.sh --help
```

Il file ZIP generato contiene:
- Solo i file essenziali del plugin
- Esclude test, cache, file di sviluppo
- Pronto per installazione in KADAS/QGIS
- Conforme alle specifiche del repository plugin QGIS

### Struttura del Progetto
```
kadas_maxar/
├── __init__.py              # Entry point del plugin
├── kadas_maxar.py           # Classe principale del plugin
├── logger.py                # Sistema di logging
├── metadata.txt             # Metadati del plugin
├── dialogs/
│   ├── maxar_dock.py        # Dock widget principale
│   └── settings_dock.py     # Pannello impostazioni
├── icons/                   # Icone SVG
├── tests/                   # Test suite
└── README.md
```

### Test
```bash
# Esegui tutti i test
python -m pytest

# Test specifici
python -m pytest tests/test_ui.py -v

# Coverage
python -m pytest --cov=kadas_maxar
```

## Changelog

### v0.1.0 (2026-01-12)
- ✅ Selezione interattiva da mappa con Ctrl+Click multi-selezione
- ✅ Sincronizzazione bidirezionale mappa ↔ tabella
- ✅ Mapping basato su quadkey (sort-safe)
- ✅ Filtri per cloud cover e date range
- ✅ Caricamento immagini COG (visual, MS, pan)
- ✅ Gestione CRS automatica
- ✅ Logging completo per debugging

## Crediti

Basato su [qgis-maxar-plugin](https://github.com/opengeos/qgis-maxar-plugin) di Qiusheng Wu.

Adattato per KADAS da Michael Lanini ([Intelligeo](https://www.intelligeo.ch)).

Dati forniti da [Maxar Open Data Program](https://www.maxar.com/open-data).

## Licenza

MIT License - vedi file LICENSE per dettagli.

## Supporto

- Issues: [GitHub Issues](https://github.com/mlanini/kadas-vantor-plugin/issues)
- Email: michael@intelligeo.ch

## Screenshot

### Panel Principale
![Main Panel](docs/screenshots/main_panel.png)

### Selezione Interattiva
![Interactive Selection](docs/screenshots/selection_mode.png)

### Filtri Applicati
![Filters](docs/screenshots/filters.png)
