# Kindheit in Berlin – Leitlinien für die Weiterentwicklung

Beitrag zum Berliner Open-Data-Ideenwettbewerb 2026/2027 (Einsendeschluss 15.01.2027). Die Anwendung zeigt, wie weit
es für Berliner Kinder zu Fuß zu Spielplatz, Kita, Schule und Jugendclub ist, und wo zusätzliche Angebote viele
Kinder erreichen würden. Leitidee: Wege statt Kreise.

## Befehle

```bash
npm run dev            # Entwicklungsserver
npm run type-check && npm run lint && npm test   # vor jedem Commit
npm run build && npm run test:e2e                # End-to-End und Barrierefreiheit (braucht den Build)
.venv/bin/python -m pytest tests/pipeline -q     # Rechenverfahren
```

Datenpipeline in dieser Reihenfolge: `pipeline.download`, `pipeline.walk_network`, `pipeline.osm_features`,
`analysis.01_home_accessibility`, `analysis.02_planning_area_indicators`, `analysis.03_findings`,
`pipeline.export_frontend`, `analysis.04_figures` (jeweils `.venv/bin/python -m …`).

## Umgang mit Daten

- **Keine Zahl von Hand.** Jede veröffentlichte Zahl kommt aus `data/processed/findings.json` oder `public/data/`.
  Texte der Anwendung lesen die Werte aus den Daten; Dokumente nennen den Schlüssel.
- **Keine erfundenen oder Platzhalterdaten** in `public/data`.
- Neue Quelle: zuerst in `pipeline/sources.py` eintragen (Titel, Lizenz, Datenstand, Adresse). Daraus entstehen
  Download, `docs/DATA_SOURCES.md` und die Quellentabelle der Anwendung.
- Fehlende Werte bleiben `null` und werden als „keine Angabe“ gezeigt, nie als 0.
- Anteile und Mittelwerte nur für Planungsräume mit mindestens 100 Kindern.
- Ändern sich Kernzahlen: `tests/unit/data.test.ts`, `docs/FINDINGS.md` und `docs/ANALYSIS_REPORT.md` anpassen.
- Rechnen in EPSG:25833; WGS84 erst beim Export.

## Inhaltliche Leitplanken

- Keine Rangliste „guter“ und „schlechter“ Quartiere, kein zusammengesetzter Index.
- Sozialdaten sind Kontext für Gebiete, nie Aussagen über Menschen. Keine Zuschreibungen.
- Korrelation nicht als Ursache formulieren. Unfälle sind beobachtete Ereignisse, keine Risikovorhersage.
- Szenarien sind Modellrechnungen: immer als hypothetisch kennzeichnen, keine Kosten erfinden.
- Die Lücke des amtlichen Spielplatzbestands (Wohnanlagen) bei jeder Versorgungsaussage mitdenken.
- Automatische Aussagen nur über Regeln in `src/domain/insights.ts`, mit Schwelle und Zahlen im Text.

## Code

- Vue 3 mit `<script setup lang="ts">`, TypeScript strict, kein `any`. Bezeichner und Kommentare auf Englisch,
  Texte der Oberfläche auf Deutsch.
- Fachlogik gehört nach `src/domain` (ohne Vue, mit Tests), nicht in Komponenten oder Templates.
- Kennzahlen nur in `src/domain/indicators.ts` definieren. Zahlen nur über `src/domain/format.ts` formatieren.
- Farben, Abstände und Schriftgrößen nur über die Tokens in `src/styles/tokens.css`.
- Keine Magic Numbers: benannte Konstanten mit Begründung.
- Ansichtszustand gehört in die URL (`useQueryParam`), nicht in einen Store.
- Neue Abhängigkeiten nur mit konkretem Bedarf. Keine Dienste, die Schlüssel, Registrierung oder Anfragen an
  Dritte im Betrieb erfordern.
- Kommentare erklären Entscheidungen und fachliche Annahmen, nicht das Offensichtliche.

## Barrierefreiheit (WCAG 2.2 AA)

- Jede Karte und jedes Diagramm braucht eine Tabelle oder Liste mit denselben Werten.
- Nichts nur über Farbe oder nur per Hover vermitteln. Sichtbarer Fokus, vollständige Tastaturbedienung.
- Neue Seiten in `tests/e2e/accessibility.spec.ts` aufnehmen.

## Dokumentation

`docs/METHODOLOGY.md` (Rechenwege), `docs/FINDINGS.md` (Erkenntnisse), `docs/DATA_QUALITY.md` (Feedback),
`docs/ARCHITECTURE.md` (Entscheidungen), `docs/COMPETITION.md` (Anforderungen und Checkliste),
`docs/AI_USAGE.md` (KI-Offenlegung). `docs/DATA_SOURCES.md` wird erzeugt und nicht von Hand geändert.
