# Einsatz generativer KI

Offenlegung nach Ziffer 6 der Teilnahmebedingungen des Berliner Open-Data-Ideenwettbewerbs.

## Eingesetztes Werkzeug

**Claude Code (Anthropic), Modell Claude Fable 5.2**, als Programmierassistent mit Zugriff auf das Projektverzeichnis,
eine Kommandozeile und einen Browser. Begonnen am 24.11.2026.

## Wofür es eingesetzt wurde

| Bereich | Einsatz |
|---|---|
| Recherche | Lesen der Ausschreibung und des Formulars, Suche nach Datensätzen im Berliner Datenregister, Sichtung bestehender Angebote |
| Datenaufbereitung | Entwurf und Programmierung der Python-Skripte in `pipeline/` und `analysis/` |
| Analyse | Formulierung und Prüfung der Hypothesen, Auswahl der Kennzahlen und Verfahren |
| Webanwendung | Konzept, Gestaltung und Programmierung (Vue, TypeScript), Tests |
| Texte | Texte der Anwendung, Dokumentation, Analysebericht |
| Grafiken | Diagramme und Karten werden vom Code aus den Daten erzeugt, nicht von einem Bildgenerator |

## Wofür es nicht eingesetzt wird

- **Keine Zahl in der Anwendung stammt aus einem Sprachmodell.** Alle Werte werden von den veröffentlichten
  Skripten aus den Quelldaten berechnet und liegen in `data/processed/findings.json` und `public/data/`.
- Die Hinweise im Quartiersprofil entstehen aus festen, dokumentierten Regeln (`src/domain/insights.ts`), nicht
  durch Textgenerierung zur Laufzeit.
- Die Anwendung ruft im Betrieb keinen KI-Dienst auf.

## Prüfungen

Maschinell abgesichert:

- Abgleich mit unabhängigen Angaben: Einwohnersumme, amtlicher Versorgungsgrad mit Spielfläche (rund 60 %),
  Kinderarmutsquote des Monitorings Soziale Stadtentwicklung, jährliche Zahl der Unfälle mit Personenschaden.
- Automatisierte Tests der Rechenverfahren, der Datenkonsistenz, der wichtigsten Nutzungswege und der
  Barrierefreiheit (siehe `README.md`).
- Ein Fehler im Schulhof-Szenario wurde durch die Tests gefunden und korrigiert (siehe `docs/FINDINGS.md`).

**Vom Einreichenden vor der Einreichung zu prüfen und hier zu bestätigen:**

- [ ] Stichproben bekannter Quartiere und Einrichtungen gegen eigene Ortskenntnis oder Kartendienste
- [ ] Texte der Startseite auf Verständlichkeit und Tonfall
- [ ] Lizenz- und Quellenangaben
- [ ] Bedienung mit Tastatur und Screenreader

Die Verantwortung für Richtigkeit und Rechte liegt beim Einreichenden.
