# Claude Code Prompt – Stufe 1: Batch-Verarbeitung

Kopiere alles ab der Trennlinie und füge es in Claude Code ein.

---

Ich erweitere meinen bestehenden Vertragsmanagement-Workflow um
Batch-Verarbeitung. Das Projekt folgt dem WAT-Framework und liegt
bereits mit dieser Struktur vor:

```
workflows/
  vertragsmanagement_workflow.md
tools/
  vertragsanalyse.py        ← existiert bereits
  create_test_pdf.py        ← existiert bereits
.tmp/
```

Führe folgende Schritte der Reihe nach aus und erkläre jeden kurz:

---

## Schritt 1: Workflow-SOP erweitern

Ergänze die Datei `workflows/vertragsmanagement_workflow.md` am Ende
um einen neuen Abschnitt mit folgendem Inhalt:

```
---

## Batch-Modus (mehrere PDFs auf einmal)

### Verwendung
python tools/batch_vertragsanalyse.py ./ordner/mit/pdfs/

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
```

---

## Schritt 2: Batch-Tool erstellen

Erstelle die Datei `tools/batch_vertragsanalyse.py`:

```python
#!/usr/bin/env python3
"""
Batch-Vertragsanalyse Tool – Verarbeitet alle PDFs in einem Ordner.

Usage:
    python tools/batch_vertragsanalyse.py ./vertraege/
    python tools/batch_vertragsanalyse.py .          (aktueller Ordner)

Was dieses Script macht:
    1. Findet alle .pdf-Dateien im angegebenen Ordner
    2. Extrahiert aus jeder PDF den Text mit pdfplumber
    3. Erstellt pro PDF eine strukturierte Analyse-Datei in .tmp/
    4. Überspringt fehlerhafte PDFs ohne abzubrechen
    5. Erstellt eine Zusammenfassung aller verarbeiteten Dateien
"""

import sys
import os
import re
from datetime import datetime
from pathlib import Path


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "_", text.strip())
    return text[:50]


def extract_text_from_pdf(pdf_path: str) -> tuple[str, int]:
    """
    Extrahiert Text aus PDF.
    Gibt (text, seitenanzahl) zurück.
    Wirft Exception bei Fehler.
    """
    import pdfplumber
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text and text.strip():
                text_parts.append(f"[Seite {i}]\n{text}")
            else:
                text_parts.append(f"[Seite {i} – kein Text extrahierbar]")
    return "\n\n".join(text_parts), total_pages


def create_analysis_template(pdf_name: str, rohtext: str, seiten: int) -> str:
    datum = datetime.now().strftime("%Y-%m-%d")
    vorschau = rohtext[:3000]
    if len(rohtext) > 3000:
        vorschau += "\n\n[... gekürzt für Übersicht ...]"
    return f"""# Vertragsanalyse: {pdf_name}

**Analysedatum:** {datum}
**Seiten:** {seiten}
**Analysiert mit:** Vertragsmanagement-Workflow v1.0 (Batch)
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
{vorschau}
```

*Vollständiger Rohtext: {len(rohtext)} Zeichen | {rohtext.count(chr(10))} Zeilen*
"""


def verarbeite_pdf(pdf_path: Path, output_dir: Path, index: int, total: int) -> dict:
    """
    Verarbeitet eine einzelne PDF.
    Gibt ein Ergebnis-Dict zurück: {datei, status, output_pfad, fehler, seiten}
    """
    print(f"\n  [{index}/{total}] {pdf_path.name}")

    ergebnis = {
        "datei": pdf_path.name,
        "status": None,
        "output_pfad": None,
        "fehler": None,
        "seiten": 0,
        "zeichen": 0,
    }

    try:
        rohtext, seiten = extract_text_from_pdf(str(pdf_path))
        ergebnis["seiten"] = seiten
        ergebnis["zeichen"] = len(rohtext)

        datum = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = slugify(pdf_path.stem)
        output_pfad = output_dir / f"vertragsanalyse_{slug}_{datum}.md"

        template = create_analysis_template(pdf_path.stem, rohtext, seiten)
        with open(output_pfad, "w", encoding="utf-8") as f:
            f.write(template)

        ergebnis["status"] = "OK"
        ergebnis["output_pfad"] = str(output_pfad)
        print(f"      OK – {seiten} Seiten, {len(rohtext)} Zeichen → {output_pfad.name}")

    except ImportError:
        ergebnis["status"] = "FEHLER"
        ergebnis["fehler"] = "pdfplumber nicht installiert. Führe aus: pip install pdfplumber"
        print(f"      FEHLER: {ergebnis['fehler']}")

    except Exception as e:
        ergebnis["status"] = "FEHLER"
        ergebnis["fehler"] = str(e)
        print(f"      FEHLER: {e}")

    return ergebnis


def erstelle_zusammenfassung(ergebnisse: list, ordner: str, dauer_sek: float) -> str:
    datum = datetime.now().strftime("%Y-%m-%d %H:%M")
    ok = [e for e in ergebnisse if e["status"] == "OK"]
    fehler = [e for e in ergebnisse if e["status"] == "FEHLER"]
    uebersprungen = [e for e in ergebnisse if e["status"] == "UEBERSPRUNGEN"]

    zeilen = [
        f"# Batch-Zusammenfassung",
        f"",
        f"**Datum:** {datum}",
        f"**Ordner:** {ordner}",
        f"**Dauer:** {dauer_sek:.1f} Sekunden",
        f"",
        f"---",
        f"",
        f"## Ergebnis",
        f"",
        f"| Status | Anzahl |",
        f"|--------|--------|",
        f"| Erfolgreich | {len(ok)} |",
        f"| Fehler | {len(fehler)} |",
        f"| Übersprungen | {len(uebersprungen)} |",
        f"| **Gesamt** | **{len(ergebnisse)}** |",
        f"",
    ]

    if ok:
        zeilen += [
            f"---",
            f"",
            f"## Erfolgreich verarbeitet",
            f"",
        ]
        for e in ok:
            zeilen.append(
                f"- **{e['datei']}** – {e['seiten']} Seiten, "
                f"{e['zeichen']} Zeichen → `{os.path.basename(e['output_pfad'])}`"
            )
        zeilen.append("")

    if fehler:
        zeilen += [
            f"---",
            f"",
            f"## Fehler",
            f"",
        ]
        for e in fehler:
            zeilen.append(f"- **{e['datei']}** – {e['fehler']}")
        zeilen.append("")

    if uebersprungen:
        zeilen += [
            f"---",
            f"",
            f"## Übersprungen (keine PDFs)",
            f"",
        ]
        for e in uebersprungen:
            zeilen.append(f"- {e['datei']}")
        zeilen.append("")

    zeilen += [
        f"---",
        f"",
        f"*Erstellt mit Vertragsmanagement-Workflow v1.0 (Batch)*",
    ]

    return "\n".join(zeilen)


def main():
    import time

    if len(sys.argv) < 2:
        print("Verwendung: python tools/batch_vertragsanalyse.py ./ordner/")
        print("Beispiel:   python tools/batch_vertragsanalyse.py .tmp/test_vertraege/")
        sys.exit(1)

    eingabe_ordner = Path(sys.argv[1])

    if not eingabe_ordner.exists():
        print(f"Fehler: Ordner nicht gefunden: {eingabe_ordner}")
        sys.exit(1)

    if not eingabe_ordner.is_dir():
        print(f"Fehler: Das ist kein Ordner: {eingabe_ordner}")
        sys.exit(1)

    # Alle Dateien im Ordner finden
    alle_dateien = list(eingabe_ordner.iterdir())
    pdf_dateien = [f for f in alle_dateien if f.suffix.lower() == ".pdf"]
    andere_dateien = [f for f in alle_dateien if f.suffix.lower() != ".pdf" and f.is_file()]

    if not pdf_dateien:
        print(f"Keine PDF-Dateien gefunden in: {eingabe_ordner}")
        sys.exit(0)

    output_dir = Path(".tmp")
    output_dir.mkdir(exist_ok=True)

    print(f"\nBatch-Vertragsanalyse")
    print(f"{'=' * 40}")
    print(f"Ordner:  {eingabe_ordner.resolve()}")
    print(f"PDFs:    {len(pdf_dateien)}")
    if andere_dateien:
        print(f"Andere Dateien (werden übersprungen): {len(andere_dateien)}")
    print(f"Output:  {output_dir.resolve()}")

    start = time.time()
    ergebnisse = []

    # Übersprungene Nicht-PDFs dokumentieren
    for datei in andere_dateien:
        ergebnisse.append({
            "datei": datei.name,
            "status": "UEBERSPRUNGEN",
            "output_pfad": None,
            "fehler": "Keine PDF-Datei",
            "seiten": 0,
            "zeichen": 0,
        })

    # PDFs verarbeiten
    for i, pdf_pfad in enumerate(sorted(pdf_dateien), 1):
        ergebnis = verarbeite_pdf(pdf_pfad, output_dir, i, len(pdf_dateien))
        ergebnisse.append(ergebnis)

    dauer = time.time() - start

    # Zusammenfassung schreiben
    zusammenfassung = erstelle_zusammenfassung(ergebnisse, str(eingabe_ordner), dauer)
    datum_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
    zusammenfassung_pfad = output_dir / f"batch_zusammenfassung_{datum_slug}.md"
    with open(zusammenfassung_pfad, "w", encoding="utf-8") as f:
        f.write(zusammenfassung)

    # Abschlussbericht im Terminal
    ok_count = sum(1 for e in ergebnisse if e["status"] == "OK")
    fehler_count = sum(1 for e in ergebnisse if e["status"] == "FEHLER")

    print(f"\n{'=' * 40}")
    print(f"Abgeschlossen in {dauer:.1f}s")
    print(f"  Erfolgreich: {ok_count}/{len(pdf_dateien)}")
    if fehler_count:
        print(f"  Fehler:      {fehler_count}/{len(pdf_dateien)}")
    print(f"\nZusammenfassung: {zusammenfassung_pfad}")
    print(f"Analysen in:     .tmp/")


if __name__ == "__main__":
    main()
```

---

## Schritt 3: Mehrere Test-PDFs erstellen

Erstelle die Datei `tools/create_test_batch.py`, die 4 verschiedene
Test-Verträge auf einmal generiert:

```python
#!/usr/bin/env python3
"""Erstellt 4 verschiedene Test-Verträge für den Batch-Test."""

import os
from pathlib import Path


def schreibe_pdf(output_path: str, titel: str, zeilen: list):
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
    except ImportError:
        print("Installiere: pip install reportlab")
        import sys
        sys.exit(1)

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    y = height - 60

    c.setFont("Helvetica-Bold", 13)
    c.drawString(60, y, titel)
    c.setFont("Helvetica", 10)
    y -= 30

    for zeile in zeilen:
        if y < 60:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 60
        if zeile.startswith("§") or zeile.isupper():
            c.setFont("Helvetica-Bold", 10)
        else:
            c.setFont("Helvetica", 10)
        c.drawString(60, y, zeile)
        y -= 16

    c.save()
    print(f"  Erstellt: {output_path}")


def main():
    ordner = Path(".tmp/test_vertraege")
    ordner.mkdir(parents=True, exist_ok=True)

    # Vertrag 1: Dienstleistungsvertrag
    schreibe_pdf(str(ordner / "01_dienstleistungsvertrag.pdf"),
        "DIENSTLEISTUNGSVERTRAG",
        [
            "zwischen Mustermann GmbH, Leopoldstr. 10, 80802 München (Auftraggeber)",
            "und TechService UG, Maximilianstr. 5, 80539 München (Auftragnehmer)",
            "",
            "§ 1 Gegenstand",
            "IT-Beratung im Bereich DSGVO-Compliance.",
            "",
            "§ 2 Vergütung",
            "Monatlich 2.500 EUR netto, zahlbar binnen 14 Tagen.",
            "",
            "§ 3 Laufzeit",
            "Beginn: 01.05.2026. Laufzeit: unbefristet.",
            "Kündigung: 3 Monate zum Monatsende.",
            "",
            "§ 4 Geheimhaltung",
            "Verschwiegenheitspflicht auch nach Vertragsende.",
            "",
            "§ 5 Haftung",
            "Haftung begrenzt auf Vorsatz und grobe Fahrlässigkeit.",
            "Maximale Haftungssumme: 10.000 EUR.",
            "",
            "Gerichtsstand: München. Recht: Deutschland.",
        ]
    )

    # Vertrag 2: Mietvertrag
    schreibe_pdf(str(ordner / "02_mietvertrag.pdf"),
        "MIETVERTRAG",
        [
            "zwischen Schmidt Immobilien GmbH, Sendlinger Str. 20, 80331 München",
            "(Vermieter) und Luca Langer, Nymphenburger Str. 5, 80335 München",
            "(Mieter)",
            "",
            "§ 1 Mietobjekt",
            "3-Zimmer-Wohnung, 75 qm, Nymphenburger Str. 5, 80335 München.",
            "",
            "§ 2 Miete",
            "Kaltmiete: 1.400 EUR. Nebenkosten: 200 EUR. Gesamt: 1.600 EUR.",
            "Fälligkeit: 1. Werktag des Monats.",
            "",
            "§ 3 Mietdauer",
            "Beginn: 01.06.2026. Unbefristet.",
            "Kündigung durch Mieter: 3 Monate. Vermieter: gesetzliche Fristen.",
            "",
            "§ 4 Kaution",
            "3 Monatskaltmieten = 4.200 EUR, zahlbar bis 01.06.2026.",
            "",
            "§ 5 Schönheitsreparaturen",
            "Mieter trägt Schönheitsreparaturen bei Auszug.",
            "",
            "Gerichtsstand: München.",
        ]
    )

    # Vertrag 3: Kaufvertrag
    schreibe_pdf(str(ordner / "03_kaufvertrag.pdf"),
        "KAUFVERTRAG",
        [
            "zwischen Elektronik AG, Rosenheimer Str. 145, 81671 München (Verkäufer)",
            "und Büro Solutions GmbH, Tal 12, 80331 München (Käufer)",
            "",
            "§ 1 Kaufgegenstand",
            "50 Laptops Modell ProBook 450, inkl. 3 Jahre Garantie.",
            "",
            "§ 2 Kaufpreis",
            "Gesamtpreis: 62.500 EUR netto (1.250 EUR pro Stück).",
            "Zahlung: 50% bei Bestellung, 50% bei Lieferung.",
            "",
            "§ 3 Lieferung",
            "Liefertermin: 15.05.2026. Lieferung frei Haus München.",
            "Verzug: 0,5% Vertragsstrafe pro Woche, max. 5%.",
            "",
            "§ 4 Gewährleistung",
            "Gewährleistung: 24 Monate ab Lieferdatum.",
            "",
            "§ 5 Eigentumsvorbehalt",
            "Ware bleibt bis vollständiger Bezahlung Eigentum des Verkäufers.",
            "",
            "Gerichtsstand: München.",
        ]
    )

    # Vertrag 4: Arbeitsvertrag
    schreibe_pdf(str(ordner / "04_arbeitsvertrag.pdf"),
        "ARBEITSVERTRAG",
        [
            "zwischen Consulting GmbH, Theatinerstr. 8, 80333 München (Arbeitgeber)",
            "und Max Müller, Schwabing, München (Arbeitnehmer)",
            "",
            "§ 1 Beginn und Tätigkeit",
            "Beginn: 01.07.2026. Tätigkeit: Junior-Berater.",
            "",
            "§ 2 Probezeit",
            "Probezeit: 6 Monate. Kündigung in Probezeit: 2 Wochen.",
            "",
            "§ 3 Arbeitszeit",
            "40 Stunden pro Woche. Überstunden nach Absprache.",
            "",
            "§ 4 Vergütung",
            "Bruttogehalt: 42.000 EUR jährlich, zahlbar monatlich.",
            "Bonus: bis 10% nach Zielerreichung.",
            "",
            "§ 5 Kündigung",
            "Nach Probezeit: 4 Wochen zum Monatsende.",
            "Nach 2 Jahren: 2 Monate zum Monatsende.",
            "",
            "§ 6 Wettbewerbsverbot",
            "12 Monate nach Austritt, Ausgleich 50% des Gehalts.",
            "",
            "Gerichtsstand: München.",
        ]
    )

    print(f"\n4 Test-Vertraege erstellt in: {ordner.resolve()}")
    print(f"Jetzt testen mit:")
    print(f"  python tools/batch_vertragsanalyse.py {ordner}")


if __name__ == "__main__":
    main()
```

---

## Schritt 4: Abhängigkeiten sicherstellen

Führe aus:
```
pip install pdfplumber reportlab
```

---

## Schritt 5: Test-Batch erstellen und ausführen

Führe nacheinander aus:

```
python tools/create_test_batch.py
python tools/batch_vertragsanalyse.py .tmp/test_vertraege/
```

---

## Schritt 6: Ergebnis zeigen und bewerten

Zeige mir nach dem Durchlauf:

1. Den Terminal-Output des Batch-Runs (Fortschrittsanzeige + Abschlussbericht)
2. Den vollständigen Inhalt der Datei `batch_zusammenfassung_[...].md`
3. Exemplarisch eine der 4 erstellten Analyse-Dateien (z.B. den Mietvertrag)
4. Eine kurze Einschätzung: Was funktioniert gut, was könnte verbessert werden?
