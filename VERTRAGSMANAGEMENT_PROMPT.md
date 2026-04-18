# Claude Code Prompt – Vertragsmanagement-Demo Workflow

Kopiere alles ab der Trennlinie und füge es in Claude Code ein.

---

Ich baue einen AI-Automatisierungs-Demo-Workflow für Vertragsmanagement.
Ziel ist es, eine Vertrags-PDF einzulesen und automatisch eine strukturierte
Analyse zu erzeugen (Parteien, Fristen, Pflichten, Risiken).

Das Projekt folgt dem WAT-Framework: Workflows (Markdown-SOPs) → Agent (du,
Claude Code) → Tools (Python-Scripts). Jede Schicht hat eine klare Aufgabe.

Führe jetzt folgende Schritte der Reihe nach aus und erkläre jeden kurz:

---

## Schritt 1: Projektstruktur anlegen

Erstelle folgende Ordner im aktuellen Verzeichnis, falls nicht vorhanden:
- workflows/
- tools/
- .tmp/

---

## Schritt 2: Workflow-SOP erstellen

Erstelle die Datei `workflows/vertragsmanagement_workflow.md` mit exakt
diesem Inhalt:

```
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
```

---

## Schritt 3: Python-Tool erstellen

Erstelle die Datei `tools/vertragsanalyse.py` mit folgendem Inhalt:

```python
#!/usr/bin/env python3
"""
Vertragsanalyse Tool – Extrahiert Text aus einer Vertrags-PDF und
erstellt eine strukturierte Analyse-Template-Datei.

Usage:
    python tools/vertragsanalyse.py vertrag.pdf
    python tools/vertragsanalyse.py pfad/zu/vertrag.pdf
"""

import sys
import os
import re
from datetime import datetime


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrahiert den vollständigen Text aus einer PDF-Datei."""
    try:
        import pdfplumber
    except ImportError:
        print("pdfplumber nicht installiert. Installiere mit:")
        print("  pip install pdfplumber")
        sys.exit(1)

    text_parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"PDF geladen: {total_pages} Seiten")
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    text_parts.append(f"[Seite {i}]\n{text}")
                else:
                    text_parts.append(f"[Seite {i} – kein Text extrahierbar]")
    except Exception as e:
        print(f"Fehler beim Lesen der PDF: {e}")
        sys.exit(1)

    return "\n\n".join(text_parts)


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "_", text.strip())
    return text[:50]


def create_analysis_template(pdf_name: str, rohtext: str) -> str:
    datum = datetime.now().strftime("%Y-%m-%d")
    return f"""# Vertragsanalyse: {pdf_name}

**Analysedatum:** {datum}
**Analysiert mit:** Vertragsmanagement-Workflow v1.0
**Status:** In Bearbeitung

---

## 1. Vertragsparteien

- **Partei A:**
- **Partei B:**

---

## 2. Vertragstyp & Gegenstand

- **Vertragstyp (BGB-Systematik):**
- **Leistungsgegenstand:**
- **Vergütung / Vertragswert:**

---

## 3. Laufzeit & Fristen

- **Vertragsbeginn:**
- **Vertragsende / Laufzeit:**
- **Ordentliche Kündigungsfrist:**
- **Außerordentliche Kündigung:**
- **Weitere Fristen:**

---

## 4. Kernpflichten

### Pflichten Partei A:


### Pflichten Partei B:


### Relevante Nebenpflichten:


---

## 5. Rechtliche Risiken & Auffälligkeiten


---

## 6. Handlungsempfehlungen

**Muss (vor Unterzeichnung):**

**Sollte (empfohlen):**

**Kann (optional):**

---

## 7. Rohtext (Quelle)

```
{rohtext[:3000]}{"..." if len(rohtext) > 3000 else ""}
```

*Vollständiger Rohtext: {len(rohtext)} Zeichen, {rohtext.count(chr(10))} Zeilen*
"""


def main():
    if len(sys.argv) < 2:
        print("Fehler: Kein PDF-Pfad angegeben.")
        print("Verwendung: python tools/vertragsanalyse.py vertrag.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"Fehler: Datei nicht gefunden: {pdf_path}")
        sys.exit(1)

    print(f"Verarbeite: {pdf_path}")
    rohtext = extract_text_from_pdf(pdf_path)

    os.makedirs(".tmp", exist_ok=True)

    datum = datetime.now().strftime("%Y%m%d")
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    slug = slugify(pdf_name)
    output_path = f".tmp/vertragsanalyse_{slug}_{datum}.md"

    template = create_analysis_template(pdf_name, rohtext)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(template)

    print(f"Datei erstellt: {output_path}")
    print(f"Extrahierter Text: {len(rohtext)} Zeichen")
    print(f"\nNaechster Schritt:")
    print(f"  Lies {output_path} und befuelle alle Abschnitte")
    print(f"  gemaess workflows/vertragsmanagement_workflow.md")

    return output_path


if __name__ == "__main__":
    main()
```

---

## Schritt 4: Abhängigkeit installieren

Führe folgenden Befehl im Terminal aus:
```
pip install pdfplumber
```

Bestätige mir wenn die Installation erfolgreich war.

---

## Schritt 5: Test-Vertrag erstellen und Workflow testen

Da wir möglicherweise keine echte Vertrags-PDF zur Hand haben, erstelle
zunächst eine Test-PDF. Schreibe dafür das Script `tools/create_test_pdf.py`:

```python
#!/usr/bin/env python3
"""Erstellt einen minimalen Test-Vertrag als PDF für den Workflow-Test."""

def create_test_pdf():
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
    except ImportError:
        print("reportlab nicht installiert. Installiere mit: pip install reportlab")
        import sys
        sys.exit(1)

    import os
    os.makedirs(".tmp", exist_ok=True)
    output = ".tmp/test_vertrag.pdf"

    c = canvas.Canvas(output, pagesize=A4)
    width, height = A4

    lines = [
        "DIENSTLEISTUNGSVERTRAG",
        "",
        "zwischen",
        "",
        "Mustermann GmbH, Leopoldstrasse 10, 80802 München",
        "(nachfolgend: Auftraggeber)",
        "",
        "und",
        "",
        "TechService UG, Maximilianstrasse 5, 80539 München",
        "(nachfolgend: Auftragnehmer)",
        "",
        "§ 1 Gegenstand",
        "Der Auftragnehmer erbringt IT-Beratungsleistungen im Bereich",
        "Datenschutz und DSGVO-Compliance.",
        "",
        "§ 2 Vergütung",
        "Die monatliche Vergütung beträgt 2.500 EUR netto.",
        "Zahlung innerhalb von 14 Tagen nach Rechnungsstellung.",
        "",
        "§ 3 Laufzeit und Kündigung",
        "Der Vertrag beginnt am 01.05.2026 und läuft auf unbestimmte Zeit.",
        "Ordentliche Kündigung mit 3 Monaten Frist zum Monatsende.",
        "Außerordentliche Kündigung bei schwerwiegenden Vertragsverletzungen.",
        "",
        "§ 4 Geheimhaltung",
        "Der Auftragnehmer verpflichtet sich zur Verschwiegenheit über alle",
        "betrieblichen Informationen auch nach Vertragsende.",
        "",
        "§ 5 Haftung",
        "Die Haftung des Auftragnehmers ist auf Vorsatz und grobe Fahrlässigkeit",
        "beschränkt. Die maximale Haftungssumme beträgt 10.000 EUR.",
        "",
        "§ 6 Schlussbestimmungen",
        "Gerichtsstand ist München. Es gilt deutsches Recht.",
        "Änderungen bedürfen der Schriftform.",
        "",
        "München, den 15.04.2026",
        "",
        "____________________          ____________________",
        "Mustermann GmbH               TechService UG",
    ]

    y = height - 60
    c.setFont("Helvetica-Bold", 14)
    c.drawString(180, y, lines[0])
    c.setFont("Helvetica", 11)
    y -= 30

    for line in lines[1:]:
        if y < 60:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - 60
        if line.startswith("§"):
            c.setFont("Helvetica-Bold", 11)
        else:
            c.setFont("Helvetica", 11)
        c.drawString(60, y, line)
        y -= 18

    c.save()
    print(f"Test-PDF erstellt: {output}")
    return output

if __name__ == "__main__":
    create_test_pdf()
```

Installiere reportlab und führe das Script aus:
```
pip install reportlab
python tools/create_test_pdf.py
```

Führe dann den vollständigen Workflow-Test durch:
```
python tools/vertragsanalyse.py .tmp/test_vertrag.pdf
```

Öffne die erstellte Analyse-Datei in .tmp/ und befülle alle 6 Abschnitte
vollständig gemäß `workflows/vertragsmanagement_workflow.md`.

---

## Schritt 6: Ergebnis zeigen

Zeige mir am Ende:
1. Die fertige Ordnerstruktur (alle erstellten Dateien)
2. Den vollständig befüllten Inhalt der Vertragsanalyse-Datei
3. Eine kurze Erklärung: Wie nutze ich diesen Workflow mit einer echten PDF?
