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
