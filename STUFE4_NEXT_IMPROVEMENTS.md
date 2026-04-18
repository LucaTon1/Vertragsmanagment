# STUFE 4 – Next Improvements: Vertragsmanagement-System

## Kontext

Du arbeitest am Vertragsmanagement-Projekt unter `CLAUDE/Projects/vertragsmanagement/`.
**Lies zuerst `CLAUDE.md` in diesem Ordner** für die vollständige Projektstruktur und das WAT-Framework.

### Aktueller Stand (Stand: 16.04.2026)

Das Projekt ist voll funktionsfähig mit:
- `tools/vertragsanalyse.py` — Einzelne PDF → KI-Analyse (Haiku 4.5, default) oder leeres Template (--no-ki)
- `tools/batch_vertragsanalyse.py` — Ordner → Batch-Analyse mit --ki Flag
- `tools/ki_analyse.py` — Claude API Modul (Haiku 4.5 + Prompt Caching, 90% Kostenersparnis)
- `tools/generate_report.py` — Markdown-Analyse → professioneller HTML-Report
- `tools/fristen_extraktor.py` — Regex-basierte Fristenerkennung
- `tools/vertrags_datenbank.py` — CSV-Datenbank (`output/vertrags_datenbank.csv`)
- `.env` — enthält `ANTHROPIC_API_KEY`
- `output/` — fertige Analysen und HTML-Reports
- `.tmp/` — temporäre Dateien (jederzeit regenerierbar)

### Bekannte Schwachstellen (to fix)

1. `generate_report.py` verarbeitet nur eine .md-Datei gleichzeitig (CLI-Limitation)
2. Kein End-to-End-Pipeline-Befehl (PDF → Analyse → HTML → Datenbank)
3. `ki_analyse.py` lädt den System-Prompt hardcoded — nicht tunable ohne Code-Änderung
4. Kein Token-/Kosten-Log für langfristiges Spending-Tracking
5. Kein `requirements.txt` + Setup-Check

---

## Aufgaben

### 1. `generate_report.py` — Multi-File & Folder Support

**Zieldatei:** `tools/generate_report.py`

Erweitere `main()` so, dass:

```bash
# Einzelne Datei (wie bisher)
python tools/generate_report.py output/analyse_xyz.md

# Mehrere Dateien
python tools/generate_report.py output/analyse_a.md output/analyse_b.md output/analyse_c.md

# Ganzer Ordner (alle *.md-Dateien darin)
python tools/generate_report.py output/

# Mit explizitem Output-Ordner
python tools/generate_report.py output/ --output output/reports/
```

Logik:
- Wenn das Argument ein Verzeichnis ist: `glob.glob(os.path.join(arg, "*.md"))` 
- Wenn mehrere Argumente: jedes einzeln verarbeiten
- Ausgabe: für jede Datei eine Zeile `✓ output/report_xyz.html`
- Am Ende: `Fertig: N Report(s) erstellt.`
- Fehler bei einzelner Datei überspringen (mit Warnung), Rest weiterlaufen lassen

Verifikation:
```bash
python tools/generate_report.py .tmp/
# Sollte 2 HTML-Reports in output/ erstellen (arbeitsvertrag + dienstleistung)
```

---

### 2. `tools/pipeline.py` — End-to-End-Befehl

**Neue Datei:** `tools/pipeline.py`

Ein einziger Befehl, der die volle Kette ausführt:

```bash
python tools/pipeline.py vertraege/mietvertrag.pdf
python tools/pipeline.py vertraege/          # alle PDFs im Ordner
python tools/pipeline.py vertraege/ --no-ki  # ohne API
```

Pipeline-Schritte (in dieser Reihenfolge, mit Statusausgabe):
```
[1/4] PDF extrahieren & analysieren  →  output/vertragsanalyse_mietvertrag.md
[2/4] HTML-Report generieren         →  output/vertragsanalyse_mietvertrag.html
[3/4] Datenbank aktualisieren        →  output/vertrags_datenbank.csv
[4/4] Abgeschlossen ✓
```

Implementierung:
- Importiere Funktionen aus den bestehenden Tools (nicht subprocess)
- Verwende `from tools.vertragsanalyse import verarbeite_pdf` etc.  
  → Passe ggf. die bestehenden Scripts an, sodass Kernfunktionen importierbar sind (kein `if __name__ == "__main__"` Guard fehlen lassen — bleibt CLI-kompatibel)
- Bei Fehler in einem Schritt: Abbruch + klare Fehlermeldung + Exit Code 1

Update `CLAUDE.md` Workflow-Tabelle:

| Trigger | Workflow-Datei | Tool | Funktion |
|---|---|---|---|
| „Pipeline" | `workflows/vertragsmanagement_workflow.md` | `python3 tools/pipeline.py <PDF-oder-Ordner>` | Vollständige Pipeline: PDF → Analyse → HTML → DB |

---

### 3. `ki_analyse.py` — System-Prompt externalisieren

**Zieldateien:** `tools/ki_analyse.py`, `prompts/KI_SYSTEM_PROMPT.md`

Aktuell ist `SYSTEM_PROMPT` als Python-String direkt in `ki_analyse.py` hartcodiert.

Ändere das so:
```python
# In ki_analyse.py:
def _lade_system_prompt() -> str:
    """Lädt System-Prompt aus prompts/KI_SYSTEM_PROMPT.md (relativ zur tools/-Datei)."""
    base = os.path.dirname(os.path.abspath(__file__))
    prompt_pfad = os.path.join(base, "..", "prompts", "KI_SYSTEM_PROMPT.md")
    with open(prompt_pfad, "r", encoding="utf-8") as f:
        return f.read()

SYSTEM_PROMPT = _lade_system_prompt()
```

Extrahiere den aktuellen System-Prompt-Inhalt vollständig in `prompts/KI_SYSTEM_PROMPT.md`.
Der Prompt-Inhalt soll **identisch** bleiben — nur der Speicherort ändert sich.

Verifikation:
```bash
python -c "from tools.ki_analyse import SYSTEM_PROMPT; print(SYSTEM_PROMPT[:100])"
# Muss die ersten Zeichen des Prompt ausgeben, kein Fehler
```

---

### 4. Token-/Kosten-Log

**Zieldatei:** `tools/ki_analyse.py` (und indirekt alle Aufrufer)

Nach jeder erfolgreichen API-Analyse: Token-Daten an `output/token_log.csv` anhängen.

CSV-Format (Header nur beim ersten Erstellen):
```
timestamp,datei,modell,input_tokens,output_tokens,cache_write_tokens,cache_read_tokens,kosten_usd
2026-04-16T14:32:00,mietvertrag.pdf,claude-haiku-4-5-20251001,1250,892,1250,0,0.0187
```

Implementierung in `ki_analyse.py`:
```python
import csv
from datetime import datetime

def _schreibe_token_log(datei: str, token_info: dict):
    log_pfad = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "token_log.csv")
    header = ["timestamp", "datei", "modell", "input_tokens", "output_tokens",
              "cache_write_tokens", "cache_read_tokens", "kosten_usd"]
    neu = not os.path.exists(log_pfad)
    with open(log_pfad, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if neu:
            writer.writerow(header)
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            datei,
            token_info.get("modell", ""),
            token_info.get("input_tokens", 0),
            token_info.get("output_tokens", 0),
            token_info.get("cache_creation_input_tokens", 0),
            token_info.get("cache_read_input_tokens", 0),
            round(token_info.get("kosten_usd", 0.0), 6),
        ])
```

Rufe `_schreibe_token_log(vertrag_titel, token_info)` am Ende von `analysiere_vertrag()` auf (nach dem Return-Wert aufbereiten, vor dem Return).

Verifikation:
```bash
cat output/token_log.csv
# Muss Header + mindestens eine Zeile zeigen nach dem ersten KI-Aufruf
```

---

### 5. `requirements.txt` + Setup-Check

**Neue Dateien:**
- `requirements.txt` im Projektstamm
- `tools/check_setup.py`

**`requirements.txt`:**
```
anthropic>=0.40.0
pdfplumber>=0.10.0
python-dotenv>=1.0.0
```

**`tools/check_setup.py`:**
```
python tools/check_setup.py
```

Ausgabe (Beispiel):
```
Vertragsmanagement – Setup Check
═══════════════════════════════
[✓] Python 3.9+          (3.12.2)
[✓] anthropic            (0.43.0)
[✓] pdfplumber           (0.10.3)
[✓] python-dotenv        (1.0.1)
[✓] .env vorhanden
[✓] ANTHROPIC_API_KEY gesetzt
[✓] output/ Ordner vorhanden
[✓] prompts/ Ordner vorhanden

Alles bereit. Starte mit:
  python tools/vertragsanalyse.py <PDF>
  python tools/pipeline.py <PDF>
```

Fehlerfall:
```
[✗] anthropic fehlt → pip install anthropic
[✗] .env fehlt      → .env Datei mit ANTHROPIC_API_KEY erstellen
```

Exit Code 0 wenn alles OK, Exit Code 1 wenn etwas fehlt.

---

## Reihenfolge der Umsetzung

1. `generate_report.py` Multi-File (schnell, isoliert, sofort testbar)
2. `requirements.txt` + `check_setup.py` (unabhängig, schnell)
3. System-Prompt externalisieren (refactoring, kein Verhaltenswechsel)
4. Token-Log in `ki_analyse.py` (erfordert API-Aufruf zum Testen)
5. `pipeline.py` (integriert alles, zuletzt)

Nach jedem Schritt: Tool ausführen und Ausgabe prüfen.
Fehler tracen und fixen bevor weitergemacht wird.

---

## Abschlussprüfung

```bash
# 1. Setup prüfen
python tools/check_setup.py

# 2. Multi-File Report
python tools/generate_report.py .tmp/

# 3. Pipeline (ohne KI, da API-Credits nötig)
python tools/pipeline.py .tmp/test_vertraege/ --no-ki

# 4. Struktur prüfen
ls output/
# Erwartet: .md Dateien, .html Reports, vertrags_datenbank.csv, token_log.csv (nach KI-Aufruf)
```

Bei Abschluss `CLAUDE.md` aktualisieren:
- Workflow-Tabelle um Pipeline-Eintrag ergänzen
- Ordnerstruktur um `requirements.txt` und `tools/pipeline.py` und `tools/check_setup.py` ergänzen
