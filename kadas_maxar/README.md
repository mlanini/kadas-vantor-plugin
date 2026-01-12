# KADAS Vantor Open Data Plugin

Plugin KADAS per visualizzare e scaricare immagini satellitari ad alta risoluzione dal programma Maxar Open Data.

## Caratteristiche

- **Browsing Eventi**: Esplora eventi di disastro con immagini Maxar disponibili
- **Selezione Interattiva**: Seleziona footprints dalla mappa con Ctrl+Click multi-selezione
- **Sincronizzazione Bidirezionale**: Mappa ↔ Tabella con mapping basato su quadkey
- **Filtri Avanzati**: Cloud cover, date range, ordinamento colonne
- **Caricamento COG**: Immagini visual, multispectral e panchromatic come Cloud Optimized GeoTIFF

## Utilizzo

1. Apri il panel: `View → Panels → Vantor EO Data`
2. Seleziona un evento dal menu a tendina
3. Clicca "Load Footprints"
4. Usa "Select from Map" per selezione interattiva
5. Carica immagini con "Load Visual", "Load MS" o "Load Pan"

## Test

```bash
python -m pytest
```

## Crediti

Adattato da [qgis-maxar-plugin](https://github.com/opengeos/qgis-maxar-plugin) di Qiusheng Wu.

## Licenza

MIT License - Copyright (c) 2026 Michael Lanini (Intelligeo Sàrl)
