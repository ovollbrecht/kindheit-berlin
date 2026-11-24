# Hinweise zu Drittinhalten

## Daten

Die vollständige Liste mit Links, Datenständen und Abrufdatum steht in [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md)
und in der Anwendung unter „Daten und Methodik“.

| Quelle | Lizenz | Vorgeschriebene Namensnennung |
|---|---|---|
| Geodaten des Landes Berlin (Grünanlagen und Spielplätze, Kitas, Jugendfreizeiteinrichtungen, Schulen, Sportanlagen, ALKIS-Gebäude, Monitoring Soziale Stadtentwicklung, Umweltgerechtigkeit) | [Datenlizenz Deutschland – Zero – Version 2.0](https://www.govdata.de/dl-de/zero-2-0) | keine; die Anbieter werden dennoch genannt |
| Amt für Statistik Berlin-Brandenburg: LOR-Planungsräume, Einwohnerdichte 2022 und 2025 | [CC BY 3.0 DE](https://creativecommons.org/licenses/by/3.0/de/) | „Amt für Statistik Berlin-Brandenburg / [Titel des Datensatzes]“ |
| Polizei Berlin: Verkehrsunfallsituation 2025 | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.de) | „Polizei Berlin“ |
| Unfallatlas 2018–2024 | [Datenlizenz Deutschland – Namensnennung – Version 2.0](https://www.govdata.de/dl-de/by-2-0) | „Statistische Ämter des Bundes und der Länder, Unfallatlas“ |
| OpenStreetMap (Auszug der Geofabrik GmbH) | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) | „© OpenStreetMap-Mitwirkende“ mit Link auf <https://www.openstreetmap.org/copyright> |

Die Anwendung lädt keine Kartenkacheln oder andere Inhalte von Dritten nach. Die Karte zeigt ausschließlich die
mitgelieferte, vereinfachte Geometrie der Planungsräume.

## Software in der Webanwendung

| Komponente | Lizenz |
|---|---|
| [Vue](https://vuejs.org/) und [Vue Router](https://router.vuejs.org/) | MIT |
| [MapLibre GL JS](https://maplibre.org/) | BSD-3-Clause |
| Schriften [Source Serif 4](https://github.com/adobe-fonts/source-serif) und [Source Sans 3](https://github.com/adobe-fonts/source-sans) (über Fontsource, selbst gehostet) | SIL Open Font License 1.1 |

## Software in der Datenaufbereitung

GeoPandas, pandas, Shapely, pyproj, pyogrio, SciPy, NumPy (BSD), Requests (Apache-2.0), pyosmium (BSD-2-Clause),
Matplotlib (PSF-basiert), pytest (MIT). Entwicklungswerkzeuge: Vite, TypeScript, Vitest, Playwright, ESLint, Prettier,
axe-core (MPL-2.0).
