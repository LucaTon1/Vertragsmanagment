# Deployment – Vertragsmanagement auf Streamlit Cloud

## Voraussetzungen

- GitHub-Account (kostenlos)
- Streamlit Cloud Account (kostenlos unter share.streamlit.io)
- Anthropic API-Key (console.anthropic.com)

## Schritt-für-Schritt

### 1. GitHub-Repository erstellen

```bash
cd vertragsmanagement/
git init
git add .
git commit -m "Initial commit: Vertragsmanagement v2.0"
# Neues Repo auf github.com erstellen, dann:
git remote add origin https://github.com/DEIN_USERNAME/vertragsmanagement.git
git push -u origin main
```

**Wichtig:** `.env` wird durch `.gitignore` automatisch ausgeschlossen.

### 2. Streamlit Cloud deployen

1. Gehe zu share.streamlit.io → "New app"
2. Repository: `DEIN_USERNAME/vertragsmanagement`
3. Branch: `main`
4. Main file path: `tools/app.py`
5. Klicke "Advanced settings" → "Secrets"
6. Trage ein:
```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
```
7. Klicke "Deploy"

### 3. Bekannte Einschränkungen (Streamlit Cloud Free Tier)

- **Kein persistenter Speicher:** `vertrags_datenbank.csv` und `token_log.csv` werden bei
  Neustart zurückgesetzt. Für produktiven Einsatz: Supabase oder Google Sheets als DB nutzen.
- **Schlafen nach Inaktivität:** App schläft nach 7 Tagen ohne Besucher (reaktiviert sich beim
  ersten Aufruf in ~30 Sekunden).
- **Ressourcen:** 1 GB RAM, ausreichend für Vertragsanalysen bis ca. 50 Seiten.

### 4. Lokal starten

```bash
pip install -r requirements.txt
streamlit run tools/app.py
```

## URL-Format nach Deployment

`https://DEIN_USERNAME-vertragsmanagement-tools-app-XXXX.streamlit.app`
