# Claude Code Prompt – Vertragsmanagement v2: Bugfixes, Streamlit UI & Fristen-Reminder

## Kontext & Auftrag

Du arbeitest am Projekt `vertragsmanagement/` unter dem WAT-Framework (Workflows → Agent → Tools).

**Lies zuerst `CLAUDE.md` in diesem Ordner** – sie beschreibt Framework, Ordnerstruktur und alle verfügbaren Tools vollständig. Lese danach `output/QA_REVIEW_saas_vertrag_20260417.md` für den letzten Teststatus.

**Arbeitsweise (ZWINGEND):**
- Nach jedem implementierten Schritt: zugehörigen Verifikationsbefehl ausführen
- Bei Fehler: Stacktrace lesen → ursächlich fixen → erneut testen → erst dann weiter
- Niemals einen Schritt als „erledigt" markieren, ohne den Verifikationsbefehl erfolgreich ausgeführt zu haben
- Am Ende jeder Phase: kurze Zusammenfassung was gemacht wurde und ob alle Tests grün sind

---

## Phase 1 – Bugfixes (kein neues Feature, nur Korrekturen)

### 1.1 Prompt Caching für Haiku 4.5 reparieren

**Symptom:** `output/token_log.csv` zeigt für alle Haiku-Runs `cache_write_tokens=0` und `cache_read_tokens=0`. Für Sonnet 4.6 funktioniert Caching korrekt (Beleg: `cache_write=2630` in Run 4 des Logs).

**Ursache analysieren:**
Öffne `tools/ki_analyse.py` und prüfe die aktuelle Caching-Implementierung.
Dann prüfe in der Anthropic-Dokumentation (oder im Quellcode der `anthropic`-Library), ob `claude-haiku-4-5-20251001` Prompt Caching unterstützt und welches Mindest-Token-Limit gilt (Haiku: 2048 Tokens, Sonnet: 1024 Tokens).

Führe diesen Diagnose-Befehl aus, um die System-Prompt-Länge zu messen:
```bash
cd ~/Documents/CLAUDE/Projects/vertragsmanagement
python3 -c "
from tools.ki_analyse import SYSTEM_PROMPT
# Grobe Token-Schätzung: Anthropic ~4 Zeichen pro Token
zeichen = len(SYSTEM_PROMPT)
est_tokens = zeichen // 4
print(f'System-Prompt: {zeichen} Zeichen ≈ {est_tokens} Tokens (geschätzt)')
print(f'Haiku-Minimum: 2048 Tokens')
print(f'Ausreichend für Haiku-Caching: {\"JA\" if est_tokens >= 2048 else \"NEIN – zu kurz\"}')
"
```

**Fix je nach Diagnose:**

*Fall A – System-Prompt unterschreitet 2048 Tokens:*
Ergänze `prompts/KI_SYSTEM_PROMPT.md` am Ende mit einem Abschnitt `## Analyse-Referenz` der typische deutsche Vertragsklauseln, BGB-Paragraphen und Standardformulierungen als Referenzmaterial enthält – inhaltlich korrekt und nützlich, kein Padding. Ziel: sicherstellen, dass der Prompt dauerhaft über 2048 Tokens liegt (Puffer: mindestens 2400 Tokens).

*Fall B – System-Prompt ist ausreichend lang, aber Haiku-Modell unterstützt kein Caching:*
Ergänze in `tools/ki_analyse.py` die Preistabelle `PREISE` um ein Flag `"caching_supported": True/False` pro Modell. In `analysiere_vertrag()`: Wenn `caching_supported=False` für das gewählte Modell, übergib den System-Prompt ohne `cache_control`-Block (normales `{"type": "text", "text": SYSTEM_PROMPT}`). Gib beim Start einen Hinweis aus: `Hinweis: Prompt Caching für [Modell] nicht verfügbar.`

*Fall C – Code-Fehler (z.B. falscher Key-Name im usage-Objekt):*
Prüfe ob `message.usage.cache_creation_input_tokens` für Haiku einen anderen Attributnamen hat. Fixe die Zuordnung in `analysiere_vertrag()` entsprechend.

**Verifikation:**
```bash
# Einen Mini-Test ohne echten API-Call machen: prüfe ob SYSTEM_PROMPT korrekt geladen wird
python3 -c "from tools.ki_analyse import SYSTEM_PROMPT; print('OK, Länge:', len(SYSTEM_PROMPT))"
# Bei echtem API-Key: prüfe nach einem Haiku-Run ob cache_write_tokens > 0 im token_log
```

---

### 1.2 vertrags_datenbank.py – Unvollständige Einträge filtern

**Symptom:** `output/vertrags_datenbank.csv` enthält 4 Einträge mit Status `"Unvollstaendig (Template leer)"` und leeren Feldern. Diese entstehen durch `--no-ki`-Läufe oder abgebrochene Runs.

**Analyse:** Öffne `tools/vertrags_datenbank.py` und prüfe die aktuelle Logik in `parse_analyse_datei()` und `aktualisiere_db()`.

**Fix:**
Ergänze in `aktualisiere_db()` nach dem Parsen eine Filterlogik:
```python
# Vollständige und unvollständige Einträge trennen
vollstaendig = [ds for ds in datensaetze if ds.get("partei_a") or ds.get("partei_b")]
unvollstaendig = [ds for ds in datensaetze if not ds.get("partei_a") and not ds.get("partei_b")]
```
Schreibe **nur `vollstaendig`** in die CSV. Gib am Ende eine Zeile aus:
```
DB aktualisiert: 3 vollständige Einträge geschrieben, 4 unvollständige übersprungen.
```

Ergänze außerdem einen optionalen CLI-Flag `--alle` in `main()`, der auch unvollständige Einträge schreibt (für Debugging):
```bash
python tools/vertrags_datenbank.py --alle   # schreibt alles inkl. leerer Templates
python tools/vertrags_datenbank.py          # Standard: nur vollständige Einträge
```

**Verifikation:**
```bash
cd ~/Documents/CLAUDE/Projects/vertragsmanagement
python3 tools/vertrags_datenbank.py --tmp .tmp/
# Erwartetes Ergebnis: "3 vollständige Einträge geschrieben, 4 übersprungen"
# CSV prüfen:
python3 -c "
import csv
with open('output/vertrags_datenbank.csv') as f:
    rows = list(csv.DictReader(f))
print(f'{len(rows)} Einträge in CSV')
for r in rows:
    print(f'  {r[\"quelldatei\"][:50]} | {r[\"status\"]}')
"
```

---

## Phase 2 – Streamlit UI

**Zieldatei:** `tools/app.py`

**Zweck:** Das CLI-Tool in eine browserbasierte Anwendung verwandeln, die ein nicht-technischer Kunde nutzen kann. Kein Overengineering – nur was nötig ist, um das Produkt demonstrierbar zu machen.

### Setup prüfen

```bash
pip install streamlit --break-system-packages 2>/dev/null || pip install streamlit
streamlit --version
```

### Implementierung

Erstelle `tools/app.py` mit folgender Struktur:

```
Sidebar:
  - Logo-Text "⚖️ Vertragsmanagement"
  - Navigation: ["📤 Analyse", "📋 Datenbank", "💰 Kosten"]

Seite 1 – Analyse (Standard):
  - Titel: "Vertrag analysieren"
  - File-Uploader: akzeptiert .pdf, einzelne Datei
  - Modell-Auswahl: Selectbox ["Haiku 4.5 – schnell (~0,05 $)", "Sonnet 4.6 – präzise (~0,15 $)"]
  - Button: "Analysieren"
  - Bei Klick:
    1. PDF in .tmp/ speichern
    2. Statusmeldung: "⏳ Analyse läuft..."
    3. pipeline.py-Logik aufrufen (import, kein subprocess)
    4. HTML-Report in st.components.v1.html() einbetten (height=800)
    5. Download-Button: HTML-Report herunterladen
    6. Kosten-Anzeige: "Analyse abgeschlossen | Kosten: ~$X.XX | Modell: ..."

Seite 2 – Datenbank:
  - Liest output/vertrags_datenbank.csv
  - Zeigt Tabelle mit st.dataframe() (vollständige Einträge)
  - Filter-Dropdown: nach Vertragstyp
  - Metriken oben: "Verträge gesamt | Abgeschlossen | Dieses Monat"
  - Wenn CSV leer: "Noch keine Verträge analysiert. Gehe zu 📤 Analyse."

Seite 3 – Kosten:
  - Liest output/token_log.csv
  - Zeigt Tabelle aller API-Calls
  - Metric-Box: "Gesamtkosten USD | Analysierte Verträge | Ø pro Vertrag"
  - Linechart: Kosten pro Analyse über Zeit (st.line_chart)
```

**Fehlerbehandlung:**
- Kein API-Key → klare Fehlermeldung mit Link zu console.anthropic.com
- Upload eines Nicht-PDFs → Fehlermeldung
- Leere Datenbank → leerer State mit Hinweis (kein Absturz)
- Pipeline-Fehler → `st.error(str(e))` mit vollständigem Traceback

**Start-Kommando** am Ende von `app.py` in einen Kommentar schreiben:
```python
# Starten mit: streamlit run tools/app.py --server.headless true
```

**Verifikation:**
```bash
cd ~/Documents/CLAUDE/Projects/vertragsmanagement
# Syntax-Check (kein streamlit-Start nötig für Syntax)
python3 -c "import ast; ast.parse(open('tools/app.py').read()); print('Syntax OK')"
# Imports prüfen
python3 -c "
import sys; sys.path.insert(0, 'tools')
# Prüfe ob alle imports ohne Fehler laden (außer streamlit selbst)
print('Import-Check läuft...')
from vertrags_datenbank import aktualisiere_db
from generate_report import generiere_report
print('Core imports: OK')
"
```

Dann einmal manuell starten und prüfen ob die UI lädt:
```bash
streamlit run tools/app.py --server.headless true &
sleep 3
curl -s http://localhost:8501 | head -5
# Erwartung: HTML-Response (kein Fehler)
kill %1
```

---

## Phase 3 – Fristen-Reminder

**Neue Datei:** `tools/fristen_reminder.py`

**Zweck:** Liest `output/vertrags_datenbank.csv`, berechnet welche Fristen in den nächsten 90/30/7 Tagen ablaufen und sendet E-Mail-Benachrichtigungen via SMTP.

### Implementierung

```python
#!/usr/bin/env python3
"""
Fristen-Reminder – prüft Vertrags-DB auf ablaufende Fristen und sendet E-Mails.

Usage:
    python tools/fristen_reminder.py --check      # Nur anzeigen, keine Mail
    python tools/fristen_reminder.py --send        # Mails senden
    python tools/fristen_reminder.py --dry-run     # Simulieren (Mails ausgeben, nicht senden)
"""
```

**Logik:**

1. **Datums-Parsing:** Versuche für jede Zeile in der CSV die Felder `vertragsende`, `kuendigungsfrist` auf absolute Datumsangaben zu parsen (Formate: `DD.MM.YYYY`, `YYYY-MM-DD`, `DD. Monat YYYY`). Nutze `dateutil.parser.parse()` mit Fallback auf Regex.

2. **Fristen-Kategorien:**
   ```
   KRITISCH  (≤  7 Tage):  Betreff-Präfix "[KRITISCH]"
   DRINGEND  (≤ 30 Tage):  Betreff-Präfix "[DRINGEND]"
   HINWEIS   (≤ 90 Tage):  Betreff-Präfix "[HINWEIS]"
   ```

3. **E-Mail-Konfiguration** aus `.env` lesen:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=deine@email.de
   SMTP_PASSWORD=app-passwort
   REMINDER_TO=empfaenger@email.de
   ```
   Wenn SMTP-Vars nicht gesetzt: `--send` gibt Warnung aus und fällt auf `--dry-run` zurück.

4. **E-Mail-Format** (plain text, kein HTML):
   ```
   Betreff: [DRINGEND] Kündigungsfrist läuft ab: Mietvertrag (Muster GmbH / Schmidt KG)
   
   Vertragsmanagement – Automatische Erinnerung
   ─────────────────────────────────────────────
   Vertrag:        Mietvertrag
   Parteien:       Muster GmbH / Schmidt KG
   Frist läuft ab: 15.05.2026 (in 12 Tagen)
   Fristtyp:       Ordentliche Kündigungsfrist
   
   Handlung erforderlich: Kündigung muss bis 15.05.2026 zugehen.
   
   Quelldatei: vertragsanalyse_mietvertrag_20260416.md
   ─────────────────────────────────────────────
   Automatisch generiert von Vertragsmanagement v2.0
   ```

5. **Standalone + importierbar:**
   ```python
   def pruefe_fristen(db_pfad: Path = None) -> list[dict]:
       """Gibt Liste aller ablaufenden Fristen zurück (für Streamlit-Integration)."""
   
   def sende_reminder(frist: dict, dry_run: bool = False) -> bool:
       """Sendet eine Reminder-E-Mail. Bei dry_run: nur ausgeben."""
   ```

6. **Streamlit-Integration vorbereiten:** In `tools/app.py` auf Seite 2 (Datenbank) eine Section `🔔 Ablaufende Fristen` ergänzen, die `pruefe_fristen()` aufruft und Fristen farblich hervorhebt (rot = kritisch, orange = dringend, gelb = hinweis). Diese Integration erst implementieren, nachdem `fristen_reminder.py` funktioniert.

**Verifikation:**
```bash
cd ~/Documents/CLAUDE/Projects/vertragsmanagement
# Dependency prüfen
python3 -c "import dateutil; print('dateutil OK')" 2>/dev/null || pip install python-dateutil --break-system-packages

# Dry-Run mit vorhandener DB
python3 tools/fristen_reminder.py --check
# Erwartung: Tabelle mit erkannten Fristen ODER "Keine ablaufenden Fristen in den nächsten 90 Tagen."
# Kein Absturz, kein Fehler

# Syntax-Check
python3 -c "import ast; ast.parse(open('tools/fristen_reminder.py').read()); print('Syntax OK')"
```

---

## Phase 4 – Eigenständige Verbesserungsvorschläge

Nachdem Phasen 1–3 vollständig abgeschlossen und verifiziert sind, analysiere den Codebase eigenständig und implementiere **bis zu 3 weitere Verbesserungen** die du als hochwertig einschätzt.

Kriterien für eine gute Verbesserung:
- Behebt ein reales Problem das du beim Lesen des Codes identifiziert hast
- Erhöht Produktqualität für einen Nicht-Techniker (Fehlertoleranz, Lesbarkeit, UX)
- Ist in < 30 Minuten implementierbar (kein Scope Creep)
- Verstößt nicht gegen bestehende Architektur-Entscheidungen in `CLAUDE.md`

Ausdrücklich erlaubt (Beispiele, keine Pflicht):
- Verbesserte Fehlerausgaben an kritischen Stellen
- Deduplizierungs-Logik in `batch_vertragsanalyse.py` (prüft ob PDF bereits analysiert)
- `check_setup.py` um Streamlit-Check erweitern
- Robusteres Datums-Parsing im fristen_extraktor
- Modell-Empfehlung in der Streamlit-UI basierend auf Vertragslänge

Für jede Verbesserung: kurz begründen warum, dann implementieren, dann verifizieren.

---

## Abschluss

Wenn alle Phasen abgeschlossen sind:

### CLAUDE.md aktualisieren

Ergänze in `CLAUDE.md`:
- Workflow-Tabelle: Eintrag für `tools/app.py` (Streamlit UI)
- Workflow-Tabelle: Eintrag für `tools/fristen_reminder.py`
- Ordnerstruktur: neue Dateien eintragen
- Bekannte Schwachstellen: behobene Bugs als `[gelöst]` markieren

### Abschlussprüfung ausführen

```bash
cd ~/Documents/CLAUDE/Projects/vertragsmanagement

# 1. Setup komplett grün?
python3 tools/check_setup.py

# 2. Datenbank sauber?
python3 tools/vertrags_datenbank.py --tmp .tmp/ --preview

# 3. Fristen-Check läuft?
python3 tools/fristen_reminder.py --check

# 4. Streamlit-Syntax sauber?
python3 -c "import ast; ast.parse(open('tools/app.py').read()); print('app.py Syntax: OK')"

# 5. Pipeline weiterhin funktionsfähig? (ohne KI, gratis)
python3 tools/pipeline.py .tmp/test_vertraege/ --no-ki
```

Gib am Ende einen kurzen Abschlussbericht aus:
- Was wurde in jeder Phase implementiert
- Welche Tests sind grün / rot
- Welche 3 eigenständigen Verbesserungen wurden in Phase 4 umgesetzt und warum
- Nächste empfohlene Schritte (max. 3 Punkte)
