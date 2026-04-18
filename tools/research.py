"""
research.py — WAT Framework Tool
Erstellt ein strukturiertes Research-Template in .tmp/ für ein gegebenes Thema.

Verwendung:
    python tools/research.py "DSGVO Art. 17 – Recht auf Löschung"
"""

import sys
import os
from datetime import date


def sanitize_filename(name: str) -> str:
    """Konvertiert Thema in sicheren Dateinamen."""
    keep = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZäöüÄÖÜß0123456789 -_")
    cleaned = "".join(c if c in keep else "_" for c in name)
    return cleaned.strip().replace(" ", "_")[:80]


def build_template(thema: str, datum: str) -> str:
    return f"""# Research: {thema}

**Datum:** {datum}
**Workflow:** workflows/research_workflow.md

---

## 1. Kernaussage


## 2. Rechtliche Grundlagen


## 3. Streitpunkte & Auslegungsfragen


## 4. Praktische Relevanz


## 5. Business-Relevanz KI-Agentur


## 6. Offene Fragen


---

## Qualitäts-Check
- [ ] Alle 6 Abschnitte befüllt
- [ ] Rechtliche Grundlagen mit konkreten Artikeln
- [ ] Mindestens ein KI-Agentur Use Case in Abschnitt 5
- [ ] Offene Fragen als echte Fragen formuliert
"""


def main():
    if len(sys.argv) < 2:
        print("Verwendung: python tools/research.py \"<Thema>\"")
        sys.exit(1)

    thema = sys.argv[1]
    datum = date.today().isoformat()

    # Pfad relativ zum Projekt-Root (ein Verzeichnis über tools/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    tmp_dir = os.path.join(project_root, ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    filename = f"research_{sanitize_filename(thema)}_{datum}.md"
    filepath = os.path.join(tmp_dir, filename)

    content = build_template(thema, datum)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(filepath)


if __name__ == "__main__":
    main()
