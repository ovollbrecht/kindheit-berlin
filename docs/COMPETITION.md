# Wettbewerb: Anforderungen und Einreichungs-Checkliste

Berliner Open-Data-Ideenwettbewerb 2026/2027 · geprüft am 24.11.2026 anhand von

- Ausschreibung und Teilnahmebedingungen (Ziffern 1–15, auf der Seite selbst, kein separates PDF):
  <https://www.berlin.de/moderne-verwaltung/e-government/open-data-wettbewerb-1730431.php>
- Einreichungsformular (DOCX, auf derselben Seite verlinkt)

Vor der Einreichung beide Quellen erneut prüfen; Änderungen werden laut Ziffer 15 auf mein.berlin.de bekanntgegeben.

## Termine

| Termin | Datum |
|---|---|
| Einreichung offen seit | 02.11.2026 |
| Offene Sprechstunde | 09.12.2026 |
| **Einsendeschluss** | **15.01.2027, 23:59 Uhr (Eingang der E-Mail)** |
| Jurysitzung | 15.02.2027 |
| Ergebnisse | bis 22.02.2027 |
| Preisverleihung, Berlin Open Data Day | 26.05.2027 |

Preise: 750 €, 450 €, 300 €. Rückfragen: opendata@senatskanzlei.berlin.de (Antwort binnen drei Werktagen).

## Teilnahme

- Einzelpersonen, Teams, Gruppen und Organisationen ab 16 Jahren; höchstens zwei Beiträge.
- Ausgeschlossen: Beschäftigte der Senatskanzlei, von ODIS und BerlinOnline, Jurymitglieder und Angehörige.
- Der Beitrag darf nicht vor dem in Ziffer 3.4 genannten Datum entstanden sein (dort „[01.10.2026]“ in
  eckigen Klammern). Projektbeginn hier: 24.11.2026.

## Formale Anforderungen und Stand im Projekt

| Anforderung (Ziffer) | Umsetzung | Stand |
|---|---|---|
| Mindestens ein Datensatz von daten.berlin.de, alle mit Link (3.1) | 12 Datensätze des Portals; Liste mit Links in `docs/DATA_SOURCES.md` | erfüllt |
| Weitere Quellen benannt und rechtlich nutzbar (3.1) | OSM (ODbL), Unfallatlas (dl-de/by-2.0); in der Fußzeile und unter „Daten und Methodik“ genannt | erfüllt |
| Beitrag als öffentlicher Link, zum Einsendeschluss erreichbar (3.2, 3.4) | GitHub Pages; Workflow `.github/workflows/ci.yml` vorhanden | offen: Repository anlegen und veröffentlichen |
| Kurzbeschreibung höchstens 1.500 Zeichen inkl. Leerzeichen (3.2) | – | offen |
| Methodik und Werkzeuge beschrieben, Skripte verlinkt (3.2) | `docs/METHODOLOGY.md`, Seite „Daten und Methodik“ | erfüllt; Kurzfassung für das Formular offen |
| Sprache Deutsch oder Englisch (3.3) | Deutsch | erfüllt |
| Inhalte unter CC BY 4.0, CC BY-SA 4.0 oder CC0 (4.1) | CC BY 4.0, `LICENSE-CONTENT.md` | erfüllt |
| Quellcode öffentlich, OSI-Lizenz (4.2) | MIT, `LICENSE` | offen: Repository öffentlich machen, Adresse in `src/config.ts` eintragen |
| Fremde Inhalte lizenzkonform und gekennzeichnet, Namensnennung (5.1) | `THIRD_PARTY_NOTICES.md`, Quellenzeile an jeder Grafik, Quellentabelle | erfüllt |
| KI-Einsatz offengelegt: Werkzeug und Zweck (6) | `docs/AI_USAGE.md`, Hinweis unter „Daten und Methodik“ | erfüllt; menschliche Prüfungen dort abhaken |
| Barrierearm: Alternativtexte, Kontraste, Tastatur, nicht nur Farbe (7, Bitte) | WCAG 2.2 AA als Ziel; axe-core-Prüfung aller Seiten ohne Befund | automatisch geprüft; manuelle Prüfung mit Screenreader offen |
| Datensatz-Feedback (8, Pflicht) | `docs/DATA_QUALITY.md`, gegliedert wie das Formular | Material vorhanden |
| Keine personenbezogenen Daten Dritter, nichts Diskriminierendes oder Werbliches (11) | nur aggregierte amtliche Daten, keine Quartiers-Rankings | erfüllt, bei Texten weiter beachten |

Rechteeinräumung (5.2): Das Land Berlin erhält ein einfaches, unbefristetes Nutzungsrecht für
Öffentlichkeitsarbeit mit Namensnennung. Wertungsfähige Beiträge werden mit Zustimmung unter
daten.berlin.de/anwendungen veröffentlicht (10).

## Bewertungskriterien und Projektbezug

Die Jury vergibt je Kriterium 0 bis 5 Punkte.

| Kriterium | Gewicht | Womit das Projekt punkten soll |
|---|---|---|
| Erkenntnisgewinn und Relevanz für Berlin | 25 % | Fünf belegte Erkenntnisse, zwei davon gegen die Erwartung; Bezug zur amtlichen Spielplatzversorgung |
| Datennutzung und Nachvollziehbarkeit | 20 % | 12 Portal-Datensätze verknüpft, jede Zahl aus `findings.json`, vollständige Pipeline, 66 automatische Tests |
| Kreativität und Originalität | 20 % | Gebäudegenaue Fußwege statt Radien, Hauptstraßenquerungen, Szenarien ohne Doppelzählung |
| Verständlichkeit, Gestaltung, Zugänglichkeit | 20 % | Geführte Story, Tabelle neben jeder Karte, WCAG 2.2 AA |
| Technische Umsetzung und Nachnutzbarkeit | 15 % | Statische Anwendung, MIT, dokumentierte Datenartefakte zum Download |

## Felder des Einreichungsformulars

Pflichtfelder mit *. Formular je Beitrag als Word- oder PDF-Datei speichern.

| Abschnitt | Feld | Inhalt |
|---|---|---|
| a | Titel des Beitrags * | offen |
| a | Art des Beitrags * (Auswahl) | Web-Anwendung |
| a | Sprache * (Auswahl) | Deutsch |
| a | Link zum Beitrag (Pflicht ohne Anhang) | URL GitHub Pages |
| b | Kurzbeschreibung * (max. 1.500 Zeichen): Was zeigt der Beitrag, welche Frage, für wen? | offen |
| c | Verwendete Datensätze *: Name und Link je Zeile | aus `pipeline/sources.py` |
| c | Weitere Datenquellen mit Link und Lizenz | OSM, Unfallatlas, AfS-Bericht |
| d | Methodik und eingesetzte Werkzeuge * | offen |
| d | Einsatz generativer KI * (Ja/Nein), Werkzeug und Zweck | Ja; Claude Code (Anthropic) für Recherche, Datenanalyse, Code, Texte |
| d | Lizenz der Inhalte * (Auswahl) | CC BY 4.0 |
| e | Link zum öffentlichen Quellcode | GitHub-Repository |
| e | Softwarelizenz (Auswahl) | MIT |
| f | Qualität der Datensätze * | aus `docs/DATA_QUALITY.md` |
| f | Fehlende Daten | Spielplätze der Wohnungsunternehmen, Barrierefreiheit, Kita-Belegung, Unfallkoordinaten mit Alter |
| f | Wünsche und Anregungen | sprechende Attributnamen, funktionierende CSV-Links, Altersgruppen vor 2022 |
| g | Einreichung als *, Name, E-Mail *, Telefon, Name für die Veröffentlichung * | trägt der Einreichende ein |
| – | Sieben Erklärungen zum Ankreuzen (sechs davon Pflicht) | trägt der Einreichende ein |

## Checkliste für die Einreichung

- [ ] Ausschreibung und Formular erneut auf Änderungen geprüft
- [ ] Anwendung unter der öffentlichen URL erreichbar, auch im Repository-Unterpfad
- [ ] Repository öffentlich, `LICENSE` (MIT) und `LICENSE-CONTENT.md` (CC BY 4.0) vorhanden
- [ ] Quellen und Namensnennungen in der Anwendung sichtbar (AfS: CC BY 3.0 DE; OSM: „© OpenStreetMap-Mitwirkende“, ODbL; Unfallatlas: dl-de/by-2.0; Polizei Berlin: CC BY 4.0)
- [ ] Kurzbeschreibung gezählt: höchstens 1.500 Zeichen inklusive Leerzeichen
- [ ] Datensatzliste mit funktionierenden Links
- [ ] Methodenbeschreibung mit Link auf die Skripte
- [ ] KI-Offenlegung ausgefüllt
- [ ] Feedbackfelder ausgefüllt
- [ ] Kontaktdaten und Erklärungen ausgefüllt
- [ ] Formular als Word oder PDF gespeichert, z. B. `Ideenwettbewerb_Titel-des-Beitrags`
- [ ] E-Mail an opendata@senatskanzlei.berlin.de, Betreff „Ideenwettbewerb – [Titel des Beitrags]“, Anhänge unter 10 MB
- [ ] Eingang vor dem 15.01.2027, 23:59 Uhr

Die Einreichung nimmt der Einreichende selbst vor.
