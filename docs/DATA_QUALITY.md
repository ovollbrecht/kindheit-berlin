# Datenqualität und Feedback zu den Datensätzen

Grundlage für die Pflichtangaben im Einreichungsformular (Abschnitt f). Geprüft mit `analysis/00_inspect_raw.py`
und den Auswertungen in `analysis/03_findings.py` (Schlüssel `data_gaps`), Abruf am 24.11.2026.

## Was gut funktioniert

- Alle 14 verwendeten WFS-Layer liefern GeoJSON in EPSG:25833 mit Paging; die Zahl der gelieferten Objekte stimmte
  jedes Mal mit der gemeldeten Gesamtzahl überein. Keine leeren oder ungültigen Geometrien.
- **Einwohnerdichte (Umweltatlas)** enthält seit 2022 Altersgruppen je Block. Das ist für kleinräumige Analysen
  ein großer Gewinn und der Kern dieses Projekts. Die Summe der Altersgruppen entspricht exakt der Blocksumme
  (3.913.505 Einwohner).
- **ALKIS Gebäude** lässt sich serverseitig filtern und auf wenige Attribute beschränken (309.025 Wohngebäude in
  gut einer Minute).
- **LOR, MSS und Umweltgerechtigkeit** verwenden dieselben 542 Planungsräume und lassen sich direkt verknüpfen.

## Qualitätsprobleme

| Datensatz | Befund |
|---|---|
| Einwohnerregisterstatistik je LOR-Planungsraum (CSV) | Die auf daten.berlin.de verlinkten Dateien (`…/opendata/EWR_L21_202512E_Matrix.csv`, auch ältere Jahrgänge) liefern die Startseite des Amts für Statistik mit HTTP 200 statt der Datei. Maschinenlesbar bleiben nur die XLSX-Berichte mit mehrzeiligen Tabellenköpfen. |
| Grünanlagenbestand – Spielplätze | 1.119 von 1.886 ohne Baujahr (59 %), 1.377 ohne Sanierungsjahr (73 %), 82 ohne Widmungsstatus. 40 Plätze mit Netto-Spielfläche 0 bei vorhandener Katasterfläche. Leere Werte sind als Leerzeichen kodiert. |
| Grünanlagenbestand – Spielplätze | Kein Attribut zu Ausstattung, Altersgruppe, Zustand oder Barrierefreiheit. |
| Einwohnerdichte | Altersgruppen erst ab 2022; der Layername wechselt zwischen den Jahrgängen (`ua_einwohnerdichte_2025`, `einwohnerdichte2022`), ebenso das Attribut der Einwohnerzahl (`ew2025`, `ew2022`). Kleine Werte sind gerundet, ohne Hinweis in den Metadaten. |
| Monitoring Soziale Stadtentwicklung 2025 | Attribute heißen nur `s1`–`s4`, `d1`–`d4`, `ki_01`–`ki_20`; `DescribeFeatureType` antwortet mit HTTP 400. Die Bedeutung steht ausschließlich im PDF der Indikatorenblätter. Fehlwerte sind als −9999 kodiert. In der Layerbeschreibung von K14 und K15 steht „in Prozent“, gemeint sind Räume und m². |
| Jugendfreizeiteinrichtungen | Zielgruppenmerkmale nur bei 78 von 418 Einrichtungen gesetzt („ja“ oder leer); 23 Einrichtungen mit identischen Koordinaten; Plätze als Text. |
| Kindertagesstätten | Plätze als Text, 22 ohne Angabe, 32 doppelte Koordinaten. Nur genehmigte Plätze. |
| Standorte öffentlicher Sportanlagen | 508 von 1.085 ohne Flächenangabe; keine Angabe zu Art der Anlage und freier Zugänglichkeit; 745 liegen auf Schulgelände. |
| Verkehrsunfallsituation Berlin (Polizei) | Enthält die Altersgruppe der Beteiligten, aber keine Koordinaten, nur Straßennamen und Postleitzahl. Zeichenkodierung Latin-1 ohne Angabe. Nur das Jahr 2025 verlinkt. |
| Umweltgerechtigkeit 2023/2024 | Nur Klassen (gering/mittel/hoch), keine Messwerte; zwei Planungsräume ohne Lärm- und Grünwert. |

## Fehlende Daten

- **Spielplätze auf Flächen von Wohnungsunternehmen und andere private, öffentlich nutzbare Spielplätze.** In
  OpenStreetMap sind in Berlin 5.544 Spielplätze erfasst, im amtlichen Bestand 1.886. Für Großsiedlungen ändert das
  die Versorgungsaussage grundlegend (70 % gegenüber 97 % der Kinder mit Spielplatz in 400 m).
- **Ergebnisse der amtlichen Spielplatzversorgungsanalyse** als offene Daten (Versorgungsgrad je
  Versorgungsbereich, geschätzte private Spielflächen).
- **Barrierefreiheit und Ausstattung** von Spielplätzen und Jugendfreizeiteinrichtungen.
- **Unfälle mit Koordinaten und Altersgruppe** in einem Datensatz. Bisher hat der Unfallatlas Koordinaten ohne
  Alter, die Polizeistatistik Alter ohne Koordinaten.
- **Belegung und freie Plätze** der Kitas, Kapazitäten und Auslastung der Schulen.
- **Altersgruppen je Block vor 2022** und eine kleinräumige Bevölkerungsprognose als Datensatz im Portal.
- **Schulhofflächen** und ihre Zugänglichkeit außerhalb der Unterrichtszeit.
- **Querungen** (Ampeln, Fußgängerüberwege, Mittelinseln) als amtlicher Datensatz.

## Wünsche und Anregungen

- Sprechende Attributnamen oder eine maschinenlesbare Attributbeschreibung an jedem WFS-Layer.
- Einheitliche Layer- und Attributnamen über Jahrgänge hinweg; fehlende Werte als `null` statt als Leerzeichen
  oder −9999.
- Funktionierende, stabile Download-Adressen für die Einwohnerregisterstatistik als CSV.
- Zahlen als Zahlen (Plätze in Kitas und Jugendfreizeiteinrichtungen).
- Ein Hinweis in den Metadaten der Einwohnerdichte, wie kleine Werte gerundet werden.
- Der Spielplatzdatensatz mit Typ (Kleinkinder, Bolzplatz, Skateanlage) und, wo bekannt, Angaben zur Barrierefreiheit.
