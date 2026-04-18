# Workflow: Vertragsmanagement-Analyse

## Zweck
Automatische Erstanalyse eines Vertrags-PDFs. Output ist eine strukturierte
Markdown-Datei mit allen vertragsrelevanten Informationen, die ein Anwalt
oder Unternehmer sofort nutzen kann.

## Inputs
- `pdf_pfad`: Pfad zur Vertrags-PDF-Datei
  Beispiel: python tools/vertragsanalyse.py vertrag.pdf

## Schritt-für-Schritt-Ausführung

### Schritt 1: Vollautomatische KI-Analyse (Standard, empfohlen)

```bash
python tools/vertragsanalyse.py [PDF-PFAD]
```

→ Extrahiert Text aus der PDF
→ Erkennt Fristen automatisch per Regex
→ Sendet Vertragstext an Claude API (Haiku 4.5)
→ Gibt fertig befüllte Analyse zurück (~$0.02 pro Vertrag)
→ Speichert Ergebnis in .tmp/

Modell wechseln (für komplexe Verträge):
```bash
python tools/vertragsanalyse.py vertrag.pdf --modell claude-sonnet-4-6
```

Ohne API (nur Template erstellen):
```bash
python tools/vertragsanalyse.py vertrag.pdf --no-ki
```

### Schritt 2: Qualitäts-Check der KI-Analyse

Die KI liefert eine vollständige Erstanalyse. Prüfe:
- [ ] Fristen korrekt erkannt und kontextuell richtig eingeordnet?
- [ ] Risiken (Abschnitt 5) konkret und mit Paragrafenangabe?
- [ ] Handlungsempfehlungen umsetzbar und priorisiert?
- [ ] Status ist bereits auf "Abgeschlossen" gesetzt

Bei Bedarf: Abschnitte manuell korrigieren oder ergänzen.

## Expected Output
Datei: .tmp/vertragsanalyse_[dateiname]_[YYYYMMDD_HHMMSS].md
Status nach KI-Analyse: "Abgeschlossen" (direkt verwertbar)

## Edge Cases
- Schlecht lesbares PDF (Scan): Qualität im Output vermerken
- Sehr langer Vertrag (>20 Seiten): nur Seiten 1–10 analysieren, Rest vermerken
- Fremdsprachiger Vertrag: Sprache vermerken, trotzdem analysieren
- Kein Text extrahierbar: Fehlermeldung ausgeben, manuellen Input anbieten

---

## Batch-Modus (mehrere PDFs auf einmal)

### Verwendung
```bash
# Nur Text extrahieren + leeres Template (schnell, kostenlos)
python tools/batch_vertragsanalyse.py ./ordner/mit/pdfs/

# Mit KI-Analyse (alle PDFs automatisch vollständig analysiert)
python tools/batch_vertragsanalyse.py ./ordner/mit/pdfs/ --ki

# Rekursiv + KI + Sonnet
python tools/batch_vertragsanalyse.py ./ordner/ --recursive --ki --modell claude-sonnet-4-6
```

### Verhalten
- Verarbeitet alle .pdf-Dateien im angegebenen Ordner
- Überspringt Dateien die keine PDFs sind (mit Hinweis)
- Bricht bei einem fehlerhaften PDF NICHT ab – dokumentiert den
  Fehler und macht mit der nächsten Datei weiter
- Zeigt Fortschritt: "Verarbeite 2/5: lieferantenvertrag.pdf"
- Gibt am Ende eine Zusammenfassung aus

### Expected Output
- Eine .md-Analyse-Datei pro PDF in .tmp/
- Eine Zusammenfassungsdatei: .tmp/batch_zusammenfassung_[datum].md

### Status-Workflow
- Jede Analyse-Datei startet mit `**Status:** In Bearbeitung`
- Nach manuellem Befüllen aller Abschnitte (Schritte 2–3 des Einzel-Workflows) auf `**Status:** Abgeschlossen` setzen
- Dateien mit Status "In Bearbeitung" sind Rohtexte, noch keine fertigen Analysen

---

## Fristen-Extraktion (automatisch, kein AI nötig)

### Verwendung
python tools/fristen_extraktor.py vertrag.pdf
python tools/fristen_extraktor.py ./vertraege/     ← ganzer Ordner

### Was erkannt wird
- Absolute Daten: 01.05.2026, 1. Juli 2026, Mai 2026
- Relative Fristen: 3 Monate, 30 Tage, 2 Wochen, 6 Monate
- Zahlungsfristen: binnen 14 Tagen, zahlbar monatlich
- Kündigungsfristen: Kündigung mit ... Frist

### Expected Output
- Konsolen-Ausgabe mit allen gefundenen Fristen und Kontext
- .tmp/fristen_[dateiname]_[datum].md mit strukturierter Fristenliste

---

## Stufe 3: Vertrags-Datenbank (CSV)

### Zweck
Konsolidiert alle Analyse-Dateien aus .tmp/ in ein maschinenlesbares
CSV-Register. Ermöglicht Suche, Filterung und Weiterverarbeitung
(z. B. Google Sheets, Excel, BI-Tools).

### Verwendung
python tools/vertrags_datenbank.py              # Alle .tmp/*.md einlesen
python tools/vertrags_datenbank.py --preview    # Nur Vorschau, kein Schreiben
python tools/vertrags_datenbank.py --output pfad/zur/datenbank.csv

### CSV-Spalten
| Spalte              | Quelle                          |
|---------------------|---------------------------------|
| id                  | Auto (laufende Nummer)          |
| quelldatei          | Dateiname der .md-Quelldatei    |
| analysedatum        | Header-Feld "Analysedatum"      |
| status              | Header-Feld "Status"            |
| partei_a            | Abschnitt 1 – Partei A          |
| partei_b            | Abschnitt 1 – Partei B          |
| vertragstyp         | Abschnitt 2 – Vertragstyp       |
| leistungsgegenstand | Abschnitt 2 – Leistungsgegenstand |
| verguetung          | Abschnitt 2 – Vergütung         |
| vertragsbeginn      | Abschnitt 3 – Vertragsbeginn    |
| vertragsende        | Abschnitt 3 – Vertragsende      |
| kuendigungsfrist    | Abschnitt 3 – Kündigungsfrist   |
| risiko_notiz        | Abschnitt 5 – erste Zeile       |
| letzte_aktualisierung | Zeitstempel des Durchlaufs    |

### Expected Output
output/vertrags_datenbank.csv (persistent – wird bei jedem Lauf aktualisiert, nie löschen)

### Edge Cases
- Abschnitt nicht befüllt ("In Bearbeitung"): Feld bleibt leer, kein Fehler
- Duplikate (gleicher Quelldateiname): neueste Version überschreibt
- Leere .tmp/: Leere CSV mit nur Header-Zeile wird erstellt
