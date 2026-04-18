# Claude Code Prompt – Stufe 2: Automatische Fristen-Extraktion

Kopiere alles ab der Trennlinie und füge es in Claude Code ein.

---

Ich erweitere meinen Vertragsmanagement-Workflow um automatische
Fristen-Erkennung per Regex. Das Projekt hat bereits diese Struktur:

```
workflows/
  vertragsmanagement_workflow.md
tools/
  vertragsanalyse.py
  batch_vertragsanalyse.py
  create_test_batch.py
.tmp/
  test_vertraege/   ← 4 Test-PDFs vorhanden
```

Führe folgende Schritte der Reihe nach aus:

---

## Schritt 1: Workflow-SOP erweitern

Ergänze `workflows/vertragsmanagement_workflow.md` am Ende um:

```
---

## Fristen-Extraktion (automatisch, kein AI nötig)

### Verwendung
python tools/fristen_extraktor.py vertrag.pdf
python tools/fristen_extraktor.py ./vertraege/     ← ganzer Ordner

### Was erkannt wird
- Absolute Daten: 01.05.2026, 1. Juli 2026, Mai 2026
- Relative Fristen: 3 Monate, 30 Tage, 2 Wochen, 6 Monate
- Zahlungsfristen: binnen 14 Tagen, zahlbar monatlich
- Kündigungsfristen: Kündigung mit ... Frist

### Expected Output
- Konsolen-Ausgabe mit allen gefundenen Fristen und Kontext
- .tmp/fristen_[dateiname]_[datum].md mit strukturierter Fristenliste
```

---

## Schritt 2: Fristen-Extraktor erstellen

Erstelle `tools/fristen_extraktor.py`:

```python
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


# ── Regex-Muster ────────────────────────────────────────────────────────────

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
    ],
    "kuendigungsfrist": [
        r"[Kk]ündigung(?:sfrist)?\s+(?:von\s+)?(?:mindestens\s+)?\d+\s+\w+",
        r"[Kk]ündigung\s+(?:mit|unter)\s+\w+\s+\w+\s+Frist",
        r"[Kk]ündigungsfrist[:\s]+\w+",
        r"ordentliche\s+[Kk]ündigung",
        r"außerordentliche\s+[Kk]ündigung",
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


def extrahiere_fristen(text: str) -> list[dict]:
    """
    Sucht alle Fristen-Matches im Text.
    Gibt Liste von Dicts zurück: {kategorie, match, kontext, position}
    """
    treffer = []
    bereits_gefunden = set()  # Duplikate vermeiden

    for kategorie, muster_liste in MUSTER.items():
        for muster in muster_liste:
            for m in re.finditer(muster, text, re.IGNORECASE):
                match_text = m.group(0).strip()
                # Duplikate überspringen (gleicher Text, gleiche Position ±10 Zeichen)
                key = (match_text.lower(), m.start() // 10)
                if key in bereits_gefunden:
                    continue
                bereits_gefunden.add(key)

                kontext = extrahiere_kontext(text, m.start(), m.end())
                treffer.append({
                    "kategorie": kategorie,
                    "match": match_text,
                    "kontext": kontext,
                    "position": m.start(),
                })

    # Nach Position im Dokument sortieren
    treffer.sort(key=lambda x: x["position"])
    return treffer


def kategorien_label(kategorie: str) -> str:
    labels = {
        "absolutes_datum": "Datum",
        "relative_frist": "Frist",
        "zahlungsfrist": "Zahlung",
        "kuendigungsfrist": "Kündigung",
        "laufzeit": "Laufzeit",
    }
    return labels.get(kategorie, kategorie)


def erstelle_fristen_bericht(dateiname: str, treffer: list,
                              rohtext_laenge: int) -> str:
    datum = datetime.now().strftime("%Y-%m-%d")
    
    # Nach Kategorie gruppieren
    gruppen = {}
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

    reihenfolge = ["absolutes_datum", "kuendigungsfrist", "relative_frist",
                   "zahlungsfrist", "laufzeit"]

    for kat in reihenfolge:
        if kat not in gruppen:
            continue
        label = kategorien_label(kat)
        eintraege = gruppen[kat]
        zeilen += [
            f"## {label} ({len(eintraege)} Treffer)",
            f"",
        ]
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

    zeilen += [
        f"---",
        f"",
        f"*Erstellt mit Fristen-Extraktor v1.0 (Regex, kein AI)*",
    ]

    return "\n".join(zeilen)


def verarbeite_datei(pdf_pfad: Path) -> tuple[list, str]:
    """Extrahiert Text und Fristen aus einer PDF. Gibt (treffer, rohtext) zurück."""
    try:
        import pdfplumber
    except ImportError:
        print("Installiere pdfplumber: pip install pdfplumber")
        sys.exit(1)

    text_teile = []
    with pdfplumber.open(str(pdf_pfad)) as pdf:
        for seite in pdf.pages:
            text = seite.extract_text()
            if text:
                text_teile.append(text)

    rohtext = "\n\n".join(text_teile)
    treffer = extrahiere_fristen(rohtext)
    return treffer, rohtext


def main():
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  python tools/fristen_extraktor.py vertrag.pdf")
        print("  python tools/fristen_extraktor.py ./vertraege/")
        sys.exit(1)

    eingabe = Path(sys.argv[1])
    os.makedirs(".tmp", exist_ok=True)

    # Einzelne PDF oder ganzer Ordner?
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
            treffer, rohtext = verarbeite_datei(pdf_pfad)
        except Exception as e:
            print(f"  FEHLER: {e}")
            continue

        gesamt_treffer += len(treffer)

        # Terminal-Ausgabe
        if treffer:
            print(f"  {len(treffer)} Fristen gefunden:")
            for t in treffer:
                label = kategorien_label(t["kategorie"])
                print(f"    [{label}] {t['match']}")
        else:
            print("  Keine Fristen erkannt.")

        # Datei speichern
        datum_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r"[^\w]", "_", pdf_pfad.stem)[:40]
        output_pfad = Path(".tmp") / f"fristen_{slug}_{datum_slug}.md"
        bericht = erstelle_fristen_bericht(
            pdf_pfad.name, treffer, len(rohtext)
        )
        with open(output_pfad, "w", encoding="utf-8") as f:
            f.write(bericht)
        print(f"  Bericht: {output_pfad}")

    print(f"\n{'─' * 50}")
    print(f"Gesamt: {gesamt_treffer} Fristen in {len(pdf_dateien)} Datei(en)")


if __name__ == "__main__":
    main()
```

---

## Schritt 3: Test auf allen 4 Test-Verträgen

Führe aus:
```
python tools/fristen_extraktor.py .tmp/test_vertraege/
```

Zeige mir:
1. Den vollständigen Terminal-Output (alle erkannten Fristen pro Datei)
2. Den Inhalt eines der generierten Fristen-Berichte (z.B. Arbeitsvertrag)

---

## Schritt 4: Integration in Batch-Workflow

Erweitere `tools/batch_vertragsanalyse.py` so, dass nach jeder
erfolgreichen PDF-Verarbeitung automatisch auch der Fristen-Extraktor
aufgerufen wird.

Konkret: In der Funktion `verarbeite_pdf()`, nach dem Schreiben der
Analyse-Datei, füge einen Aufruf an `extrahiere_fristen()` aus
`tools/fristen_extraktor.py` hinzu und ergänze die Fristen-Zusammenfassung
im Analyse-Template unter Abschnitt 3 (Laufzeit & Fristen) mit den
automatisch erkannten Werten als vorausgefüllte Hinweise.

Die Abschnitte sollen so aussehen:
```
## 3. Laufzeit & Fristen

<!-- Automatisch erkannt – bitte prüfen und ergänzen -->
- 01.07.2026 (Datum)
- 6 Monate (Frist)
- 4 Wochen zum Monatsende (Kündigung)
- 12 Monate nach Austritt (Kündigung)

- **Vertragsbeginn:** [manuelle Einordnung]
- **Kündigungsfrist:** [manuelle Einordnung]
...
```

---

## Schritt 5: Abschlusstest

Führe den vollen Batch inklusive Fristen-Extraktion aus:
```
python tools/batch_vertragsanalyse.py .tmp/test_vertraege/
```

Zeige mir eine der fertigen Analyse-Dateien, in der die automatisch
erkannten Fristen bereits unter Abschnitt 3 vorausgefüllt sind.
