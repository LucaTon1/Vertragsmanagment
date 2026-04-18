#!/usr/bin/env python3
"""
Vertragsanalyse Tool – Einzelne PDF vollständig analysieren.

Standard: PDF → Text extrahieren → Claude API → fertige Analyse
Fallback:  PDF → Text extrahieren → leeres Template (--no-ki)

Usage:
    python tools/vertragsanalyse.py vertrag.pdf
    python tools/vertragsanalyse.py vertrag.pdf --modell claude-sonnet-4-6
    python tools/vertragsanalyse.py vertrag.pdf --no-ki   (nur Template, kein API-Call)
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import extract_text_from_pdf, ensure_output_dir, slugify, display_name
from fristen_extraktor import extrahiere_fristen, kategorien_label
from ki_analyse import DEFAULT_MODELL, PREISE


def erstelle_fristen_hinweise(rohtext: str) -> str:
    """Erstellt vorausgefüllte Fristen-Hinweise für Abschnitt 3."""
    treffer = extrahiere_fristen(rohtext)
    if not treffer:
        return "<!-- Keine Fristen automatisch erkannt -->"
    zeilen = ["<!-- Automatisch erkannt – bitte prüfen und einordnen -->"]
    for t in treffer:
        zeilen.append(f"- {t['match']} ({kategorien_label(t['kategorie'])})")
    return "\n".join(zeilen)


def erstelle_leeres_template(pdf_stem: str, rohtext: str, seiten: int) -> str:
    """Erstellt ein leeres Template (ohne KI) – Fallback für --no-ki."""
    datum = datetime.now().strftime("%Y-%m-%d")
    titel = display_name(pdf_stem)
    fristen_hinweise = erstelle_fristen_hinweise(rohtext)
    vorschau = rohtext[:3000]
    if len(rohtext) > 3000:
        vorschau += "\n\n[... gekürzt – vollständiger Text unten ...]"

    return f"""# Vertragsanalyse: {titel}

**Analysedatum:** {datum}
**Seiten:** {seiten}
**Analysiert mit:** Vertragsmanagement-Workflow v2.0 (manuell)
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


def verarbeite_pdf(pdf_pfad: str, no_ki: bool = False, modell: str = None) -> Path:
    """
    Importierbare Kernfunktion: PDF → Analyse-Markdown.

    Returns:
        Path zur erstellten .md-Datei
    """
    from ki_analyse import analysiere_vertrag, berechne_kosten, formatiere_token_info

    pdf_path = Path(pdf_pfad)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")

    if modell is None:
        modell = DEFAULT_MODELL

    rohtext, seiten = extract_text_from_pdf(str(pdf_path))
    fristen = extrahiere_fristen(rohtext)

    output_dir = ensure_output_dir()
    datum = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(pdf_path.stem)
    output_path = output_dir / f"vertragsanalyse_{slug}_{datum}.md"

    if no_ki:
        inhalt = erstelle_leeres_template(pdf_path.stem, rohtext, seiten)
    else:
        fristen_hinweise = erstelle_fristen_hinweise(rohtext)
        analyse_text, token_info = analysiere_vertrag(
            rohtext=rohtext,
            vertrag_titel=display_name(pdf_path.stem),
            seiten=seiten,
            fristen_hinweise=fristen_hinweise,
            modell=modell,
        )
        vorschau = rohtext[:3000]
        if len(rohtext) > 3000:
            vorschau += "\n\n[... gekürzt – vollständiger Text unten ...]"
        inhalt = (
            analyse_text
            + f"\n\n---\n\n"
              f"## 7. Rohtext (Quelle)\n\n"
              f"```\n{vorschau}\n```\n\n"
              f"*Vollständiger Rohtext: {len(rohtext)} Zeichen | "
              f"{rohtext.count(chr(10))} Zeilen*\n"
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(inhalt)

    return output_path


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Vertragsanalyse – PDF vollständig analysieren\n")
        print("Verwendung:")
        print("  python tools/vertragsanalyse.py vertrag.pdf")
        print("  python tools/vertragsanalyse.py vertrag.pdf --modell claude-sonnet-4-6")
        print("  python tools/vertragsanalyse.py vertrag.pdf --no-ki")
        print("\nOptionen:")
        print("  --no-ki          Nur Text extrahieren, kein API-Call (leeres Template)")
        print("  --modell <id>    Claude-Modell wählen (Standard: claude-haiku-4-5-20251001)")
        print("\nVerfügbare Modelle:")
        for mid, info in PREISE.items():
            marker = " ← Standard" if mid == DEFAULT_MODELL else ""
            print(f"  {mid:<40} {info['label']}{marker}")
        sys.exit(0)

    pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"Fehler: Datei nicht gefunden: {pdf_path}")
        sys.exit(1)

    no_ki = "--no-ki" in sys.argv

    modell = DEFAULT_MODELL
    if "--modell" in sys.argv:
        idx = sys.argv.index("--modell")
        if idx + 1 < len(sys.argv):
            modell = sys.argv[idx + 1]
        if modell not in PREISE:
            print(f"Unbekanntes Modell: {modell}")
            sys.exit(1)

    # ── Schritt 1: Text extrahieren ──────────────────────────────────────────
    print(f"Verarbeite: {pdf_path.name}")
    rohtext, seiten = extract_text_from_pdf(str(pdf_path))
    print(f"  {seiten} Seiten | {len(rohtext)} Zeichen")

    fristen = extrahiere_fristen(rohtext)
    print(f"  {len(fristen)} Fristen automatisch erkannt")

    output_dir = ensure_output_dir()
    datum = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(pdf_path.stem)
    output_path = output_dir / f"vertragsanalyse_{slug}_{datum}.md"

    # ── Schritt 2a: KI-Analyse (Standard) ───────────────────────────────────
    if not no_ki:
        try:
            from ki_analyse import analysiere_vertrag, berechne_kosten, formatiere_token_info

            fristen_hinweise = erstelle_fristen_hinweise(rohtext)
            print(f"\nSende an Claude API ({modell})...")

            analyse_text, token_info = analysiere_vertrag(
                rohtext=rohtext,
                vertrag_titel=display_name(pdf_path.stem),
                seiten=seiten,
                fristen_hinweise=fristen_hinweise,
                modell=modell,
            )
            print(f"  {formatiere_token_info(token_info)}")

            # Rohtext-Anhang hinzufügen
            vorschau = rohtext[:3000]
            if len(rohtext) > 3000:
                vorschau += "\n\n[... gekürzt – vollständiger Text unten ...]"

            inhalt = (
                analyse_text
                + f"\n\n---\n\n"
                  f"## 7. Rohtext (Quelle)\n\n"
                  f"```\n{vorschau}\n```\n\n"
                  f"*Vollständiger Rohtext: {len(rohtext)} Zeichen | "
                  f"{rohtext.count(chr(10))} Zeilen*\n"
            )

        except (ImportError, ValueError) as e:
            print(f"\nKI-Analyse fehlgeschlagen: {e}")
            print("Falle zurück auf leeres Template (--no-ki Modus)...")
            inhalt = erstelle_leeres_template(pdf_path.stem, rohtext, seiten)

    # ── Schritt 2b: Leeres Template (--no-ki) ───────────────────────────────
    else:
        print("\nModus: --no-ki (leeres Template, kein API-Call)")
        inhalt = erstelle_leeres_template(pdf_path.stem, rohtext, seiten)

    # ── Schritt 3: Datei schreiben ───────────────────────────────────────────
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(inhalt)

    print(f"\nDatei erstellt: {output_path}")
    if no_ki:
        print(f"Nächster Schritt: Öffne die Datei und befülle alle Abschnitte")
        print(f"                  gemäß workflows/vertragsmanagement_workflow.md")
    else:
        print(f"Nächster Schritt: python tools/vertrags_datenbank.py")

    return str(output_path)


if __name__ == "__main__":
    main()
