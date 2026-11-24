# Architektur

## Überblick

```
Offene Daten ──► pipeline/ + analysis/ (Python) ──► public/data/*.json ──► Vue-Anwendung (statisch) ──► GitHub Pages
```

Alles Aufwendige geschieht vor dem Deployment. Im Betrieb gibt es kein Backend, keine Datenbank, keinen
API-Schlüssel und keine Anfragen an Dritte: Die Anwendung lädt sechs statische Dateien (zusammen rund 1,3 MB,
komprimiert etwa 250 kB).

## Datenaufbereitung (Python)

| Modul | Aufgabe |
|---|---|
| `pipeline/sources.py` | Einziges Register aller Quellen (Titel, Lizenz, Datenstand, Adresse) |
| `pipeline/download.py` | Download mit Cache, Wiederholungen, Paging und Zählkontrolle; schreibt atomar |
| `pipeline/walk_network.py` | Fußwegenetz aus dem OSM-Auszug |
| `pipeline/osm_features.py` | Spielplätze, Bibliotheken und Barrieren aus OSM |
| `pipeline/accessibility.py` | Netzdistanzen (SciPy-Dijkstra), Zugänge, Hauptstraßenvarianten |
| `pipeline/catchment.py` | Zweistufiges Einzugsbereichsverfahren, Greedy-Auswahl |
| `analysis/01…04` | Wohnstandorte, Kennzahlen je Planungsraum, Erkenntnisse und Szenarien, Grafiken |
| `pipeline/export_frontend.py` | Export, Validierung, `docs/DATA_SOURCES.md` |

`data/raw` und `data/interim` (zusammen rund 700 MB) werden nicht versioniert, `data/processed` und `public/data`
schon: Damit ist der veröffentlichte Datenstand im Repository nachvollziehbar.

## Webanwendung

| Verzeichnis | Inhalt |
|---|---|
| `src/domain` | Fachlogik ohne Vue: Typen, Kennzahlen-Konfiguration, Formatierung, Ähnlichkeit, Regeln für Hinweise |
| `src/services` | Laden und Prüfen der Datendateien, einmal je Sitzung |
| `src/composables` | Wiederverwendbare Vue-Logik: Ladezustand, URL-Parameter, Elementbreite |
| `src/components` | Karte, Legende, Suche, Tabellen, Diagramme |
| `src/views` | Sechs Seiten: Story, Explorer, Quartiersprofil, Vergleich, Potenziale, Daten und Methodik |
| `src/styles` | Design-Tokens und Grundstile |

Jede Kennzahl ist genau einmal definiert (`src/domain/indicators.ts`: Bezeichnung, Erklärung, Format,
Klassengrenzen, Quellen). Karte, Tabelle, Profil und Methodikseite lesen diese Definition.

## Entscheidungen

| Entscheidung | Begründung |
|---|---|
| **Hash-Routing** (`/#/explorer`) | GitHub Pages kann keine Pfade auf `index.html` umschreiben. Mit `base: './'` läuft der Build unter jedem Unterpfad; die End-to-End-Tests prüfen das. |
| **Zustand in der URL statt Pinia** | Jede Ansicht ist als Link teilbar; ein globaler Store wäre zusätzlicher Code ohne Nutzen. |
| **MapLibre ohne Basiskarte** | Die Karte zeigt nur die 542 Planungsräume aus der eigenen GeoJSON-Datei. Keine Kacheln von Dritten: kein Datenschutzthema, keine Abhängigkeit von fremden Diensten. MapLibre wird erst geladen, wenn eine Karte erscheint. |
| **Diagramme als eigene SVG- und HTML-Komponenten statt ECharts** | Vier einfache Diagrammtypen. Eigene Komponenten sind klein, vollständig gestaltbar und für Screenreader als Liste oder Tabelle lesbar. ECharts hätte rund 1 MB Code hinzugefügt. |
| **Selbst gehostete Schriften** (Fontsource) | Keine Verbindung zu Google Fonts. |
| **Planungsräume statt Blöcke in der Anwendung** | 542 Flächen sind schnell geladen und mit den amtlichen Sozial- und Umweltdaten vergleichbar. Blockgenaue Karten könnten als Aussage über einzelne Häuser missverstanden werden. |
| **Amtlicher Bestand als Standard, OSM als Umschalter** | Nur der amtliche Bestand hat Flächen; die Lücke wird sichtbar gemacht statt versteckt. |
| **Kein zusammengesetzter Index, keine Rangliste** | Die Qualität einer Kindheit ist nicht messbar; Einzelkennzahlen bleiben überprüfbar. |
| **Feste Regeln statt generierter Texte** | Aussagen im Profil müssen deterministisch und nachprüfbar sein. |

## Farben und Barrierefreiheit

Die drei Serienfarben und die fünfstufige Blauskala wurden mit einem Prüfskript auf Unterscheidbarkeit bei
Farbfehlsichtigkeit getestet. Informationen werden nie nur über Farbe vermittelt: Jede Karte hat eine Tabelle,
jedes Diagramm eine Datentabelle und beschriftete Werte. Geprüft wird mit axe-core gegen WCAG 2.2 AA auf allen
sechs Seiten, in Desktop- und Mobilgröße.

## Qualitätssicherung

| Ebene | Werkzeug | Umfang |
|---|---|---|
| Rechenverfahren | pytest (`tests/pipeline`) | 12 Tests an von Hand nachrechenbaren Beispielen |
| Fachlogik und Datenkonsistenz | Vitest (`tests/unit`) | 37 Tests |
| Nutzungswege, Barrierefreiheit, Unterpfad | Playwright und axe-core (`tests/e2e`) | 17 Tests, Desktop und Mobil |
| Typen und Stil | vue-tsc (strict), ESLint, Prettier | gesamter Code |

GitHub Actions führt alles bei jedem Push aus und veröffentlicht nur bei Erfolg. Die Datenaktualisierung ist ein
eigener, manuell gestarteter Workflow, der einen Pull Request öffnet und bei jedem Fehler abbricht.
