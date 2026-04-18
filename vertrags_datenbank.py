#!/usr/bin/env python3
"""
Vertrags-Datenbank Tool – Liest alle Analyse-Markdown-Dateien aus .tmp/
und schreibt die extrahierten Felder in eine persistente CSV-Datenbank.

Usage:
    python tools/vertrags_datenbank.py
    python tools/vertrags_datenbank.py --preview
    python tools/vertrags_datenbank.py --tmp output/   (für abgeschlossene Analysen)
    python tools/vertrags_datenbank.py --output output/vertrags_datenbank.csv
"""

import sys
import os
import re
import csv
import argparse
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Parsing-Funktionen
# ---------------------------------------------------------------------------

def extrahiere_header_feld(text: str, feldname: str) -> str:
    """
    Liest ein Feld aus dem Markdown-Header.
    Sucht nach: **Feldname:** Wert
    Beispiel: **Analysedatum:** 2026-04-16  →  "2026-04-16"
    """
    pattern = rf"\*\*{re.escape(feldname)}:\*\*\s*(.+)"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return ""


def extrahiere_abschnitt(text: str, abschnitt_nr: int) -> str:
    """
    Extrahiert den Rohtext eines nummerierten Abschnitts (## 1. ... bis ## 2.).
    """
    pattern = rf"##\s+{abschnitt_nr}\..+?\n(.*?)(?=\n##\s+\d+\.|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def extrahiere_listenfeld(abschnitt_text: str, feldname: str) -> str:
    """
    Extrahiert den Wert eines Listeneintrags innerhalb eines Abschnitts.
    Sucht nach: - **Feldname:** Wert

    WICHTIG: Matcht NUR innerhalb derselben Zeile. `[ \t]*` statt `\s*`,
    damit Template-Platzhalter (`- **Partei A:**\n- **Partei B:**`) nicht
    ueber Zeilengrenzen zusammengeklebt werden.
    """
    # [^:*]* erlaubt zusätzlichen Text wie "(Mandant / Auftraggeberin)" vor dem :**
    pattern = rf"-\s+\*\*{re.escape(feldname)}[^:*]*[:\*]+[ \t]*([^\n]*)"
    match = re.search(pattern, abschnitt_text)
    if not match:
        return ""
    wert = match.group(1).strip()
    # Leere Platzhalter oder Template-Reste ignorieren
    if wert in ("", "-", "–", "n/a", "N/A", "tbd", "TBD"):
        return ""
    # Falls der Wert selbst ein Template-Platzhalter ist (z.B. "**Feld:**"),
    # auch zurueckweisen
    if wert.startswith("**") and wert.endswith(":**"):
        return ""
    return wert


def extrahiere_erste_inhaltliche_zeile(abschnitt_text: str) -> str:
    """
    Gibt die erste nicht-leere, nicht-formatierte Zeile eines Abschnitts zurück.
    Nützlich für Freitext-Abschnitte (z. B. Risiken).
    """
    for zeile in abschnitt_text.splitlines():
        zeile = zeile.strip()
        # Überschriften, leere Zeilen, Trennlinien überspringen
        if not zeile or zeile.startswith("#") or zeile.startswith("---"):
            continue
        # Markdown-Formatierung entfernen
        zeile = re.sub(r"\*+", "", zeile)
        zeile = re.sub(r"^[-–•]\s*", "", zeile)
        if zeile:
            return zeile[:200]  # Max. 200 Zeichen für CSV-Lesbarkeit
    return ""


def parse_analyse_datei(md_pfad: Path) -> dict:
    """
    Liest eine Vertragsanalyse-.md-Datei und extrahiert alle CSV-Felder.
    Gibt ein Dict zurück; fehlende Felder sind leere Strings.
    """
    try:
        text = md_pfad.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "quelldatei": md_pfad.name,
            "fehler": str(e),
        }

    abschnitt1 = extrahiere_abschnitt(text, 1)
    abschnitt2 = extrahiere_abschnitt(text, 2)
    abschnitt3 = extrahiere_abschnitt(text, 3)
    abschnitt5 = extrahiere_abschnitt(text, 5)

    partei_a = extrahiere_listenfeld(abschnitt1, "Partei A")
    partei_b = extrahiere_listenfeld(abschnitt1, "Partei B")
    status   = extrahiere_header_feld(text, "Status")

    # Wenn beide Parteien leer sind, liegt ein unbefuelltes Template vor.
    # Status ueberschreiben, damit diese Eintraege in Reports klar erkennbar sind.
    if not partei_a and not partei_b:
        status = "Unvollstaendig (Template leer)"

    return {
        "quelldatei":          md_pfad.name,
        "analysedatum":        extrahiere_header_feld(text, "Analysedatum"),
        "status":              status,
        "partei_a":            partei_a,
        "partei_b":            partei_b,
        "vertragstyp":         extrahiere_listenfeld(abschnitt2, "Vertragstyp (BGB-Systematik)"),
        "leistungsgegenstand": extrahiere_listenfeld(abschnitt2, "Leistungsgegenstand"),
        "verguetung":          extrahiere_listenfeld(abschnitt2, "Vergütung / Vertragswert"),
        "vertragsbeginn":      extrahiere_listenfeld(abschnitt3, "Vertragsbeginn"),
        "vertragsende":        extrahiere_listenfeld(abschnitt3, "Vertragsende / Laufzeit"),
        "kuendigungsfrist":    extrahiere_listenfeld(abschnitt3, "Ordentliche Kündigungsfrist"),
        "risiko_notiz":        extrahiere_erste_inhaltliche_zeile(abschnitt5),
        "letzte_aktualisierung": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "fehler":              "",
    }


# ---------------------------------------------------------------------------
# Hauptlogik
# ---------------------------------------------------------------------------

CSV_SPALTEN = [
    "id",
    "quelldatei",
    "analysedatum",
    "status",
    "partei_a",
    "partei_b",
    "vertragstyp",
    "leistungsgegenstand",
    "verguetung",
    "vertragsbeginn",
    "vertragsende",
    "kuendigungsfrist",
    "risiko_notiz",
    "letzte_aktualisierung",
    "fehler",
]


def schreibe_csv(datensaetze: list, output_pfad: Path):
    with open(output_pfad, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=CSV_SPALTEN,
            extrasaction="ignore",
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        for i, ds in enumerate(datensaetze, 1):
            ds["id"] = i
            writer.writerow(ds)


def drucke_vorschau(datensaetze: list):
    """Gibt eine lesbare Tabellen-Vorschau im Terminal aus."""
    if not datensaetze:
        print("  (keine Datensätze)")
        return

    # Spaltenbreiten berechnen
    felder = ["id", "quelldatei", "partei_a", "partei_b", "vertragstyp",
              "vertragsbeginn", "vertragsende", "status"]
    breiten = {f: len(f) for f in felder}
    for i, ds in enumerate(datensaetze, 1):
        ds_mit_id = {"id": str(i), **ds}
        for f in felder:
            breiten[f] = max(breiten[f], len(str(ds_mit_id.get(f, ""))[:40]))

    # Header
    header = "  ".join(f.ljust(breiten[f]) for f in felder)
    trenn = "  ".join("-" * breiten[f] for f in felder)
    print(header)
    print(trenn)

    for i, ds in enumerate(datensaetze, 1):
        ds_mit_id = {"id": str(i), **ds}
        zeile = "  ".join(
            str(ds_mit_id.get(f, ""))[:breiten[f]].ljust(breiten[f])
            for f in felder
        )
        print(zeile)


def aktualisiere_db(source_dir: Path, output_pfad: Path = None, alle: bool = False) -> int:
    """
    Importierbare Kernfunktion: Liest alle vertragsanalyse_*.md aus source_dir,
    schreibt/aktualisiert CSV. Gibt Anzahl der geschriebenen Einträge zurück.
    Überspringt standardmäßig unvollständige Einträge (leere Parteien).
    """
    if output_pfad is None:
        output_pfad = Path(__file__).parent.parent / "output" / "vertrags_datenbank.csv"

    alle_md = sorted(source_dir.glob("vertragsanalyse_*.md"))
    seen: dict = {}
    for md in reversed(alle_md):
        basis = re.sub(r"_\d{8}_\d{6}\.md$", "", md.name)
        if basis not in seen:
            seen[basis] = md
    md_dateien = sorted(seen.values(), key=lambda p: p.name)

    datensaetze = [parse_analyse_datei(md) for md in md_dateien]

    if not alle:
        vollstaendig = [ds for ds in datensaetze if ds.get("partei_a") or ds.get("partei_b")]
        unvollstaendig = [ds for ds in datensaetze if not ds.get("partei_a") and not ds.get("partei_b")]
        if unvollstaendig:
            print(f"DB aktualisiert: {len(vollstaendig)} vollständige Einträge geschrieben, "
                  f"{len(unvollstaendig)} unvollständige übersprungen.")
        datensaetze = vollstaendig

    output_pfad.parent.mkdir(parents=True, exist_ok=True)
    schreibe_csv(datensaetze, output_pfad)
    return len(datensaetze)


def main():
    parser = argparse.ArgumentParser(
        description="Vertrags-Datenbank: Extrahiert Felder aus Analyse-MDs in .tmp/"
    )
    parser.add_argument(
        "--preview", action="store_true",
        help="Nur Vorschau ausgeben, keine CSV schreiben"
    )
    parser.add_argument(
        "--output", default="output/vertrags_datenbank.csv",
        help="Pfad zur Ausgabe-CSV (Standard: output/vertrags_datenbank.csv)"
    )
    parser.add_argument(
        "--tmp", default=".tmp",
        help="Ordner mit den Analyse-Markdown-Dateien (Standard: .tmp/)"
    )
    parser.add_argument(
        "--alle", action="store_true",
        help="Auch unvollständige Einträge (leere Templates) schreiben (für Debugging)"
    )
    args = parser.parse_args()

    tmp_dir = Path(args.tmp)
    if not tmp_dir.exists():
        print(f"Fehler: Ordner nicht gefunden: {tmp_dir}")
        sys.exit(1)

    # Alle Analyse-Dateien finden; Duplikate (gleicher Basisname) → nur neueste
    alle_md = sorted(tmp_dir.glob("vertragsanalyse_*.md"))
    seen: dict = {}
    for md in reversed(alle_md):
        basis = re.sub(r"_\d{8}_\d{6}\.md$", "", md.name)
        if basis not in seen:
            seen[basis] = md
    md_dateien = sorted(seen.values(), key=lambda p: p.name)

    print(f"\nVertrags-Datenbank Builder")
    print(f"{'=' * 40}")
    print(f"Eingabe-Ordner:  {tmp_dir.resolve()}")
    print(f"Gefundene Dateien: {len(alle_md)} (nach Deduplizierung: {len(md_dateien)})")

    if not md_dateien:
        print("\nKeine vertragsanalyse_*.md-Dateien gefunden.")
        print("Führe erst einen Analyse-Lauf durch:")
        print("  python tools/vertragsanalyse.py vertrag.pdf")
        print("  python tools/batch_vertragsanalyse.py ./ordner/")
        # Leere CSV mit nur Header schreiben
        if not args.preview:
            output_pfad = Path(args.output)
            output_pfad.parent.mkdir(parents=True, exist_ok=True)
            schreibe_csv([], output_pfad)
            print(f"\nLeere Datenbank erstellt: {output_pfad}")
        sys.exit(0)

    # Alle Dateien parsen
    print(f"\nVerarbeite Dateien...")
    datensaetze = []
    fehler_count = 0

    for md in md_dateien:
        ds = parse_analyse_datei(md)
        datensaetze.append(ds)
        status_icon = "✗" if ds.get("fehler") else "✓"
        if ds.get("fehler"):
            fehler_count += 1
            print(f"  {status_icon} {md.name} — FEHLER: {ds['fehler']}")
        else:
            print(f"  {status_icon} {md.name} — {ds.get('vertragstyp') or 'Typ unbekannt'}")

    # Vorschau ausgeben
    print(f"\n{'=' * 40}")
    print(f"Vorschau ({len(datensaetze)} Einträge):\n")
    drucke_vorschau(datensaetze)

    # Unvollständige Einträge herausfiltern (außer bei --alle)
    if not args.alle:
        vollstaendig = [ds for ds in datensaetze if ds.get("partei_a") or ds.get("partei_b")]
        unvollstaendig_count = len(datensaetze) - len(vollstaendig)
        datensaetze = vollstaendig
        if unvollstaendig_count:
            print(f"\nHinweis: {unvollstaendig_count} unvollständige Einträge übersprungen "
                  f"(leere Templates / --no-ki Läufe). Mit --alle einschließen.")
    else:
        print(f"\nModus --alle: Schreibe auch unvollständige Einträge.")

    if args.preview:
        print(f"\n[Vorschau-Modus: Keine CSV geschrieben]")
        print(f"Zum Schreiben: python tools/vertrags_datenbank.py")
        return

    # CSV schreiben
    output_pfad = Path(args.output)
    output_pfad.parent.mkdir(parents=True, exist_ok=True)
    schreibe_csv(datensaetze, output_pfad)

    print(f"\n{'=' * 40}")
    print(f"CSV geschrieben: {output_pfad.resolve()}")
    print(f"  Einträge:    {len(datensaetze)}")
    print(f"  Fehler:      {fehler_count}")
    print(f"  Spalten:     {len(CSV_SPALTEN)}")
    if fehler_count == 0:
        print(f"\nNächster Schritt:")
        print(f"  Öffne {output_pfad} in Excel / Google Sheets")
        print(f"  Oder importiere in Google Sheets via Stufe 4")


if __name__ == "__main__":
    main()
