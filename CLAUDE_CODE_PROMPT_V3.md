# Claude Code Prompt – Vertragsmanagement v3: DOCX-Export, Deployment & Pitch

## Kontext (lies das, nicht die Codebasis)

Projekt: `vertragsmanagement/` – WAT-Framework, vollständig funktionsfähig.
Lies **ausschließlich** `CLAUDE.md` als Einstieg. Keine weiteren Explorationen nötig.

Aktueller Stand (bereits implementiert, nicht anfassen):
- `tools/app.py` – Streamlit UI, 3 Seiten, lauffähig
- `tools/fristen_reminder.py` – Fristen-Check + E-Mail-Reminder
- `tools/pipeline.py` – End-to-End PDF → Analyse → HTML → DB
- `tools/ki_analyse.py` – Claude API, Haiku 4.5 + Prompt Caching (aktiv)
- `tools/generate_report.py` – Markdown → HTML-Report
- `output/token_log.csv` – enthält 5 Einträge, letzter Run hat cache_write=5709 ✓

Bekannte Lücken die dieser Prompt schließt:
1. `requirements.txt` fehlen `streamlit` und `python-dateutil`
2. Kein `.gitignore` (`.env` würde sonst in Git landen)
3. Kein DOCX-Export (Kunden wollen Word, nicht nur HTML)
4. Kein Streamlit-Cloud-Deployment (kein öffentlicher Demo-Link)
5. Kein Pitch-Material für Kundenakquise

**Arbeitsweise:**
- Jeden Schritt nach Implementierung sofort verifizieren (Befehl angegeben)
- Bei Fehler: Stacktrace lesen, fixen, erneut testen
- Keine unnötigen Datei-Reads von bereits bekannten Files

---

## Phase 1 – Infrastruktur (5 Minuten, kein API-Call)

### 1.1 requirements.txt ergänzen

Öffne `requirements.txt`. Ergänze am Ende:
```
streamlit>=1.30.0
python-dateutil>=2.8.0
python-docx>=1.1.0
```

**Verifikation:**
```bash
cat requirements.txt
# Muss 6 Zeilen zeigen (3 alt + 3 neu)
```

---

### 1.2 .gitignore erstellen

Erstelle `.gitignore` im Projektstamm `vertragsmanagement/`:

```gitignore
# Secrets
.env
.env.*

# Temporäre Dateien
.tmp/
__pycache__/
*.pyc
*.pyo
.DS_Store

# Streamlit Cloud Secrets (lokal)
.streamlit/secrets.toml

# Output (nicht committen – wird lokal generiert)
output/token_log.csv
output/vertrags_datenbank.csv

# Aber HTML-Reports und Analysen behalten:
!output/*.html
!output/*.md
```

**Verifikation:**
```bash
cat .gitignore
# .env muss in der Liste sein
```

---

## Phase 2 – DOCX-Export

**Zieldateien:** `tools/generate_report.py` (neue Funktion), `tools/app.py` (neuer Button)

### 2.1 `generiere_docx()` in generate_report.py

Ergänze am Ende von `generate_report.py` (vor dem `if __name__ == "__main__"` Block) folgende Funktion:

```python
def generiere_docx(md_pfad, output_dir=None):
    """
    Wandelt eine Vertragsanalyse-Markdown-Datei in ein DOCX-Dokument um.
    Gibt den Pfad zur erstellten .docx-Datei zurück.
    """
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        raise ImportError("python-docx fehlt. Lösung: pip install python-docx")

    md_pfad = Path(md_pfad)
    text = md_pfad.read_text(encoding="utf-8")

    if output_dir is None:
        output_dir = md_pfad.parent
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stamm = re.sub(r"_\d{8}_\d{6}$", "", md_pfad.stem)
    datum_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    docx_pfad = output_dir / f"{stamm}_{datum_str}.docx"

    doc = Document()

    # ── Seitenränder ──
    section = doc.sections[0]
    section.left_margin   = Inches(1.0)
    section.right_margin  = Inches(1.0)
    section.top_margin    = Inches(1.0)
    section.bottom_margin = Inches(1.0)

    # ── Styles ──
    def stil_ueberschrift1(para):
        para.style = doc.styles["Heading 1"]
        run = para.runs[0] if para.runs else para.add_run(para.text)
        run.font.size = Pt(16)
        run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    def stil_ueberschrift2(para):
        para.style = doc.styles["Heading 2"]
        run = para.runs[0] if para.runs else para.add_run(para.text)
        run.font.size = Pt(13)
        run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x5F)

    # ── Titel-Block ──
    titel_match = re.search(r"#\s+Vertragsanalyse:\s+(.+)", text)
    titel = titel_match.group(1).strip() if titel_match else md_pfad.stem

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"Vertragsanalyse")
    run.font.size = Pt(20)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run2 = p2.add_run(titel)
    run2.font.size = Pt(14)
    run2.font.color.rgb = RGBColor(0x1E, 0x3A, 0x5F)

    # Header-Felder (Analysedatum, Status, Modell)
    for feld in ["Analysedatum", "Status", "Analysiert mit"]:
        m = re.search(rf"\*\*{feld}:\*\*\s*(.+)", text)
        if m:
            p = doc.add_paragraph()
            run = p.add_run(f"{feld}: ")
            run.font.bold = True
            run.font.size = Pt(10)
            run2 = p.add_run(m.group(1).strip())
            run2.font.size = Pt(10)

    doc.add_paragraph()  # Leerzeile

    # ── Abschnitte parsen und ausgeben ──
    abschnitt_pattern = re.compile(
        r"^##\s+(\d+\.\s+.+?)$\n(.*?)(?=^##\s+\d+\.|\Z)",
        re.MULTILINE | re.DOTALL,
    )

    for match in abschnitt_pattern.finditer(text):
        abschnitt_titel = match.group(1).strip()
        abschnitt_inhalt = match.group(2).strip()

        # Abschnitt-Überschrift
        p = doc.add_paragraph()
        stil_ueberschrift2(p)
        p.clear()
        p.add_run(abschnitt_titel).font.size = Pt(13)

        # Inhalt zeilenweise
        for zeile in abschnitt_inhalt.splitlines():
            zeile = zeile.strip()
            if not zeile or zeile == "---":
                continue

            # ### Unterüberschrift
            if zeile.startswith("### "):
                p = doc.add_paragraph()
                run = p.add_run(zeile[4:])
                run.font.bold = True
                run.font.size = Pt(11)
                run.font.color.rgb = RGBColor(0x37, 0x41, 0x51)

            # Listeneintrag
            elif zeile.startswith("- "):
                inhalt = zeile[2:]
                # Fettdruck **..:** am Anfang erkennen
                fett_match = re.match(r"\*\*(.+?):\*\*\s*(.*)", inhalt)
                p = doc.add_paragraph(style="List Bullet")
                if fett_match:
                    run = p.add_run(fett_match.group(1) + ": ")
                    run.font.bold = True
                    run.font.size = Pt(10)
                    rest = re.sub(r"\*+", "", fett_match.group(2))
                    p.add_run(rest).font.size = Pt(10)
                else:
                    clean = re.sub(r"\*+", "", inhalt)
                    p.add_run(clean).font.size = Pt(10)

            # Normaler Text
            else:
                clean = re.sub(r"\*+", "", zeile)
                if clean:
                    p = doc.add_paragraph(clean)
                    p.runs[0].font.size = Pt(10) if p.runs else None

        doc.add_paragraph()  # Abstand nach Abschnitt

    # ── Footer ──
    doc.add_paragraph("─" * 60)
    p = doc.add_paragraph(
        f"Erstellt mit Vertragsmanagement v2.0 · {datetime.now().strftime('%d.%m.%Y')}"
    )
    p.runs[0].font.size = Pt(9)
    p.runs[0].font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

    doc.save(str(docx_pfad))
    return str(docx_pfad)
```

**Verifikation:**
```bash
python3 -c "
import ast
src = open('tools/generate_report.py').read()
ast.parse(src)
print('Syntax OK')
assert 'generiere_docx' in src, 'Funktion fehlt!'
print('generiere_docx: gefunden')
"
```

---

### 2.2 DOCX-Download-Button in app.py

In `tools/app.py`, in der **Seite 1 (Analyse)** direkt nach dem bestehenden `st.download_button` für HTML, füge einen zweiten Download-Button für DOCX ein:

```python
# DOCX-Download-Button (nach dem HTML-Download-Button einfügen)
try:
    from generate_report import generiere_docx
    docx_pfad = generiere_docx(md_pfad, output_dir=OUTPUT_DIR)
    with open(docx_pfad, "rb") as docx_f:
        st.download_button(
            label="Word-Dokument herunterladen (.docx)",
            data=docx_f.read(),
            file_name=Path(docx_pfad).name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
except Exception as e:
    st.caption(f"DOCX-Export nicht verfügbar: {e}")
```

**Verifikation:**
```bash
python3 -c "
import ast
src = open('tools/app.py').read()
ast.parse(src)
print('Syntax OK')
assert 'generiere_docx' in src, 'DOCX-Button fehlt!'
assert 'Word-Dokument' in src
print('DOCX-Button: gefunden')
"
```

---

## Phase 3 – Streamlit Cloud Deployment

### 3.1 Streamlit-Konfiguration

Erstelle Ordner und Dateien:

**`.streamlit/config.toml`:**
```toml
[theme]
primaryColor = "#1e3a5f"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f5"
textColor = "#1a1a2e"
font = "sans serif"

[server]
headless = true
enableCORS = false
```

**`.streamlit/secrets.toml.example`** (Vorlage für Deployment, kein echter Key):
```toml
# Kopiere diese Datei nach .streamlit/secrets.toml (lokal) ODER
# trage die Werte im Streamlit Cloud Dashboard unter "Secrets" ein.
# WICHTIG: secrets.toml NIE committen (.gitignore schützt sie bereits).

ANTHROPIC_API_KEY = "sk-ant-..."

# Optional: E-Mail-Reminder
# SMTP_HOST = "smtp.gmail.com"
# SMTP_PORT = "587"
# SMTP_USER = "deine@email.de"
# SMTP_PASSWORD = "app-passwort"
# REMINDER_TO = "empfaenger@email.de"
```

---

### 3.2 API-Key-Fallback für Streamlit Cloud

Streamlit Cloud injiziert Secrets als Umgebungsvariablen. Die bestehende `lade_api_key()`-Funktion in `tools/ki_analyse.py` nutzt bereits `os.environ.get("ANTHROPIC_API_KEY")` – das funktioniert ohne Änderung.

Ergänze jedoch in `tools/ki_analyse.py` in der Funktion `lade_api_key()` einen Streamlit-Secrets-Fallback **vor** dem `os.environ.get`-Aufruf:

```python
def lade_api_key() -> str:
    """Lädt ANTHROPIC_API_KEY: (1) Streamlit Secrets, (2) .env, (3) Umgebungsvariable."""
    # (1) Streamlit Cloud Secrets
    try:
        import streamlit as st
        key = st.secrets.get("ANTHROPIC_API_KEY", "").strip()
        if key:
            return key
    except Exception:
        pass

    # (2) .env Datei
    try:
        from dotenv import load_dotenv
        env_pfad = Path(__file__).parent.parent / ".env"
        if env_pfad.exists():
            load_dotenv(env_pfad, override=False)
    except ImportError:
        pass

    # (3) Umgebungsvariable
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY nicht gesetzt.\n"
            "Lösung A (lokal): Key in .env eintragen: ANTHROPIC_API_KEY=sk-ant-...\n"
            "Lösung B (Streamlit Cloud): Key im Dashboard unter Settings → Secrets eintragen.\n"
            "Key holen: https://console.anthropic.com/settings/keys"
        )
    return api_key
```

**Wichtig:** Den Rest von `ki_analyse.py` nicht verändern.

**Verifikation:**
```bash
python3 -c "
import ast
src = open('tools/ki_analyse.py').read()
ast.parse(src)
print('Syntax OK')
assert 'streamlit' in src and 'st.secrets' in src
print('Streamlit-Fallback: gefunden')
"
```

---

### 3.3 Deployment-Anleitung erstellen

Erstelle `DEPLOY.md` im Projektstamm mit folgendem Inhalt:

```markdown
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
```

**Verifikation:**
```bash
cat DEPLOY.md | head -5
# Muss "Deployment" als erste Überschrift zeigen
```

---

## Phase 4 – Pitch One-Pager

**Neue Datei:** `output/pitch_one_pager.html`

Erstelle eine professionelle, standalone HTML-Seite die das Produkt für einen potenziellen Kunden in München (Mittelstand, 20–500 MA) beschreibt.

**Inhalt (exakt diese Daten verwenden – nicht ausdenken):**

```
Reale Zahlen aus dem ersten echten Pipeline-Test (17.04.2026, SaaS-Vertrag 5 Seiten):
- Datenextraktion: 16/16 Felder korrekt (100 %)
- Kosten: ~0,05 USD pro Vertrag (ca. 4–5 Cent)
- Bei 100 Verträgen/Monat: ~5 USD (ca. 4,60 EUR) API-Kosten
- Analyse-Tiefe: 10 kritische Risiken, 7 mittlere Risiken, 20 Handlungsempfehlungen erkannt
- Laufzeit: ca. 30 Sekunden pro Vertrag (Haiku 4.5)
```

**Struktur der HTML-Seite:**

1. **Header:** Name + Tagline + Kontakt-Platzhalter
2. **Problem-Block:** Was kostet manuelle Vertragsprüfung?
   - Anwalt: 150–300 EUR/Stunde, Erstcheck ~2–4h = 300–1.200 EUR pro Vertrag
   - Risiko verpasster Fristen: z.B. automatische Vertragsverlängerung um 12 Monate
3. **Lösung:** Was das System tut (3 Punkte, konkret)
4. **Zahlen-Block:** Die oben genannten realen Testzahlen prominent darstellen
5. **Leistungspakete (Tabelle):**
   ```
   Starter     | Einmalig 1.500 EUR + 300 EUR/Monat  | bis 20 Verträge/Monat
   Professional| Einmalig 3.000 EUR + 500 EUR/Monat  | bis 100 Verträge/Monat
   Enterprise  | Einmalig 5.000 EUR + 800 EUR/Monat  | unbegrenzt + API-Zugang
   ```
6. **Disclaimer** (klein, unten): "Dieses Tool unterstützt juristische Erstprüfung. Es ersetzt keine anwaltliche Beratung."
7. **CTA:** Kontakt-E-Mail Platzhalter (gianlucalanger04@gmail.com)

**Design:** Professionell, dunkelblau/weiß, gleiche Farbpalette wie der HTML-Report (`#0f172a`, `#1e3a5f`). Einzelne HTML-Datei, kein externes CSS, keine externen Fonts nötig, druckbar.

**Verifikation:**
```bash
python3 -c "
from pathlib import Path
html = Path('output/pitch_one_pager.html').read_text()
assert '100 %' in html or '100%' in html, 'Testzahlen fehlen'
assert '1.500' in html, 'Preise fehlen'
assert 'gianlucalanger04@gmail.com' in html, 'Kontakt fehlt'
print('One-Pager: alle Pflichtinhalte vorhanden')
print(f'Dateigröße: {len(html):,} Zeichen')
"
```

---

## Abschluss

### CLAUDE.md aktualisieren

Ergänze in `CLAUDE.md` unter "Ordnerstruktur":
- `DEPLOY.md` — Streamlit Cloud Deployment-Anleitung
- `.gitignore` — Git-Ausschlüsse
- `.streamlit/config.toml` — Theme-Konfiguration
- `output/pitch_one_pager.html` — Pitch-Material für Kundenakquise

### Abschlussprüfung

```bash
# 1. Alle neuen Dateien vorhanden?
for f in requirements.txt .gitignore .streamlit/config.toml .streamlit/secrets.toml.example DEPLOY.md output/pitch_one_pager.html; do
    [ -f "$f" ] && echo "✓ $f" || echo "✗ FEHLT: $f"
done

# 2. Alle Python-Dateien Syntax-OK?
python3 -c "
import ast
for f in ['tools/app.py','tools/generate_report.py','tools/ki_analyse.py','tools/fristen_reminder.py']:
    ast.parse(open(f).read())
    print(f'✓ {f}')
"

# 3. requirements.txt vollständig?
python3 -c "
reqs = open('requirements.txt').read()
for p in ['anthropic', 'pdfplumber', 'python-dotenv', 'streamlit', 'python-dateutil', 'python-docx']:
    status = '✓' if p in reqs else '✗ FEHLT'
    print(f'{status} {p}')
"

# 4. .gitignore schützt .env?
python3 -c "
gi = open('.gitignore').read()
assert '.env' in gi, '.env fehlt in .gitignore!'
print('✓ .env in .gitignore geschützt')
"
```

Gib am Ende einen kurzen Abschlussbericht:
- Welche Dateien wurden erstellt / geändert
- Ob alle 4 Verifikationen grün sind
- Nächste konkrete Schritte für den Nutzer (max. 3 Punkte, handlungsorientiert)
