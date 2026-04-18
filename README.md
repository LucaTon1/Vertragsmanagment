# Vertragsmanagement – WAT-Framework

Automatisierte Vertragsanalyse mit Claude Haiku 4.5: PDFs hochladen, KI-Analyse erstellen, HTML- und DOCX-Reports herunterladen.

## Schnellstart

```bash
pip install -r requirements.txt
streamlit run tools/app.py
```

## Deployment auf Streamlit Cloud

Siehe [DEPLOY.md](DEPLOY.md) für vollständige Anleitung.

## Features

- PDF-Verträge analysieren (Fristen, Parteien, Risiken)
- HTML- und Word-Reports herunterladen
- Vertrags-Datenbank (CSV)
- Token-/Kosten-Tracking

## Voraussetzungen

- Python 3.9+
- Anthropic API Key (`.env` oder Streamlit Secrets)
