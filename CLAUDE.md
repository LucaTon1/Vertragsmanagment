# CLAUDE.md – Projekt: Vertragsmanagement

Dieses Projekt implementiert das **WAT-Framework** (Workflows → Agent → Tools) für automatisierte Vertragsanalyse.

---

## Projektübersicht

**Zweck:** PDF-Verträge automatisiert analysieren, Fristen extrahieren, Datenbank aufbauen.
**Framework:** WAT — Reasoning (Claude) ist getrennt von Execution (Python-Scripts).
**Warum:** Deterministische Scripts verhindern Fehlerfortpflanzung; 90% Accuracy über 5 Schritte = ~59% Gesamterfolg ohne Scripts.

---

## Betrieb

1. **Vor neuem Script:** prüfen ob `tools/` schon etwas Passendes hat
2. **Bei Fehlern:** Trace lesen → Script fixen → retesten → Learnings in Workflow dokumentieren
3. **Workflows nicht überschreiben** ohne explizite Anweisung — sie sind persistente SOPs
4. `.tmp/` ist flüchtig und jederzeit regenerierbar

```bash
python tools/<script_name>.py
```

---

## Verfügbare Workflows

| Trigger | Workflow-Datei | Tool | Funktion |
|---|---|---|---|
| „Research-Workflow" / „recherchiere [Thema]" | `workflows/research_workflow.md` | `python3 tools/research.py "<Thema>"` | Juristisches & Business-Research, 6 Abschnitte |
| „Vertragsanalyse" | `workflows/vertragsmanagement_workflow.md` | `python3 tools/vertragsanalyse.py <PDF>` | Einzelne PDF → vollständige KI-Analyse (Haiku 4.5) |
| „Vertragsanalyse --no-ki" | `workflows/vertragsmanagement_workflow.md` | `python3 tools/vertragsanalyse.py <PDF> --no-ki` | Einzelne PDF → leeres Template (kein API-Call) |
| „Batch-Vertragsanalyse" | `workflows/vertragsmanagement_workflow.md` | `python3 tools/batch_vertragsanalyse.py <Ordner> --ki` | Alle PDFs in Ordner → vollständige KI-Analysen |
| „Report generieren" | – | `python3 tools/generate_report.py <analyse.md\|ordner/> --output output/` | Markdown-Analyse(n) → professionelle HTML-Reports (Einzel, Mehrfach, Ordner) |
| „Pipeline" | `workflows/vertragsmanagement_workflow.md` | `python3 tools/pipeline.py <PDF-oder-Ordner> [--no-ki]` | Vollständige Pipeline: PDF → Analyse → HTML → DB |
| „Streamlit UI" | – | `python3 -m streamlit run tools/app.py` | Browser-UI: Analyse, Datenbank, Kosten |
| „Fristen-Check" | – | `python3 tools/fristen_reminder.py --check` | Ablaufende Fristen anzeigen |
| „Fristen-Mail" | – | `python3 tools/fristen_reminder.py --send` | Reminder-E-Mails via SMTP senden |

Neue Workflows werden hier eingetragen sobald sie erstellt werden.

---

## Ordnerstruktur

```
vertragsmanagement/
├── CLAUDE.md                        ← diese Datei
├── .env                             ← alle API Keys (einziger Ort)
├── requirements.txt                 ← Python-Abhängigkeiten (pip install -r)
├── tools/                           ← deterministische Python-Scripts
│   ├── pipeline.py                  # Vollständige Pipeline: PDF → Analyse → HTML → DB
│   ├── vertragsanalyse.py           # Einzelne PDF → vollständige KI-Analyse
│   ├── batch_vertragsanalyse.py     # Ordner mit PDFs → Batch-Analyse (--ki Flag)
│   ├── ki_analyse.py                # Claude API Modul (Haiku 4.5 + Prompt Caching)
│   ├── generate_report.py           # Markdown-Analyse(n) → professionelle HTML-Reports
│   ├── fristen_extraktor.py         # Fristen aus Analyse extrahieren (Regex)
│   ├── vertrags_datenbank.py        # CSV-Datenbank aufbauen
│   ├── check_setup.py               # Setup-Check: Pakete, .env, API-Key, Ordner, Streamlit
│   ├── app.py                       # Streamlit Browser-UI (Analyse, DB, Kosten)
│   ├── fristen_reminder.py          # Fristen-Check + E-Mail-Reminder
│   ├── utils.py                     # Shared utilities
│   ├── research.py                  # Research-Template erstellen
│   ├── create_test_pdf.py           # Einen Test-Vertrag als PDF erstellen
│   └── create_test_batch.py         # 4 Test-Verträge für Batch-Tests
├── workflows/                       ← Markdown SOPs
│   ├── vertragsmanagement_workflow.md
│   └── research_workflow.md
├── prompts/                         ← Prompt-Vorlagen
│   ├── KI_SYSTEM_PROMPT.md          # System-Prompt für KI-Analyse (tunable)
│   ├── VERTRAGSMANAGEMENT_PROMPT.md
│   ├── STUFE1_BATCH_PROMPT.md
│   ├── STUFE2_FRISTEN_PROMPT.md
│   └── STUFE3_DATENBANK_PROMPT.md
├── output/                          ← fertige Analysen (persistent)
│   ├── vertrags_datenbank.csv       # CSV-Datenbank aller analysierten Verträge
│   ├── token_log.csv                # Token-/Kosten-Log aller KI-Aufrufe
│   └── pitch_one_pager.html         # Pitch-Material für Kundenakquise
├── DEPLOY.md                        ← Streamlit Cloud Deployment-Anleitung
├── .gitignore                       ← Git-Ausschlüsse (.env, output-CSVs, etc.)
└── .streamlit/
    ├── config.toml                  # Theme-Konfiguration
    └── secrets.toml.example         # Vorlage für API-Key-Deployment
├── archiv/                          ← ältere Versionen / Referenz
└── .tmp/                            ← temporär, frei löschbar
    └── test_vertraege/              # Test-PDFs (via create_test_batch.py regenerierbar)
```

---

## Deliverables

- **Vertragsanalysen & Datenbank-Outputs** → `output/` (dieses Projekts)
- **Persönliche Dokumente** (CV, Anschreiben etc.) → `~/Documents/CLAUDE/MEMORY/OUTPUT/`

---

## Behobene Bugs

| Bug | Status | Fix |
|---|---|---|
| Prompt Caching für Haiku 4.5 greift nicht | [gelöst] | System-Prompt auf ~3475 Tokens erweitert (Minimum 2048) |
| vertrags_datenbank.py schreibt leere Templates in CSV | [gelöst] | Filter nach vollständigen Einträgen; `--alle` für Debugging |
| Parser erkennt `Partei A (Mandant / ...)` nicht | [gelöst] | Regex angepasst: `[^:*]*` erlaubt optionalen Text vor `:**` |
