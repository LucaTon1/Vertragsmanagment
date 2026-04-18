# Workflow: Vertragsmanagement-Analyse

## Zweck
Automatische Erstanalyse eines Vertrags-PDFs. Output ist eine strukturierte
Markdown-Datei mit allen vertragsrelevanten Informationen, die ein Anwalt
oder Unternehmer sofort nutzen kann.

## Inputs
- `pdf_pfad`: Pfad zur Vertrags-PDF-Datei
  Beispiel: python tools/vertragsanalyse.py vertrag.pdf

## Schritt-für-Schritt-Ausführung

### Schritt 1: Text extrahieren
python tools/vertragsanalyse.py [PDF-PFAD]
→ Extrahiert den Volltext aus der PDF
→ Erstellt Template-Datei in .tmp/ mit dem Rohtext

### Schritt 2: Analyse befüllen (Claude Code führt dies aus)
Lies die erstellte Datei und befülle jeden Abschnitt präzise:

Abschnitt 1 – Vertragsparteien
- Vollständige Namen beider Parteien mit Rollen (wer ist Auftraggeber?)
- Adressen falls angegeben

Abschnitt 2 – Vertragstyp & Gegenstand
- Vertragstyp nach BGB-Systematik bestimmen
- Konkreter Leistungsgegenstand in 2–3 Sätzen

Abschnitt 3 – Laufzeit & Fristen (KRITISCH)
- Vertragsbeginn und -ende mit Datum
- Kündigungsfristen exakt aus dem Text
- Alle weiteren Fristen (Gewährleistung, Zahlungsziele, Optionen)

Abschnitt 4 – Kernpflichten
- Hauptleistungspflichten beider Parteien
- Nebenpflichten die relevant sind (Geheimhaltung, Wettbewerbsverbot etc.)

Abschnitt 5 – Rechtliche Risiken & Auffälligkeiten
- Klauseln die AGB-rechtlich problematisch sein könnten (§ 307 BGB)
- Fehlende Regelungen die üblicherweise enthalten sein sollten
- Unklare oder widersprüchliche Formulierungen

Abschnitt 6 – Handlungsempfehlungen
- Konkrete Liste: Was sollte vor Unterzeichnung geklärt oder geändert werden?
- Priorisiert nach Dringlichkeit (muss / sollte / kann)

### Schritt 3: Qualitäts-Check
- [ ] Alle Fristen sind mit exakten Daten/Zeiträumen belegt
- [ ] Risiken sind konkret (nicht generisch "könnte problematisch sein")
- [ ] Handlungsempfehlungen sind umsetzbar
- [ ] Status auf "Abgeschlossen" setzen

## Expected Output
Datei: .tmp/vertragsanalyse_[dateiname]_[YYYYMMDD].md

## Edge Cases
- Schlecht lesbares PDF (Scan): Qualität im Output vermerken
- Sehr langer Vertrag (>20 Seiten): nur Seiten 1–10 analysieren, Rest vermerken
- Fremdsprachiger Vertrag: Sprache vermerken, trotzdem analysieren
- Kein Text extrahierbar: Fehlermeldung ausgeben, manuellen Input anbieten
