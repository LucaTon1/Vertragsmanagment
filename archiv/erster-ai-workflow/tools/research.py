#!/usr/bin/env python3
"""
Research Tool – Initialisiert eine strukturierte Research-Datei.

Usage:
    python tools/research.py "DSGVO Art. 17 – Recht auf Löschung"
    python tools/research.py "Vertragsfreiheit im BGB"

Was dieses Script macht:
    1. Erstellt den .tmp/ Ordner falls nicht vorhanden
    2. Generiert eine strukturierte Markdown-Datei mit allen Abschnitten
    3. Gibt den Pfad zurück, damit Claude Code die Datei direkt befüllen kann
"""

import sys
import os
import re
from datetime import datetime


def slugify(text: str) -> str:
    """Thema in einen sicheren Dateinamen umwandeln."""
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "_", text.strip())
    return text[:60]


def create_research_template(thema: str) -> str:
    datum = datetime.now().strftime("%Y-%m-%d")
    return f"""# Research: {thema}

**Datum:** {datum}
**Status:** In Bearbeitung

---

## 1. Kernaussage
<!-- 1–3 präzise Sätze. Was ist das Wesentliche? Verständlich für Nicht-Juristen. -->


---

## 2. Rechtliche Grundlagen
<!-- Primärnormen mit Absatz/Nummer, verwandte Vorschriften, Rechtsprechung -->

- **Primärnorm(en):**
- **Verwandte Vorschriften:**
- **Relevante Rechtsprechung:**

---

## 3. Hauptargumente & Streitpunkte
<!-- Was ist unbestritten (h.M.)? Was ist umstritten? -->

### Unbestrittenes (h.M.):


### Offene Streitfragen:


---

## 4. Praktische Relevanz
<!-- 2–3 konkrete Beispielfälle / typische Konstellationen aus der Praxis -->


---

## 5. Business-Relevanz (KI-Agentur)
<!-- Konkret: Kundenproblem, Automatisierungspotenzial, möglicher Service -->

- **Kundenproblem:**
- **Automatisierungspotenzial:**
- **Mögliches Servicepaket:**
- **Zielmarkt-Fit (Mittelstand München):**

---

## 6. Offene Fragen & Weiterführendes
<!-- Was konnte nicht abschließend geklärt werden? Was braucht eigenen Research? -->


---

*Erstellt mit Research-Workflow v1.0 | {datum}*
"""


def main():
    if len(sys.argv) < 2:
        print("Fehler: Kein Thema angegeben.")
        print("Verwendung: python tools/research.py 'Thema hier eingeben'")
        sys.exit(1)

    thema = " ".join(sys.argv[1:])
    datum = datetime.now().strftime("%Y%m%d")
    slug = slugify(thema)

    # Output-Ordner sicherstellen
    os.makedirs(".tmp", exist_ok=True)

    output_path = f".tmp/research_{slug}_{datum}.md"

    # Template schreiben
    template = create_research_template(thema)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(template)

    print(f"Datei erstellt: {output_path}")
    print(f"Thema: {thema}")
    print(f"\nNaechster Schritt fuer Claude Code:")
    print(f"  Lies {output_path} und befuelle jeden Abschnitt gemaess workflows/research_workflow.md")

    return output_path


if __name__ == "__main__":
    main()
