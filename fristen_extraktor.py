#!/usr/bin/env python3
"""
Fristen-Extraktor – Erkennt automatisch alle Fristen und Datumsangaben
in Vertrags-PDFs per Regex. Kein AI-API nötig.

Usage:
    python tools/fristen_extraktor.py vertrag.pdf
    python tools/fristen_extraktor.py ./vertraege/
"""

import sys
import re
import os
from datetime import datetime
from pathlib import Path

# utils aus demselben Ordner laden
sys.path.insert(0, str(Path(__file__).parent))
from utils import extract_text_from_pdf, ensure_output_dir, slugify, PROJECT_ROOT


# ── Regex-Muster ─────────────────────────────────────────────────────────────

MUSTER = {
    "absolutes_datum": [
        # 01.05.2026 / 1.5.2026
        r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b",
        # 1. Mai 2026 / 15. Juli 2025
        r"\b(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|August|"
        r"September|Oktober|November|Dezember)\s+(\d{4})\b",
        # Mai 2026 (Monatsangabe ohne Tag)
        r"\b(Januar|Februar|März|April|Mai|Juni|Juli|August|"
        r"September|Oktober|November|Dezember)\s+(\d{4})\b",
    ],
    "kuendigungsfrist": [
        # "Kündigung in Probezeit: 2 Wochen" / "Kündigung nach 2 Jahren: 3 Monate"
        r"[Kk]ündigung[^.;\n]{0,60}:\s*\d+\s+(?:Woche|Monat|Tag|Jahr)\w*",
        # "Kündigungsfrist: 3 Monate" / "Kündigungsfrist von 30 Tagen"
        r"[Kk]ündigungsfrist[:\s]+(?:von\s+)?(?:mindestens\s+)?\d+\s+\w+",
        # "ordentliche Kündigung" / "außerordentliche Kündigung"
        r"(?:ordentliche|außerordentliche|fristlose)\s+[Kk]ündigung",
        # "Kündigung mit 3 Monaten Frist" / "Kündigung unter Einhaltung einer Frist"
        r"[Kk]ündigung\s+(?:mit|unter)\s+\w+.*?Frist",
        # "mit mindestens 30 Tagen zu kündigen"
        r"(?:mit|unter Einhaltung)\s+(?:mindestens\s+)?\d+\s+(?:Woche|Monat|Tag|Jahr)\w*\s+(?:zu\s+)?[Kk]ündig",
    ],
    "relative_frist": [
        # 3 Monate / 6 Monate / zwölf Monate
        r"\b(\d+|zwei|drei|vier|fünf|sechs|sieben|acht|neun|zehn|zwölf|"
        r"vierzehn|dreißig|sechzig|neunzig)\s+Monat(?:e|en)?\b",
        # 30 Tage / 14 Tage / 90 Tage
        r"\b(\d+|vierzehn|dreißig|sechzig|neunzig)\s+(?:Werk|Kalender)?tag(?:e|en)?\b",
        # 2 Wochen / 4 Wochen
        r"\b(\d+|zwei|drei|vier|sechs|acht)\s+Woche(?:n)?\b",
        # 1 Jahr / 2 Jahre
        r"\b(\d+|ein|zwei|drei)\s+Jahr(?:e|en)?\b",
    ],
    "zahlungsfrist": [
        r"(?:binnen|innerhalb von|zahlbar binnen|fällig binnen)\s+\d+\s+\w+",
        r"Zahlungsfrist[:\s]+\w+",
        r"zahlbar\s+(?:monatlich|jährlich|quartalsweise|wöchentlich)",
        r"fällig\s+(?:am|zum|innerhalb)",
        r"Zahlungsziel[:\s]+\w+",
    ],
    "laufzeit": [
        r"[Ll]aufzeit[:\s]+\w+",
        r"(?:unbefristet|befristet|auf unbestimmte Zeit)",
        r"(?:läuft|gilt)\s+(?:bis|bis zum|ab)",
        r"[Vv]ertrag(?:sbeginn|sende|slaufzeit)",
    ],
}


def extrahiere_kontext(text: str, match_start: int, match_end: int,
                       fenster: int = 80) -> str:
    """Gibt den Text rund um einen Match zurück (Kontext-Fenster)."""
    start = max(0, match_start - fenster)
    ende = min(len(text), match_end + fenster)
    kontext = text[start:ende].replace("\n", " ").strip()
    if start > 0:
        kontext = "…" + kontext
    if ende < len(text):
        kontext = kontext + "…"
    return kontext


def extrahiere_fristen(text: str) -> list:
    """
    Sucht alle Fristen-Matches im Text.
    Reihenfolge: kuendigungsfrist wird VOR relative_frist gesucht,
    damit "Kündigung: 2 Wochen" als Kündigung klassifiziert wird,
    nicht als generische Frist.
    """
    treffer = []
    belegte_positionen: set = set()  # Verhindert Überlappungen

    # Reihenfolge bestimmt Priorität bei Überlappung
    reihenfolge = ["absolutes_datum", "kuendigungsfrist", "zahlungsfrist",
                   "laufzeit", "relative_frist"]

    for kategorie in reihenfolge:
        muster_liste = MUSTER.get(kategorie, [])
        for muster in muster_liste:
            for m in re.finditer(muster, text, re.IGNORECASE):
                match_text = m.group(0).strip()

                # Überlappung mit bereits gefundenem Treffer prüfen
                match_range = set(range(m.start(), m.end()))
                if match_range & belegte_positionen:
                    continue  # Überlappung → überspringen

                belegte_positionen |= match_range
                kontext = extrahiere_kontext(text, m.start(), m.end())
                treffer.append({
                    "kategorie": kategorie,
                    "match": match_text,
                    "kontext": kontext,
                    "position": m.start(),
                })

    treffer.sort(key=lambda x: x["position"])
    return treffer


def kategorien_label(kategorie: str) -> str:
    labels = {
        "absolutes_datum": "Datum",
        "relative_frist":  "Frist",
        "zahlungsfrist":   "Zahlung",
        "kuendigungsfrist":"Kündigung",
        "laufzeit":        "Laufzeit",
    }
    return labels.get(kategorie, kategorie)


def erstelle_fristen_bericht(dateiname: str, treffer: list,
                              rohtext_laenge: int) -> str:
    datum = datetime.now().strftime("%Y-%m-%d")

    gruppen: dict = {}
    for t in treffer:
        gruppen.setdefault(t["kategorie"], []).append(t)

    zeilen = [
        f"# Fristen-Analyse: {dateiname}",
        f"",
        f"**Analysedatum:** {datum}",
        f"**Gefundene Fristen:** {len(treffer)}",
        f"**Rohtext:** {rohtext_laenge} Zeichen",
        f"",
        f"---",
        f"",
    ]

    for kat in ["absolutes_datum", "kuendigungsfrist", "relative_frist",
                "zahlungsfrist", "laufzeit"]:
        if kat not in gruppen:
            continue
        label = kategorien_label(kat)
        eintraege = gruppen[kat]
        zeilen += [f"## {label} ({len(eintraege)} Treffer)", f""]
        for e in eintraege:
            zeilen.append(f"**`{e['match']}`**")
            zeilen.append(f"> {e['kontext']}")
            zeilen.append(f"")

    if not treffer:
        zeilen += [
            "## Keine Fristen gefunden",
            "",
            "Mögliche Ursachen:",
            "- PDF ist ein Scan (kein maschinenlesbarer Text)",
            "- Vertrag enthält keine deutschen Datumsformate",
            "- Fristen sind in ungewöhnlicher Form angegeben",
        ]

    zeilen += [f"---", f"", f"*Erstellt mit Fristen-Extraktor v1.1 (Regex, kein AI)*"]
    return "\n".join(zeilen)


def main():
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  python tools/fristen_extraktor.py vertrag.pdf")
        print("  python tools/fristen_extraktor.py ./vertraege/")
        sys.exit(1)

    eingabe = Path(sys.argv[1])
    output_dir = ensure_output_dir()

    if eingabe.is_file():
        pdf_dateien = [eingabe]
    elif eingabe.is_dir():
        pdf_dateien = sorted(eingabe.glob("**/*.pdf"))
        if not pdf_dateien:
            print(f"Keine PDFs gefunden in: {eingabe}")
            sys.exit(0)
    else:
        print(f"Nicht gefunden: {eingabe}")
        sys.exit(1)

    gesamt_treffer = 0

    for pdf_pfad in pdf_dateien:
        print(f"\n{'─' * 50}")
        print(f"Analysiere: {pdf_pfad.name}")

        try:
            rohtext, _ = extract_text_from_pdf(str(pdf_pfad))
            treffer = extrahiere_fristen(rohtext)
        except Exception as e:
            print(f"  FEHLER: {e}")
            continue

        gesamt_treffer += len(treffer)

        if treffer:
            print(f"  {len(treffer)} Fristen gefunden:")
            for t in treffer:
                print(f"    [{kategorien_label(t['kategorie'])}] {t['match']}")
        else:
            print("  Keine Fristen erkannt.")

        datum_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug_name = slugify(pdf_pfad.stem)
        output_pfad = output_dir / f"fristen_{slug_name}_{datum_slug}.md"
        bericht = erstelle_fristen_bericht(pdf_pfad.name, treffer, len(rohtext))
        with open(output_pfad, "w", encoding="utf-8") as f:
            f.write(bericht)
        print(f"  Bericht: {output_pfad.relative_to(PROJECT_ROOT)}")

    print(f"\n{'─' * 50}")
    print(f"Gesamt: {gesamt_treffer} Fristen in {len(pdf_dateien)} Datei(en)")


if __name__ == "__main__":
    main()
