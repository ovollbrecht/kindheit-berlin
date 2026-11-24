# Erkenntnisse

Stand der Bevölkerungsdaten: 31.12.2025. Alle Zahlen stehen in `data/processed/findings.json` und werden von
`analysis/03_findings.py` berechnet; der Schlüssel in Klammern nennt die Fundstelle. Die Kernzahlen sind zusätzlich
in `tests/unit/data.test.ts` festgehalten.

## Bestätigte Erkenntnisse

1. **Der Fußweg ist länger als die Luftlinie verspricht.** 86 % der 627.759 unter 18-Jährigen wohnen höchstens
   400 m Luftlinie von einem öffentlichen Spielplatz, 70 % höchstens 400 m Fußweg. Differenz: 100.921 Kinder.
   Mittlerer Fußweg 280 m, mittlere Luftlinie 173 m, mittlerer Umwegfaktor 1,45.
   (`straight_line_versus_walking`, `detours`)
2. **Große Barrieren erklären nur ein Zehntel.** Bei den betroffenen Kindern liegt auf der direkten Linie zu 7,4 %
   eine Bahntrasse, zu 2,5 % ein Gewässer, zu 1,4 % eine Autobahn; bei 89,9 % keine davon. (`barriers`)
3. **Hauptstraßen trennen.** 31.295 Kinder erreichen ihren Spielplatz in 400 m nur über eine Hauptstraße, 6.604
   davon nur über eine Querung ohne erfasste Ampel oder Markierung. (`straight_line_versus_walking`)
4. **Kurze Wege bei niedrigem sozialen Status, wenig Fläche bei sehr niedrigem.** Spielplatz in 400 m: hoch 47 %,
   mittel 75 %, niedrig 77 %, sehr niedrig 69 %. Erreichbare Spielfläche je Kind: 3,2 / 3,9 / 4,2 / 3,4 m².
   Jugendfreizeiteinrichtung in 1000 m: 38 / 79 / 92 / 97 %. Treiber ist die Bebauungsdichte (Rangkorrelation Dichte
   und Erreichbarkeit 0,72). (`by_social_status`, `correlations_spearman`)
5. **Die Kinderzahl wächst am Rand.** Ende 2022 bis Ende 2025: innere Stadt −5,0 %, äußere Stadt +1,6 %, Berlin
   −0,8 %. In 61 Planungsräumen mit mindestens +10 % (zusammen +10.884 Kinder) haben 62 % einen Spielplatz in 400 m,
   in schrumpfenden Räumen 78 %. (`growth_2022_2025`)
6. **Der amtliche Bestand ist unvollständig.** 1.886 öffentliche Spielplätze stehen 5.544 in OpenStreetMap
   gegenüber. Mit den nicht als privat markierten OSM-Plätzen steigt der Berliner Wert von 70 % auf 84 %, in
   Großsiedlungen von 70 % auf 97 %. (`osm_robustness`)
7. **Jugendliche haben die weitesten Wege.** 76 % der 10- bis 17-Jährigen haben eine Jugendfreizeiteinrichtung in
   1000 m; 66.216 nicht, 11.904 auch nicht in 2000 m. (`age_groups`)
8. **Wenige Standorte könnten viele Kinder erreichen (Modellrechnung).** 25 neue Spielplätze in bestehenden
   Grünanlagen: 20.097 Kinder zusätzlich (vorsichtig gerechnet 9.806). 25 geöffnete Grundschulhöfe: 10.651
   (vorsichtig 4.799). (`new_playground_scenario`, `schoolyard_scenario` und die Varianten `_incl_osm`)
9. **Der Richtwert je Einwohner und die Sicht der Kinder weichen voneinander ab.** Rangkorrelation zwischen
   „m² je Einwohner im Planungsraum“ und „erreichbare m² je Kind“: 0,55. In 44 Planungsräumen liegt kein Spielplatz;
   10.960 der 29.970 Kinder dort erreichen trotzdem einen in 400 m. (`supply_per_child`)

## Widerlegte Erwartungen

- **Wenig Spielfläche und hohe Umweltbelastung fallen nicht zusammen.** In drei- und vierfach belasteten
  Planungsräumen haben 86 % der Kinder einen Spielplatz in 400 m, in unbelasteten 57 %. (`multiple_disadvantage`)
- **Ärmere Quartiere haben keine längeren Wege**, siehe Erkenntnis 4.

## Ergänzende Befunde

- Kita: 0,93 genehmigte Plätze je Kind unter 6; in Planungsräumen mit sehr niedrigem Status 0,86. (`daycare_capacity`)
- Ohne eigenen Garten und ohne öffentlichen Spielplatz in 400 m: 117.311 Kinder im Geschosswohnungsbau, mit
  OSM-Plätzen gerechnet 40.876. (`housing_types`)
- 7.229 Kinder wohnen in Blöcken des Typs Gewerbe- und Industriegebiet; 46 % haben einen Spielplatz in 400 m.
  (`commercial_areas`)
- Im 250-m-Umkreis öffentlicher Grundschulen: 2.766 Unfälle mit verletzten Fußgängern oder Radfahrenden zu
  Schulwegzeiten in sieben Jahren; Median je Schule 5, Maximum 44. (`accidents_around_primary_schools`)
- In 36 Planungsräumen mit 52.643 Kindern treffen mindestens drei von vier ungünstigen Bedingungen zusammen.
  (`multiple_disadvantage`, `cases_multiple_conditions.csv`)

## Offene Hypothesen

- Ob Hauptstraßen mit hoher Verkehrsmenge stärker trennen als die Straßenklasse vermuten lässt (DTVw 2023 und
  Tempolimits liegen vor, sind aber nicht ausgewertet).
- Ob einzelne neue Querungen oder Durchwegungen ähnlich viel bewirken wie neue Standorte.
- Wie sich die Schulwege entlang der Einschulbereiche von den Wegen zur nächsten Grundschule unterscheiden.
- Warum in Gewerbegebieten Kinder wohnen; die Daten geben darüber keine Auskunft.
- Wie viele Spielplätze tatsächlich barrierefrei sind; dazu gibt es keine amtlichen Daten.

Korrektur während der Umsetzung: Im Schulhof-Szenario wurden zunächst zu viele Haushalte als bereits erreicht
gestrichen (alle bis 1.500 m statt bis 400 m). Der Fehler fiel beim Schreiben der Tests auf; die Werte oben sind
die korrigierten. Ein Regressionstest sichert das ab.
