#!/usr/bin/env python3
"""
Pipeline – Vollständige Verarbeitungskette für einen oder mehrere Verträge.

PDF → Analyse (.md) → HTML-Report → Datenbank-Update

Usage:
    python tools/pipeline.py vertraege/mietvertrag.pdf
    python tools/pipeline.py vertraege/          (alle PDFs im Ordner)
    python tools/pipeline.py vertraege/ --no-ki  (ohne API-Call)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def verarbeite_eine_pdf(pdf_path: Path, no_ki: bool, output_dir: Path) -> bool:
    """
    Führt die 3 Schritte (Analyse, Report, DB) für eine PDF durch.
    Gibt True bei Erfolg zurück, False bei Fehler.
    """
    name = pdf_path.name

    # ── [1/3] PDF analysieren ────────────────────────────────────────────────
    modus = "--no-ki" if no_ki else f"KI"
    print(f"\n{'─' * 50}")
    print(f"Vertrag: {name}  [{modus}]")
    print(f"{'─' * 50}")
    print(f"[1/3] PDF extrahieren & analysieren ...")

    try:
        from vertragsanalyse import verarbeite_pdf
        md_pfad = verarbeite_pdf(str(pdf_path), no_ki=no_ki)
        print(f"      → {md_pfad}")
    except Exception as e:
        print(f"      ✗ Fehler: {e}")
        return False

    # ── [2/3] HTML-Report generieren ─────────────────────────────────────────
    print(f"[2/3] HTML-Report generieren ...")
    try:
        from generate_report import generiere_report
        html_pfad = generiere_report(md_pfad, output_dir=output_dir)
        print(f"      → {html_pfad}")
    except Exception as e:
        print(f"      ✗ Fehler: {e}")
        return False

    # ── [3/3] Datenbank aktualisieren ────────────────────────────────────────
    print(f"[3/3] Datenbank aktualisieren ...")
    try:
        from vertrags_datenbank import aktualisiere_db
        db_pfad = output_dir / "vertrags_datenbank.csv"
        # .md-Dateien liegen in .tmp/ (Standard von verarbeite_pdf)
        tmp_dir = Path(__file__).parent.parent / ".tmp"
        anzahl = aktualisiere_db(tmp_dir, db_pfad)
        print(f"      → {db_pfad}  ({anzahl} Einträge)")
    except Exception as e:
        print(f"      ✗ Fehler: {e}")
        return False

    print(f"[✓] Abgeschlossen")
    return True


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Pipeline – PDF → Analyse → HTML → Datenbank\n")
        print("Verwendung:")
        print("  python3 tools/pipeline.py vertrag.pdf")
        print("  python3 tools/pipeline.py vertraege/    (alle PDFs im Ordner)")
        print("  python3 tools/pipeline.py vertrag.pdf --no-ki")
        sys.exit(0)

    no_ki = "--no-ki" in args
    args = [a for a in args if a != "--no-ki"]

    # PDFs sammeln
    pdf_dateien = []
    for arg in args:
        p = Path(arg)
        if p.is_dir():
            gefunden = sorted(p.glob("*.pdf"))
            if not gefunden:
                print(f"Warnung: Keine PDFs in {p}")
            pdf_dateien.extend(gefunden)
        elif p.is_file() and p.suffix.lower() == ".pdf":
            pdf_dateien.append(p)
        else:
            print(f"Warnung: Nicht gefunden oder kein PDF – {p}")

    if not pdf_dateien:
        print("Fehler: Keine PDF-Dateien gefunden.")
        sys.exit(1)

    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nPipeline gestartet: {len(pdf_dateien)} PDF(s)  |  "
          f"{'--no-ki (kein API-Call)' if no_ki else 'KI-Analyse aktiv'}")

    erfolge = 0
    fehler = 0
    for pdf in pdf_dateien:
        if verarbeite_eine_pdf(pdf, no_ki, output_dir):
            erfolge += 1
        else:
            fehler += 1

    print(f"\n{'═' * 50}")
    print(f"Pipeline abgeschlossen: {erfolge} erfolgreich, {fehler} fehlgeschlagen")
    if erfolge:
        print(f"Output:  {output_dir.resolve()}")

    sys.exit(0 if fehler == 0 else 1)


if __name__ == "__main__":
    main()
