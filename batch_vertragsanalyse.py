#!/usr/bin/env python3
"""
Batch-Vertragsanalyse Tool – Verarbeitet alle PDFs in einem Ordner.

Usage:
    python tools/batch_vertragsanalyse.py ./vertraege/
    python tools/batch_vertragsanalyse.py ./vertraege/ --recursive
    python tools/batch_vertragsanalyse.py ./vertraege/ --ki               (mit Claude API)
    python tools/batch_vertragsanalyse.py ./vertraege/ --ki --modell claude-sonnet-4-6
"""

import sys
import os
import re
from datetime import datetime
from pathlib import Path

# Shared utils + Fristen-Extraktor laden
sys.path.insert(0, str(Path(__file__).parent))
from utils import extract_text_from_pdf, ensure_output_dir, slugify, display_name
from fristen_extraktor import extrahiere_fristen, kategorien_label


def erstelle_fristen_hinweise(rohtext: str) -> str:
    """Erstellt vorausgefüllte Fristen-Hinweise für Abschnitt 3."""
    treffer = extrahiere_fristen(rohtext)
    if not treffer:
        return "<!-- Keine Fristen automatisch erkannt -->"
    zeilen = ["<!-- Automatisch erkannt – bitte prüfen und einordnen -->"]
    for t in treffer:
        zeilen.append(f"- {t['match']} ({kategorien_label(t['kategorie'])})")
    return "\n".join(zeilen)


def create_analysis_template(pdf_stem: str, rohtext: str, seiten: int) -> str:
    datum = datetime.now().strftime("%Y-%m-%d")
    titel = display_name(pdf_stem)          # "04_arbeitsvertrag" → "Arbeitsvertrag"
    fristen_hinweise = erstelle_fristen_hinweise(rohtext)
    vorschau = rohtext[:3000]
    if len(rohtext) > 3000:
        vorschau += "\n\n[... gekürzt – vollständiger Text unten ...]"

    return f"""# Vertragsanalyse: {titel}

**Analysedatum:** {datum}
**Seiten:** {seiten}
**Analysiert mit:** Vertragsmanagement-Workflow v1.1 (Batch)
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

{fristen_hinweise}

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


def verarbeite_pdf(
    pdf_path: Path,
    output_dir: Path,
    index: int,
    total: int,
    ki_modus: bool = False,
    modell: str = "claude-haiku-4-5-20251001",
) -> dict:
    print(f"\n  [{index}/{total}] {pdf_path.name}")

    ergebnis = {
        "datei":        pdf_path.name,
        "status":       None,
        "output_pfad":  None,
        "fehler":       None,
        "seiten":       0,
        "zeichen":      0,
        "fristen":      0,
        "kosten_usd":   0.0,
    }

    try:
        rohtext, seiten = extract_text_from_pdf(str(pdf_path))
        ergebnis["seiten"] = seiten
        ergebnis["zeichen"] = len(rohtext)
        fristen = extrahiere_fristen(rohtext)
        ergebnis["fristen"] = len(fristen)

        datum = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = slugify(pdf_path.stem)
        output_pfad = output_dir / f"vertragsanalyse_{slug}_{datum}.md"

        if ki_modus:
            # ── KI-Analyse via Claude API ────────────────────────────────────
            from ki_analyse import analysiere_vertrag, berechne_kosten

            fristen_hinweise = ""
            if fristen:
                zeilen = ["<!-- Automatisch erkannt – bitte prüfen -->"]
                for t in fristen:
                    zeilen.append(f"- {t['match']} ({kategorien_label(t['kategorie'])})")
                fristen_hinweise = "\n".join(zeilen)

            analyse_text, token_info = analysiere_vertrag(
                rohtext=rohtext,
                vertrag_titel=display_name(pdf_path.stem),
                seiten=seiten,
                fristen_hinweise=fristen_hinweise,
                modell=modell,
            )
            kosten = berechne_kosten(token_info)
            ergebnis["kosten_usd"] = kosten

            vorschau = rohtext[:3000]
            if len(rohtext) > 3000:
                vorschau += "\n\n[... gekürzt ...]"

            inhalt = (
                analyse_text
                + f"\n\n---\n\n## 7. Rohtext (Quelle)\n\n"
                  f"```\n{vorschau}\n```\n\n"
                  f"*Vollständiger Rohtext: {len(rohtext)} Zeichen*\n"
            )
            print(f"      OK (KI) – {seiten} Seiten | {len(fristen)} Fristen | "
                  f"~${kosten:.4f} → {output_pfad.name}")
        else:
            # ── Leeres Template (ohne KI) ────────────────────────────────────
            inhalt = create_analysis_template(pdf_path.stem, rohtext, seiten)
            print(f"      OK – {seiten} Seiten | {len(rohtext)} Zeichen | "
                  f"{ergebnis['fristen']} Fristen erkannt → {output_pfad.name}")

        with open(output_pfad, "w", encoding="utf-8") as f:
            f.write(inhalt)

        ergebnis["status"] = "OK"
        ergebnis["output_pfad"] = str(output_pfad)

    except ImportError:
        ergebnis["status"] = "FEHLER"
        ergebnis["fehler"] = "pdfplumber nicht installiert: pip install pdfplumber"
        print(f"      FEHLER: {ergebnis['fehler']}")

    except Exception as e:
        ergebnis["status"] = "FEHLER"
        ergebnis["fehler"] = str(e)
        print(f"      FEHLER: {e}")

    return ergebnis


def erstelle_zusammenfassung(ergebnisse: list, ordner: str, dauer_sek: float) -> str:
    datum = datetime.now().strftime("%Y-%m-%d %H:%M")
    ok           = [e for e in ergebnisse if e["status"] == "OK"]
    fehler       = [e for e in ergebnisse if e["status"] == "FEHLER"]
    uebersprungen= [e for e in ergebnisse if e["status"] == "UEBERSPRUNGEN"]

    zeilen = [
        "# Batch-Zusammenfassung",
        "",
        f"**Datum:** {datum}",
        f"**Ordner:** {ordner}",
        f"**Dauer:** {dauer_sek:.1f} Sekunden",
        "",
        "---",
        "",
        "## Ergebnis",
        "",
        "| Status | Anzahl |",
        "|--------|--------|",
        f"| Erfolgreich | {len(ok)} |",
        f"| Fehler | {len(fehler)} |",
        f"| Übersprungen | {len(uebersprungen)} |",
        f"| **Gesamt** | **{len(ergebnisse)}** |",
        "",
    ]

    if ok:
        zeilen += ["---", "", "## Erfolgreich verarbeitet", ""]
        for e in ok:
            zeilen.append(
                f"- **{e['datei']}** – {e['seiten']} Seiten, "
                f"{e['zeichen']} Zeichen, {e['fristen']} Fristen "
                f"→ `{os.path.basename(e['output_pfad'])}`"
            )
        zeilen.append("")

    if fehler:
        zeilen += ["---", "", "## Fehler", ""]
        for e in fehler:
            zeilen.append(f"- **{e['datei']}** – {e['fehler']}")
        zeilen.append("")

    if uebersprungen:
        zeilen += ["---", "", "## Übersprungen (keine PDFs)", ""]
        for e in uebersprungen:
            zeilen.append(f"- {e['datei']}")
        zeilen.append("")

    zeilen += ["---", "", "*Erstellt mit Vertragsmanagement-Workflow v1.1 (Batch)*"]
    return "\n".join(zeilen)


def main():
    import time

    if len(sys.argv) < 2:
        print("Verwendung: python tools/batch_vertragsanalyse.py ./ordner/ [Optionen]")
        print("Beispiel:   python tools/batch_vertragsanalyse.py .tmp/test_vertraege/")
        print("\nOptionen:")
        print("  --recursive          Unterordner einschließen")
        print("  --ki                 KI-Analyse via Claude API (Haiku 4.5)")
        print("  --modell <id>        Modell für KI-Modus wählen")
        sys.exit(1)

    eingabe_ordner = Path(sys.argv[1])
    rekursiv = "--recursive" in sys.argv
    ki_modus = "--ki" in sys.argv

    modell = "claude-haiku-4-5-20251001"
    if "--modell" in sys.argv:
        idx = sys.argv.index("--modell")
        if idx + 1 < len(sys.argv):
            modell = sys.argv[idx + 1]

    if not eingabe_ordner.exists():
        print(f"Fehler: Ordner nicht gefunden: {eingabe_ordner}")
        sys.exit(1)
    if not eingabe_ordner.is_dir():
        print(f"Fehler: Kein Ordner: {eingabe_ordner}")
        sys.exit(1)

    glob = eingabe_ordner.rglob("*") if rekursiv else eingabe_ordner.iterdir()
    alle_dateien  = [f for f in glob if f.is_file()]
    pdf_dateien   = [f for f in alle_dateien if f.suffix.lower() == ".pdf"]
    andere_dateien= [f for f in alle_dateien if f.suffix.lower() != ".pdf"]

    if not pdf_dateien:
        print(f"Keine PDF-Dateien gefunden in: {eingabe_ordner}")
        sys.exit(0)

    output_dir = ensure_output_dir()

    # Bereits analysierte PDFs ermitteln (verhindert doppelte API-Calls bei Re-Runs)
    bereits_analysiert = {
        re.sub(r"_\d{8}_\d{6}\.md$", "", p.name).replace("vertragsanalyse_", "")
        for p in output_dir.glob("vertragsanalyse_*.md")
    }

    print(f"\nBatch-Vertragsanalyse v2.0")
    print(f"{'=' * 40}")
    print(f"Ordner:  {eingabe_ordner.resolve()}")
    if rekursiv:
        print(f"Modus:   rekursiv (inkl. Unterordner)")
    if ki_modus:
        print(f"KI:      aktiviert ({modell})")
    print(f"PDFs:    {len(pdf_dateien)}")
    if andere_dateien:
        print(f"Andere:  {len(andere_dateien)} Dateien übersprungen")
    print(f"Output:  {output_dir}")

    # Neu zu verarbeitende PDFs
    neu_pdfs = [p for p in sorted(pdf_dateien) if slugify(p.stem) not in bereits_analysiert]
    skip_count = len(pdf_dateien) - len(neu_pdfs)
    if skip_count:
        print(f"Bereits analysiert: {skip_count} PDF(s) übersprungen (--force um zu erzwingen)")

    force = "--force" in sys.argv

    # Kostenabschätzung anzeigen und bestätigen lassen (nur im KI-Modus, interaktiv)
    if ki_modus and zu_verarbeiten and sys.stdin.isatty():
        from ki_analyse import PREISE
        preise = PREISE.get(modell, PREISE["claude-haiku-4-5-20251001"])
        anz = len(zu_verarbeiten)
        # Grobe Schätzung: ~5000 Input + 8000 Output Tokens pro Vertrag
        est_kosten = anz * (5000 / 1_000_000 * preise["input"] + 8000 / 1_000_000 * preise["output"])
        print(f"\nGeschätzte API-Kosten: ~${est_kosten:.3f} USD für {anz} Vertrag/Verträge")
        best = input("Fortfahren? [j/N] ").strip().lower()
        if best not in ("j", "ja", "y", "yes"):
            print("Abgebrochen.")
            sys.exit(0)

    start = time.time()
    ergebnisse = []

    for datei in andere_dateien:
        ergebnisse.append({
            "datei": datei.name, "status": "UEBERSPRUNGEN",
            "output_pfad": None, "fehler": "Keine PDF-Datei",
            "seiten": 0, "zeichen": 0, "fristen": 0,
        })

    zu_verarbeiten = sorted(pdf_dateien) if force else neu_pdfs
    for i, pdf_pfad in enumerate(zu_verarbeiten, 1):
        ergebnis = verarbeite_pdf(
            pdf_pfad, output_dir, i, len(zu_verarbeiten),
            ki_modus=ki_modus, modell=modell,
        )
        ergebnisse.append(ergebnis)

    # Übersprungene als UEBERSPRUNGEN vermerken
    if not force:
        for pdf_pfad in sorted(pdf_dateien):
            if slugify(pdf_pfad.stem) in bereits_analysiert:
                ergebnisse.append({
                    "datei": pdf_pfad.name, "status": "UEBERSPRUNGEN",
                    "output_pfad": None, "fehler": "Bereits analysiert",
                    "seiten": 0, "zeichen": 0, "fristen": 0,
                })

    dauer = time.time() - start

    zusammenfassung = erstelle_zusammenfassung(ergebnisse, str(eingabe_ordner), dauer)
    datum_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
    zusammenfassung_pfad = output_dir / f"batch_zusammenfassung_{datum_slug}.md"
    with open(zusammenfassung_pfad, "w", encoding="utf-8") as f:
        f.write(zusammenfassung)

    ok_count     = sum(1 for e in ergebnisse if e["status"] == "OK")
    fehler_count = sum(1 for e in ergebnisse if e["status"] == "FEHLER")

    print(f"\n{'=' * 40}")
    print(f"Abgeschlossen in {dauer:.1f}s")
    print(f"  Erfolgreich: {ok_count}/{len(pdf_dateien)}")
    if fehler_count:
        print(f"  Fehler:      {fehler_count}/{len(pdf_dateien)}")
    if ki_modus:
        gesamt_kosten = sum(e.get("kosten_usd", 0.0) for e in ergebnisse)
        print(f"  API-Kosten:  ~${gesamt_kosten:.4f} USD gesamt")
    print(f"\nZusammenfassung: {zusammenfassung_pfad.relative_to(Path.cwd()) if zusammenfassung_pfad.is_relative_to(Path.cwd()) else zusammenfassung_pfad}")
    print(f"Analysen in:     {output_dir}")


if __name__ == "__main__":
    main()
