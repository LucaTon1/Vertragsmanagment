# Claude Code Prompt – Stufe 3: Vertrags-Datenbank (CSV)

Kopiere alles ab der Trennlinie und füge es in Claude Code ein.

---

Ich erweitere meinen Vertragsmanagement-Workflow um eine persistente
Vertrags-Datenbank als CSV. Das Projekt hat aktuell diese Struktur:

```
tools/
  utils.py                  ← gemeinsame Hilfsfunktionen
  vertragsanalyse.py        ← Einzelanalyse
  batch_vertragsanalyse.py  ← Batch-Verarbeitung
  fristen_extraktor.py      ← Regex-Fristen-Erkennung
workflows/
  vertragsmanagement_workflow.md
.tmp/
  test_vertraege/           ← 4 Test-PDFs
```

Führe folgende Schritte der Reihe nach aus:

---

## Schritt 1: Workflow-SOP erweitern

Ergänze `workflows/vertragsmanagement_workflow.md` am Ende:

```
---

## Vertrags-Datenbank (CSV)

### Zweck
Persistente Übersicht aller je analysierten Verträge.
Wächst mit jedem Batch-Run. Kann in Excel/Numbers geöffnet werden.

### Speicherort
datenbank/vertraege.csv  ← nie löschen, kumulativ

### Spalten
Automatisch befüllt:
  dateiname, analysedatum, seiten, zeichen,
  fristen_anzahl, fristen_liste, analyse_pfad, status

Manuell zu befüllen (nach Analyse):
  partei_a, partei_b, vertragstyp,
  laufzeit_info, kuendigungsfrist_info, risiken_notiz

### Verwendung
Wird automatisch von batch_vertragsanalyse.py befüllt.
Manueller Export: python tools/vertrags_datenbank.py --preview
```

---

## Schritt 2: Ordner und Datenbank-Tool erstellen

Hinweis: Das Tool existiert bereits als `tools/vertrags_datenbank.py`. Schritt 2 ist damit erledigt. Starte direkt mit Schritt 3 (Integration in batch_vertragsanalyse.py) oder Schritt 4 (Test).

```python
#!/usr/bin/env python3
"""
Vertrags-Datenbank – Persistente CSV-Datenbank aller analysierten Verträge.

Wird automatisch von batch_vertragsanalyse.py aufgerufen.
Kann auch manuell verwendet werden:

Usage:
    python tools/datenbank.py --liste          Alle Einträge anzeigen
    python tools/datenbank.py --export         CSV-Pfad ausgeben
    python tools/datenbank.py --stats          Statistiken anzeigen
"""

import sys
import csv
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import PROJECT_ROOT

DB_PFAD = PROJECT_ROOT / "datenbank" / "vertraege.csv"

SPALTEN = [
    # Automatisch befüllt
    "dateiname",
    "analysedatum",
    "seiten",
    "zeichen",
    "fristen_anzahl",
    "fristen_liste",       # Pipe-getrennt: "01.07.2026|6 Monate|..."
    "analyse_pfad",
    "status",              # Neu | In Bearbeitung | Abgeschlossen
    # Manuell zu befüllen
    "partei_a",
    "partei_b",
    "vertragstyp",
    "laufzeit_info",
    "kuendigungsfrist_info",
    "risiken_notiz",
]


def lade_datenbank() -> list:
    """Lädt alle existierenden Einträge aus der CSV."""
    if not DB_PFAD.exists():
        return []
    with open(DB_PFAD, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def speichere_datenbank(eintraege: list):
    """Schreibt alle Einträge in die CSV."""
    DB_PFAD.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_PFAD, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SPALTEN)
        writer.writeheader()
        for eintrag in eintraege:
            # Fehlende Spalten mit leerem String auffüllen
            zeile = {k: eintrag.get(k, "") for k in SPALTEN}
            writer.writerow(zeile)


def upsert(neuer_eintrag: dict):
    """
    Fügt einen Eintrag ein oder aktualisiert ihn (anhand dateiname).
    Automatisch befüllte Felder werden immer überschrieben.
    Manuell befüllte Felder (partei_a, etc.) bleiben erhalten.
    """
    eintraege = lade_datenbank()
    manuelle_felder = ["partei_a", "partei_b", "vertragstyp",
                       "laufzeit_info", "kuendigungsfrist_info", "risiken_notiz"]

    for i, eintrag in enumerate(eintraege):
        if eintrag.get("dateiname") == neuer_eintrag.get("dateiname"):
            # Vorhandenen Eintrag aktualisieren – manuelle Felder behalten
            for feld in manuelle_felder:
                if eintrag.get(feld):
                    neuer_eintrag[feld] = eintrag[feld]
            eintraege[i] = neuer_eintrag
            speichere_datenbank(eintraege)
            return "aktualisiert"

    # Neu einfügen
    eintraege.append(neuer_eintrag)
    speichere_datenbank(eintraege)
    return "neu"


def erstelle_eintrag(dateiname: str, seiten: int, zeichen: int,
                     fristen: list, analyse_pfad: str) -> dict:
    """Erstellt einen neuen Datenbank-Eintrag aus Analyse-Daten."""
    fristen_liste = "|".join(t["match"] for t in fristen)
    return {
        "dateiname":     dateiname,
        "analysedatum":  datetime.now().strftime("%Y-%m-%d %H:%M"),
        "seiten":        str(seiten),
        "zeichen":       str(zeichen),
        "fristen_anzahl":str(len(fristen)),
        "fristen_liste": fristen_liste,
        "analyse_pfad":  analyse_pfad,
        "status":        "Neu",
        "partei_a":      "",
        "partei_b":      "",
        "vertragstyp":   "",
        "laufzeit_info": "",
        "kuendigungsfrist_info": "",
        "risiken_notiz": "",
    }


def zeige_liste():
    """Gibt alle Einträge als formatierte Tabelle aus."""
    eintraege = lade_datenbank()
    if not eintraege:
        print("Datenbank ist leer.")
        return

    print(f"\n{'─' * 70}")
    print(f"Vertrags-Datenbank  ({len(eintraege)} Einträge)")
    print(f"{'─' * 70}")
    print(f"{'Dateiname':<35} {'Datum':<12} {'Seiten':>6} {'Fristen':>7} {'Status':<15}")
    print(f"{'─' * 70}")
    for e in eintraege:
        print(f"{e['dateiname']:<35} {e['analysedatum'][:10]:<12} "
              f"{e['seiten']:>6} {e['fristen_anzahl']:>7} {e['status']:<15}")
    print(f"{'─' * 70}\n")


def zeige_stats():
    """Gibt Statistiken über die Datenbank aus."""
    eintraege = lade_datenbank()
    if not eintraege:
        print("Datenbank ist leer.")
        return

    gesamt_fristen = sum(int(e.get("fristen_anzahl", 0)) for e in eintraege)
    status_zaehler: dict = {}
    for e in eintraege:
        s = e.get("status", "Unbekannt")
        status_zaehler[s] = status_zaehler.get(s, 0) + 1

    print(f"\nDatenbank-Statistiken")
    print(f"  Verträge gesamt:       {len(eintraege)}")
    print(f"  Fristen gesamt:        {gesamt_fristen}")
    print(f"  Ø Fristen pro Vertrag: {gesamt_fristen / len(eintraege):.1f}")
    print(f"  Status-Verteilung:")
    for status, anzahl in sorted(status_zaehler.items()):
        print(f"    {status}: {anzahl}")
    print(f"  Datei: {DB_PFAD}\n")


def main():
    if "--liste" in sys.argv or len(sys.argv) == 1:
        zeige_liste()
    elif "--stats" in sys.argv:
        zeige_stats()
    elif "--export" in sys.argv:
        print(str(DB_PFAD))
    else:
        print("Verwendung:")
        print("  python tools/datenbank.py --liste")
        print("  python tools/datenbank.py --stats")
        print("  python tools/datenbank.py --export")


if __name__ == "__main__":
    main()
```

---

## Schritt 3: Datenbank-Integration in batch_vertragsanalyse.py

Ergänze den Import am Anfang von `tools/batch_vertragsanalyse.py`:

```python
from datenbank import erstelle_eintrag, upsert
```

Erweitere dann die Funktion `verarbeite_pdf()` direkt nach dem erfolgreichen
Schreiben der Analyse-Datei (nach `ergebnis["output_pfad"] = str(output_pfad)`):

```python
# Datenbank-Eintrag erstellen
fristen_liste = extrahiere_fristen(rohtext)
db_eintrag = erstelle_eintrag(
    dateiname=pdf_path.name,
    seiten=seiten,
    zeichen=len(rohtext),
    fristen=fristen_liste,
    analyse_pfad=str(output_pfad),
)
db_status = upsert(db_eintrag)
ergebnis["db_status"] = db_status
```

Ergänze außerdem die Terminal-Ausgabe in `verarbeite_pdf()`:

```python
print(f"      OK – {seiten} Seiten | {len(rohtext)} Zeichen | "
      f"{ergebnis['fristen']} Fristen | DB: {db_status} → {output_pfad.name}")
```

---

## Schritt 4: Test

Führe aus:
```
python tools/batch_vertragsanalyse.py .tmp/test_vertraege/
python tools/datenbank.py --liste
python tools/datenbank.py --stats
```

Zeige mir:
1. Den Terminal-Output des Batch-Runs (mit DB-Status pro PDF)
2. Die Ausgabe von `--liste` (Tabellenübersicht)
3. Die Ausgabe von `--stats`
4. Den rohen Inhalt von `datenbank/vertraege.csv`

---

## Schritt 5: Zweiten Batch-Run testen (Upsert-Logik prüfen)

Führe den Batch nochmal aus:
```
python tools/batch_vertragsanalyse.py .tmp/test_vertraege/
python tools/datenbank.py --liste
```

Die Datenbank soll immer noch 4 Einträge haben (nicht 8).
Zeige mir die Ausgabe von `--liste` nach dem zweiten Run.
