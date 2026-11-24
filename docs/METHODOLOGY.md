# Methodik

Alle Rechenschritte liegen als Code vor. Diese Datei beschreibt, was sie tun, welche Annahmen dahinterstehen und
wo die Grenzen liegen. Koordinatensystem aller Berechnungen: ETRS89 / UTM 33N (EPSG:25833), Längen und Flächen in Metern.

| Schritt | Skript | Ergebnis |
|---|---|---|
| 1 Download | `pipeline/download.py` | `data/raw/` mit `manifest.json` (Abrufdatum, Umfang) |
| 2 Fußwegenetz | `pipeline/walk_network.py` | `data/interim/walk_graph.npz` |
| 3 OSM-Objekte | `pipeline/osm_features.py` | weitere Spielplätze, Bibliotheken, Barrieren |
| 4 Erreichbarkeit | `analysis/01_home_accessibility.py` | `homes.csv`, Distanzmatrizen |
| 5 Kennzahlen | `analysis/02_planning_area_indicators.py` | `data/processed/plr_indicators.csv` |
| 6 Erkenntnisse | `analysis/03_findings.py` | `data/processed/findings.json`, Falllisten, Szenarien |
| 7 Export und Validierung | `pipeline/export_frontend.py` | `public/data/`, `docs/DATA_SOURCES.md` |
| 8 Grafiken | `analysis/04_figures.py` | `docs/figures/` |

## 1. Wo Kinder wohnen

**Daten:** Einwohner je Block nach Altersgruppen (unter 6, 6 bis unter 10, 10 bis unter 18) am 31.12.2025;
ALKIS-Gebäude mit Wohnfunktion (Funktionsschlüssel unter 1300).

**Verfahren:** Die Einwohner eines Blocks werden auf seine Wohngebäude verteilt, proportional zur Geschossfläche
(Grundfläche × Zahl der oberirdischen Geschosse, fehlende Geschosszahl = 1). Seniorenheime (1022) und
Studierendenwohnheime (1024) erhalten keine Kinder. Jedes Gebäude wird dem nächsten Knoten des Fußwegenetzes
zugeordnet, der nicht auf einer Hauptstraße liegt. Gebäude mit demselben Knoten werden zusammengefasst. Ergebnis:
166.695 Wohnstandorte mit (gebrochenen) Kinderzahlen; die Summe je Block bleibt exakt erhalten (wird geprüft).

**Annahmen und Grenzen:**
- Innerhalb eines Blocks ist die Altersstruktur in allen Gebäuden gleich.
- 611 bewohnte Blöcke (6.047 Kinder) haben kein Wohngebäude nach ALKIS; sie erhalten einen Standort im Block.
- Kleine Blockwerte sind vom Amt für Statistik aus Geheimhaltungsgründen gerundet.
- Sensitivität: Mit nur einem Punkt je Block läge der Berliner Wert „Spielplatz in 400 m Fußweg“ bei 68 % statt 70 %.

## 2. Fußwegenetz

Aus dem OpenStreetMap-Auszug werden alle Wege mit `highway=*` übernommen, außer Autobahnen und Schnellstraßen,
Baustellen, Wegen mit `foot=no|private|use_sidepath` und Wegen mit gesperrtem `access` (sofern `foot` nichts anderes
sagt). Jeder Wegpunkt ist ein Knoten, die Kantenlänge ist die ebene Entfernung. Verwendet wird nur die größte
zusammenhängende Komponente (97,2 % der Knoten). Steigungen, Wartezeiten und Zäune sind nicht modelliert.

Berliner Hauptstraßen haben meist getrennt erfasste Gehwege (`foot=use_sidepath`); die Fahrbahn selbst gehört dann
nicht zum Netz. Gequert wird über Wege, die die Fahrbahn an einem gemeinsamen Knoten kreuzen.

## 3. Entfernungen

- **Zugänge:** Eine Fläche (Spielplatz, Grünanlage) gilt an jedem Netzknoten im Umkreis von 15 m als erreicht.
  Liegt kein Knoten so nah, zählt der nächste Knoten bis 150 m. Punkte (Kita, Schule, Jugendfreizeiteinrichtung,
  Sportanlage, Bibliothek) werden am nächsten Knoten erreicht.
- **Fußweg:** kürzester Weg im Netz (Dijkstra) vom Wohnstandort zum nächsten Zugang.
- **Luftlinie:** Entfernung vom selben Wohnstandort zur Fläche, abzüglich der 15 m Zugangstoleranz und nie größer
  als der Fußweg, damit beide Maße am selben Ort enden.
- **Grünanlage:** nur Anlagen ab 0,5 Hektar (Kriterium der Berliner Analyse wohnungsnaher Grünanlagen).
- **Grundschule:** nächste öffentliche Grundschule, nicht die laut Einschulbereich zuständige.

## 4. Hauptstraßen

Ein Knoten gilt als Hauptstraßenknoten, wenn er auf einem Weg der OSM-Klassen `primary`, `secondary` oder `trunk`
liegt. Gerechnet werden zwei zusätzliche Varianten des nächsten Spielplatzes:

1. **ohne Hauptstraße:** Alle Hauptstraßenknoten sind gesperrt.
2. **nur gesicherte Querungen:** Gesperrt sind Hauptstraßenknoten ohne Ampel (`highway=traffic_signals`,
   `crossing=traffic_signals`, `crossing:signals=yes`) und ohne Markierung (`crossing=marked|zebra|uncontrolled`,
   `crossing:markings`), am Knoten oder am querenden Weg.

Grenzen: Die Straßenklasse ist kein Maß für Verkehrsmenge oder Geschwindigkeit. Querungsmerkmale sind in
OpenStreetMap nicht vollständig; „ungesichert“ heißt „keine Sicherung erfasst“.

## 5. Angebot je Kind (zweistufiges Einzugsbereichsverfahren)

Für Spielfläche, Plätze in Jugendfreizeiteinrichtungen und Kita-Plätze (`pipeline/catchment.py`):

1. Die Kapazität jedes Angebots wird durch die gesamte Nachfrage im Einzugsbereich geteilt (Spielfläche: alle unter
   18-Jährigen in 1000 m Fußweg; Jugendfreizeiteinrichtungen: 10- bis 17-Jährige; Kitas: unter 6-Jährige).
2. Jeder Wohnstandort summiert die Quoten aller Angebote, die er erreicht.

Die Kapazität aller Angebote mit Nachfrage wird genau einmal verteilt; das prüft das Skript bei jeder Rechnung.
Verwaltungsgrenzen spielen keine Rolle. Kapazitäten: Netto-Spielfläche (`nettospfl`), Plätze (`e_platz`). Kita-Plätze
sind genehmigte Plätze, bezogen auf alle unter 6-Jährigen.

Zum Vergleich weist das Quartiersprofil die Sicht des amtlichen Richtwerts aus: Netto-Spielfläche im Planungsraum je
Einwohner (Richtwert 1 m² nach § 4 Kinderspielplatzgesetz Berlin). Berlinweit ergibt das 0,60 m², was der amtlichen
Angabe von rund 60 % entspricht.

## 6. Schwellen und Aggregation

- 200 m für unter 6-Jährige, 400 m als Standard, 1000 m für Jugendliche und für Flächenquoten (angelehnt an
  DIN 18034). Die Erreichbarkeit von Spielplätzen liegt für 200, 300, 400, 500, 800 und 1000 m vor.
- Planungsraumwerte sind mit der jeweiligen Altersgruppe gewichtet; „mittlerer Fußweg“ ist der gewichtete Median.
- In Planungsräumen mit weniger als 100 Kindern (7 von 542) werden keine Anteile und Mittelwerte ausgewiesen.
- Fehlende Werte bleiben fehlend (`null`), sie werden nie als 0 dargestellt. Zwei unbewohnte Planungsräume haben
  die Kinderzahl 0.

## 7. Amtlicher Bestand und OpenStreetMap

Der amtliche Datensatz enthält die öffentlichen Spielplätze der Bezirke (1.886). Spielplätze von
Wohnungsunternehmen fehlen. Als zweite Sicht werden alle in OpenStreetMap als `leisure=playground` erfassten Plätze
ergänzt, die nicht als `access=private|customers|no|permit|residents` markiert sind. Für diese Plätze gibt es keine
Flächen; Flächenkennzahlen beruhen deshalb immer nur auf dem amtlichen Bestand.

## 8. Szenarien

**Frage:** Welche Standorte brächten die meisten Kinder, die bisher keinen Spielplatz in 400 m Fußweg haben, in die
Nähe eines Angebots?

- **Kandidaten Grünanlage:** öffentliche Grünanlagen ab 2.000 m² ohne Spielplatz im Umkreis von 50 m (994).
- **Kandidaten Schulhof:** alle öffentlichen Grundschulen (387).
- **Verfahren:** Greedy-Lösung des Maximum-Coverage-Problems (`greedy_max_coverage`): Schritt für Schritt wird der
  Standort gewählt, der die meisten noch nicht erreichten Kinder in 400 m Fußweg hinzugewinnt. Erreichte Kinder
  werden aus der Nachfrage entfernt, also nie doppelt gezählt. Das Ergebnis erreicht mindestens 63 % des Optimums.
- **Zwei Zählweisen:** „amtlich“ (Kinder ohne öffentlichen Spielplatz in 400 m) und „vorsichtig“ (Kinder ohne
  irgendeinen bekannten Spielplatz, auch laut OpenStreetMap).

Nicht berücksichtigt: Eigentum, Naturschutz, Größe und Eignung der Fläche, Kosten, Aufsicht, bestehende Planungen.
Die Szenarien sind Rechenmodelle und keine Planungsempfehlung.

## 9. Ähnliche Quartiere

Vier Merkmale werden über alle Planungsräume mit mindestens 100 Kindern standardisiert (Mittelwert 0,
Standardabweichung 1): Einwohner je Hektar bewohnter Blockfläche, Anteil der unter 18-Jährigen, Kinderarmut, Zahl
der Kinder. Ähnlichkeit ist der euklidische Abstand in diesem Raum (`src/domain/similarity.ts`).
Versorgungskennzahlen gehen nicht ein.

## 10. Automatische Hinweise im Quartiersprofil

Die Hinweise entstehen aus acht festen Regeln (`src/domain/insights.ts`), jeweils mit Schwelle und den zugrunde
liegenden Zahlen im Text:

| Regel | Bedingung |
|---|---|
| Abweichung von Berlin | Anteil mit Spielplatz in 400 m weicht um mindestens 15 Prozentpunkte ab |
| Umwege | Luftlinie liegt mindestens 25 Prozentpunkte über Fußweg |
| Hauptstraße | ohne Querung mindestens 15 Prozentpunkte weniger |
| Amtlicher Bestand | mit OpenStreetMap mindestens 25 Prozentpunkte mehr |
| Spielfläche | unter dem 0,5-Fachen oder über dem 1,5-Fachen des Berliner Werts |
| Wachstum | Kinderzahl seit 2022 um mindestens 10 % gestiegen und Erreichbarkeit unter Berlin |
| Jugendliche | weniger als die Hälfte hat eine Jugendfreizeiteinrichtung in 1000 m |
| Kita | weniger als 0,6 genehmigte Plätze je Kind unter 6 |

In Planungsräumen mit weniger als 100 Kindern erscheint kein Hinweis.

## 11. Sozialer und ökologischer Kontext

- Kinderarmut (S4), Kinder in alleinerziehenden Haushalten (S2), Wohnfläche (K15) und Status-Index stammen aus dem
  Monitoring Soziale Stadtentwicklung 2025 (Stand 31.12.2024). Werte mit dem Vermerk „ungültig“ werden nicht verwendet.
- Lärm, Luft, thermische Belastung und Grünversorgung stammen aus dem Umweltgerechtigkeitsatlas 2023/2024 und
  liegen nur als Klassen je Planungsraum vor.
- Unfälle: Unfallatlas 2018 bis 2024, Unfälle mit Personenschaden und Beteiligung von Fußgängern oder
  Radfahrenden, montags bis freitags 7–8 und 13–16 Uhr. Das Alter der Beteiligten ist unbekannt; die Zahl beschreibt
  das Verkehrsumfeld, nicht das Risiko einzelner Kinder.

Zusammenhänge zwischen diesen Größen und der Erreichbarkeit sind Korrelationen auf Gebietsebene. Sie erlauben keine
Aussage über einzelne Kinder oder Familien und keine über Ursachen.

## 12. Qualitätssicherung

- `tests/pipeline/`: Einzugsbereiche, Greedy-Auswahl ohne Doppelzählung, Netzdistanzen, Hauptstraßenvarianten an
  kleinen, von Hand nachrechenbaren Beispielen.
- `pipeline/export_frontend.py`: validiert den Export (542 Gebiete, Summen, Wertebereiche, Monotonie) und ersetzt
  den veröffentlichten Stand erst danach.
- `tests/unit/data.test.ts`: Karte, Tabellen und Story greifen auf dieselben Werte zu; die veröffentlichten
  Kernzahlen sind dort festgehalten.
- Abgleich mit unabhängigen Angaben: Einwohnersumme der Blöcke, amtlicher Versorgungsgrad von rund 60 %,
  Kinderarmutsquote des MSS, jährliche Unfallzahl.
