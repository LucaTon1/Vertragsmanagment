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
| check_setup.py prüfte python-docx nicht | [gelöst] | python-docx in Paketliste ergänzt |
| requirements.txt hatte veraltete anthropic-Mindestversion | [gelöst] | 0.40.0 → 0.90.0 |

---

## Supabase-Integration (ab 2026-04-18)

**Status:** Live – Supabase ist als persistentes DB-Backend integriert.

| Komponente | Detail |
|---|---|
| Supabase-Projekt | `utoqerrigzhhherxcbef.supabase.co` |
| Tabelle | `vertraege` (SQL in DEPLOY.md Abschnitt 3) |
| Modul | `tools/supabase_db.py` |
| Fallback | Automatisch auf lokale CSV wenn nicht konfiguriert |
| Credentials lokal | `.env` → `SUPABASE_URL` + `SUPABASE_KEY` |
| Credentials Cloud | Streamlit Secrets (bereits eingetragen) |

**Verhalten in app.py:**
- Supabase aktiv → ☁️-Banner + Daten aus Supabase
- Supabase nicht konfiguriert → ⚠️-Banner + lokale CSV (wie vorher)
- Nach Analyse → Eintrag wird in Supabase UND CSV geschrieben

**Migration bestehender CSV-Daten:**
```bash
python3 tools/supabase_db.py --sync
```

**Neue Spalten (einmalig in Supabase SQL Editor ausführen):**
```sql
ALTER TABLE vertraege ADD COLUMN IF NOT EXISTS risiko_score TEXT DEFAULT 'UNBEKANNT';
ALTER TABLE vertraege ADD COLUMN IF NOT EXISTS risiko_begruendung TEXT;
ALTER TABLE vertraege ADD COLUMN IF NOT EXISTS status_workflow TEXT DEFAULT 'Aktiv';
ALTER TABLE vertraege ADD COLUMN IF NOT EXISTS tags TEXT DEFAULT '';
ALTER TABLE vertraege ADD COLUMN IF NOT EXISTS notizen TEXT DEFAULT '';

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    aktion TEXT NOT NULL,
    vertrag_id TEXT,
    quelldatei TEXT,
    details TEXT,
    erstellt_am TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Nächste mögliche Aufgaben (Priorität)

✅ Delete-Button – Löscht Vertrag per ID aus Supabase (tools/app.py + supabase_db.py)
✅ SMTP-Reminder – UI-Button sendet Fristen-E-Mails via SMTP (fristen_reminder.py + app.py)
✅ PDF-Hash-Cache – SHA256-Fingerprint verhindert doppelte API-Calls (supabase_db.py + app.py)
✅ Batch-Upload – Mehrere PDFs gleichzeitig analysieren mit Progress-Bar (app.py)
✅ Risk Scoring – Risiko-Score 🟢/🟡/🔴 aus KI-Analyse extrahieren + in DB speichern + anzeigen
✅ Status-Workflow – Editierbarer Status pro Vertrag (Entwurf/In Prüfung/Aktiv/Gekündigt/Abgelaufen)
✅ Analytics Dashboard – Portfolio-Übersicht: KPIs, Charts, ablaufende Verträge
✅ Document Q&A – Fragen zum Vertrag mit Haiku 4.5 + Prompt Caching beantworten
✅ Excel-Export – CSV + XLSX-Download der gesamten Vertragsdatenbank
✅ Volltextsuche + Tags – Suchfeld in Datenbank, kommagetrennte Tags pro Vertrag
✅ Notizen pro Vertrag – Aufklappbarer Notizen-Bereich mit Speichern-Button
✅ Audit Trail – log_aktion() in supabase_db.py, Aktivitäts-Log in Analytics
✅ DSGVO-Klausel-Check – Optionaler DSGVO-Analyse-Modus mit eigenem Prompt + Download
✅ Vertragsvergleich (KI-gestützt) – Neue Seite "⚖️ Vergleich" in Navigation
