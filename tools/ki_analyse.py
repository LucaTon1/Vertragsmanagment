#!/usr/bin/env python3
"""
KI-Analyse Modul – Sendet Vertragstext an Claude API und erhält vollständige Analyse.

Verwendet claude-haiku-4-5 (günstigstes Modell) + Prompt Caching (90% Ersparnis
auf den System-Prompt). Modell per Flag wechselbar.

Usage (standalone):
    python tools/ki_analyse.py vertrag.pdf
    python tools/ki_analyse.py vertrag.pdf --modell claude-sonnet-4-6

Als Import:
    from ki_analyse import analysiere_vertrag, berechne_kosten
"""

import sys
import os
import csv
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


# ── Preistabelle (Stand April 2026, USD / Million Tokens) ────────────────────

PREISE = {
    "claude-haiku-4-5-20251001": {
        "input": 1.00, "output": 5.00,
        "cache_write": 1.25, "cache_read": 0.10,
        "label": "Haiku 4.5 (günstig)",
    },
    "claude-sonnet-4-6": {
        "input": 3.00, "output": 15.00,
        "cache_write": 3.75, "cache_read": 0.30,
        "label": "Sonnet 4.6 (balanced)",
    },
    "claude-opus-4-7": {
        "input": 5.00, "output": 25.00,
        "cache_write": 6.25, "cache_read": 0.50,
        "label": "Opus 4.7 (leistungsstark)",
    },
}

DEFAULT_MODELL = "claude-haiku-4-5-20251001"

# Max Rohtext-Zeichen die an die API gesendet werden (~15k Tokens bei Haiku)
# Haiku hat 200k Kontext – wir limitieren auf 60k Zeichen für Stabilität
MAX_ROHTEXT_ZEICHEN = 60_000


# ── System-Prompt (aus Datei laden → tunable ohne Code-Änderung) ─────────────

def _lade_system_prompt() -> str:
    """Lädt System-Prompt aus prompts/KI_SYSTEM_PROMPT.md (relativ zur tools/-Datei)."""
    base = os.path.dirname(os.path.abspath(__file__))
    prompt_pfad = os.path.join(base, "..", "prompts", "KI_SYSTEM_PROMPT.md")
    with open(prompt_pfad, "r", encoding="utf-8") as f:
        return f.read()

SYSTEM_PROMPT = _lade_system_prompt()


# ── Analyse-Template (Struktur für die KI) ───────────────────────────────────

ANALYSE_TEMPLATE = """\
# Vertragsanalyse: {titel}

**Analysedatum:** {datum}
**Seiten:** {seiten}
**Analysiert mit:** Vertragsmanagement-Workflow v2.0 (KI: {modell_label})
**Status:** Abgeschlossen

---

## 1. Vertragsparteien

- **Partei A:**
- **Partei B:**

---

## 2. Vertragstyp & Gegenstand

- **Vertragstyp (BGB-Systematik):**
- **Leistungsgegenstand:**
- **Vergütung / Vertragswert:**

---

## 3. Laufzeit & Fristen

{fristen_hinweise}

- **Vertragsbeginn:**
- **Vertragsende / Laufzeit:**
- **Ordentliche Kündigungsfrist:**
- **Außerordentliche Kündigung:**
- **Weitere Fristen:**

---

## 4. Kernpflichten

### Pflichten Partei A:


### Pflichten Partei B:


### Relevante Nebenpflichten:


---

## 5. Rechtliche Risiken & Auffälligkeiten


---

## 6. Handlungsempfehlungen

**Muss (vor Unterzeichnung):**

**Sollte (empfohlen):**

**Kann (optional):**
"""


# ── Token-Log ────────────────────────────────────────────────────────────────

def _schreibe_token_log(datei: str, token_info: dict):
    """Hängt eine Zeile mit Token-Nutzung an output/token_log.csv an."""
    log_pfad = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "token_log.csv")
    header = ["timestamp", "datei", "modell", "input_tokens", "output_tokens",
              "cache_write_tokens", "cache_read_tokens", "kosten_usd"]
    neu = not os.path.exists(log_pfad)
    os.makedirs(os.path.dirname(log_pfad), exist_ok=True)
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
            token_info.get("cache_creation_tokens", 0),
            token_info.get("cache_read_tokens", 0),
            round(berechne_kosten(token_info), 6),
        ])


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

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


def berechne_kosten(token_info: dict) -> float:
    """Berechnet die ungefähren API-Kosten in USD."""
    modell = token_info.get("modell", DEFAULT_MODELL)
    p = PREISE.get(modell, PREISE[DEFAULT_MODELL])

    kosten = (
        token_info.get("input_tokens", 0)          / 1_000_000 * p["input"] +
        token_info.get("output_tokens", 0)          / 1_000_000 * p["output"] +
        token_info.get("cache_creation_tokens", 0)  / 1_000_000 * p["cache_write"] +
        token_info.get("cache_read_tokens", 0)      / 1_000_000 * p["cache_read"]
    )
    return round(kosten, 6)


def formatiere_token_info(token_info: dict) -> str:
    """Gibt eine lesbare Zusammenfassung der Token-Nutzung zurück."""
    kosten = berechne_kosten(token_info)
    zeilen = [
        f"Modell:  {token_info.get('modell', DEFAULT_MODELL)}",
        f"Tokens:  {token_info.get('input_tokens', 0)} input | "
        f"{token_info.get('output_tokens', 0)} output",
    ]
    cache_read = token_info.get("cache_read_tokens", 0)
    cache_write = token_info.get("cache_creation_tokens", 0)
    if cache_read or cache_write:
        zeilen.append(
            f"Cache:   {cache_write} geschrieben | {cache_read} gelesen"
        )
    zeilen.append(f"Kosten:  ~${kosten:.4f} USD")
    return "\n  ".join(zeilen)


# ── Kern-Funktion ─────────────────────────────────────────────────────────────

def analysiere_vertrag(
    rohtext: str,
    vertrag_titel: str,
    seiten: int,
    fristen_hinweise: str = "",
    modell: str = DEFAULT_MODELL,
    max_tokens: int = 8192,
) -> tuple:
    """
    Analysiert einen Vertragstext via Claude API.

    Args:
        rohtext:          Volltext des Vertrags (aus PDF extrahiert)
        vertrag_titel:    Lesbarer Titel für das Template
        seiten:           Seitenanzahl des Originals
        fristen_hinweise: Vorausgefüllte Fristen (aus fristen_extraktor.py)
        modell:           Claude-Modell-ID
        max_tokens:       Max. Output-Tokens (Standard: 8192, ausreichend
                          fuer Vertraege mit 15+ Paragraphen und 10+ Risiken.
                          Haiku 4.5 erlaubt bis 64.000.)

    Returns:
        (analyse_text: str, token_info: dict)
    """
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "anthropic-Paket nicht installiert.\n"
            "Lösung: pip install anthropic"
        )

    api_key = lade_api_key()
    client = anthropic.Anthropic(api_key=api_key)

    modell_label = PREISE.get(modell, {}).get("label", modell)
    datum = datetime.now().strftime("%Y-%m-%d")

    template = ANALYSE_TEMPLATE.format(
        titel=vertrag_titel,
        datum=datum,
        seiten=seiten,
        modell_label=modell_label,
        fristen_hinweise=fristen_hinweise or "<!-- Keine Fristen automatisch erkannt -->",
    )

    # Rohtext kürzen wenn nötig
    if len(rohtext) > MAX_ROHTEXT_ZEICHEN:
        rohtext_gesendet = (
            rohtext[:MAX_ROHTEXT_ZEICHEN]
            + f"\n\n[... Text gekürzt: {len(rohtext)} Zeichen gesamt, "
            f"nur erste {MAX_ROHTEXT_ZEICHEN} gesendet ...]"
        )
    else:
        rohtext_gesendet = rohtext

    heute_iso = datetime.now().strftime("%Y-%m-%d")
    user_content = (
        f"**Heutiges Datum (fuer alle Fristberechnungen und Empfehlungen):** {heute_iso}\n\n"
        f"Befuelle dieses Template vollstaendig auf Basis des folgenden Vertragstextes. "
        f"Bei Datumsangaben in Handlungsempfehlungen beachte, dass Daten in der Vergangenheit "
        f"nicht als Frist genutzt werden duerfen.\n\n"
        f"{template}\n\n"
        f"---\n\n"
        f"## Vertragstext\n\n"
        f"{rohtext_gesendet}"
    )

    message = client.messages.create(
        model=modell,
        max_tokens=max_tokens,
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},  # System-Prompt wird gecacht
        }],
        messages=[{"role": "user", "content": user_content}],
    )

    analyse_text = message.content[0].text

    token_info = {
        "modell":                modell,
        "input_tokens":          message.usage.input_tokens,
        "output_tokens":         message.usage.output_tokens,
        "cache_creation_tokens": getattr(message.usage, "cache_creation_input_tokens", 0),
        "cache_read_tokens":     getattr(message.usage, "cache_read_input_tokens", 0),
    }

    _schreibe_token_log(vertrag_titel, token_info)

    return analyse_text, token_info


def extrahiere_risiko_score(analyse_text: str) -> dict:
    """Extrahiert Risiko-Score und Begründung aus dem Analyse-Text."""
    import re
    score_match = re.search(r'\*\*Risiko-Score:\*\*\s*(GRÜN|GELB|ROT)', analyse_text, re.IGNORECASE)
    begruendung_match = re.search(r'\*\*Begründung[^*]*\*\*[:\s]*([^\n]+)', analyse_text)
    score = score_match.group(1).upper() if score_match else "UNBEKANNT"
    begruendung = begruendung_match.group(1).strip() if begruendung_match else ""
    return {"risiko_score": score, "risiko_begruendung": begruendung}


def beantworte_frage(rohtext: str, frage: str, modell: str = "claude-haiku-4-5-20251001") -> str:
    """Beantwortet eine Frage zu einem Vertragstext. Nutzt Prompt Caching."""
    try:
        import anthropic
    except ImportError:
        raise ImportError("anthropic-Paket nicht installiert. Lösung: pip install anthropic")

    api_key = lade_api_key()
    client = anthropic.Anthropic(api_key=api_key)

    system = (
        "Du bist ein Vertragsexperte. Beantworte Fragen zu dem folgenden Vertrag präzise und auf Deutsch. "
        "Antworte in 2–4 Sätzen. Wenn die Information nicht im Vertrag steht, sage das klar."
    )

    response = client.messages.create(
        model=modell,
        max_tokens=512,
        system=[
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            },
            {
                "type": "text",
                "text": f"VERTRAGSTEXT:\n\n{rohtext[:15000]}",
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[{"role": "user", "content": frage}],
    )
    return response.content[0].text


def dsgvo_check(rohtext: str, modell: str = "claude-haiku-4-5-20251001") -> tuple:
    """
    Spezieller DSGVO-Klausel-Check für Verträge.
    Günstiger als Vollanalyse da fokussierter Output-Prompt.
    """
    import anthropic
    api_key = lade_api_key()
    client = anthropic.Anthropic(api_key=api_key)

    system = """Du bist ein DSGVO-Experte. Analysiere den Vertragstext ausschließlich auf datenschutzrechtliche Aspekte.

Erstelle einen strukturierten Bericht mit diesen Abschnitten:

## DSGVO-Check

**Gesamtbewertung:** [KONFORM | PRÜFBEDARF | KRITISCH]

### 1. Personenbezogene Daten
Werden personenbezogene Daten verarbeitet? Welche Kategorien?

### 2. Auftragsverarbeitung (Art. 28 DSGVO)
Ist ein AVV notwendig? Vorhanden?

### 3. Datenweitergabe / Drittländer (Art. 44-49 DSGVO)
Werden Daten an Dritte oder Drittländer übermittelt?

### 4. Betroffenenrechte (Art. 15-22 DSGVO)
Sind Betroffenenrechte adressiert (Auskunft, Löschung, Widerspruch)?

### 5. Technische & organisatorische Maßnahmen (Art. 32 DSGVO)
Sind TOMs erwähnt oder geregelt?

### 6. Handlungsempfehlungen
Konkrete nächste Schritte (maximal 3 Punkte).

Antworte präzise. Wenn eine Kategorie nicht relevant ist, schreibe „Nicht anwendbar."."""

    response = client.messages.create(
        model=modell,
        max_tokens=1024,
        system=[
            {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": f"VERTRAGSTEXT:\n\n{rohtext[:20000]}", "cache_control": {"type": "ephemeral"}},
        ],
        messages=[{"role": "user", "content": "Führe den DSGVO-Check durch."}],
    )
    text = response.content[0].text
    usage = response.usage
    token_info = {
        "modell": modell,
        "input_tokens": getattr(usage, "input_tokens", 0),
        "output_tokens": getattr(usage, "output_tokens", 0),
        "cache_creation_tokens": getattr(usage, "cache_creation_input_tokens", 0),
        "cache_read_tokens": getattr(usage, "cache_read_input_tokens", 0),
    }
    return text, token_info


def vergleiche_vertraege(vertrag_a: dict, vertrag_b: dict, modell: str = "claude-haiku-4-5-20251001") -> tuple:
    """
    Vergleicht zwei Verträge anhand ihrer gespeicherten Metadaten.
    Keine PDF-Re-Uploads nötig → sehr günstig (~0,02 $).
    """
    import anthropic
    api_key = lade_api_key()
    client = anthropic.Anthropic(api_key=api_key)

    def fmt(v: dict) -> str:
        felder = ["quelldatei", "partei_a", "partei_b", "vertragstyp", "vertragsbeginn",
                  "vertragsende", "kuendigungsfrist", "status_workflow", "risiko_score",
                  "risiko_begruendung", "tags", "notizen"]
        return "\n".join(f"- {k}: {v.get(k, '–')}" for k in felder)

    prompt = f"""Vergleiche diese zwei Verträge strukturiert:

VERTRAG A:
{fmt(vertrag_a)}

VERTRAG B:
{fmt(vertrag_b)}

Erstelle einen Vergleich mit:
## Gemeinsamkeiten
## Wesentliche Unterschiede
## Risiko-Einschätzung im Vergleich
## Empfehlung (welcher Vertrag ist günstiger/riskanter und warum)

Antworte präzise auf Deutsch."""

    response = client.messages.create(
        model=modell,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    usage = response.usage
    token_info = {
        "modell": modell,
        "input_tokens": getattr(usage, "input_tokens", 0),
        "output_tokens": getattr(usage, "output_tokens", 0),
    }
    return text, token_info


# ── Standalone CLI ────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("KI-Vertragsanalyse – sendet PDF an Claude API\n")
        print("Verwendung:")
        print("  python tools/ki_analyse.py vertrag.pdf")
        print("  python tools/ki_analyse.py vertrag.pdf --modell claude-sonnet-4-6")
        print("\nVerfügbare Modelle:")
        for mid, info in PREISE.items():
            print(f"  {mid:<40} {info['label']}")
        sys.exit(0)

    from utils import extract_text_from_pdf, ensure_output_dir, slugify, display_name
    from fristen_extraktor import extrahiere_fristen, kategorien_label

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Fehler: {pdf_path} nicht gefunden")
        sys.exit(1)

    # Modell aus Argument
    modell = DEFAULT_MODELL
    if "--modell" in sys.argv:
        idx = sys.argv.index("--modell")
        if idx + 1 < len(sys.argv):
            modell = sys.argv[idx + 1]
        if modell not in PREISE:
            print(f"Unbekanntes Modell: {modell}")
            print(f"Gültige Modelle: {', '.join(PREISE.keys())}")
            sys.exit(1)

    print(f"Verarbeite: {pdf_path.name}")
    rohtext, seiten = extract_text_from_pdf(str(pdf_path))
    print(f"  {seiten} Seiten | {len(rohtext)} Zeichen")

    fristen = extrahiere_fristen(rohtext)
    print(f"  {len(fristen)} Fristen automatisch erkannt")

    fristen_hinweise = ""
    if fristen:
        zeilen = ["<!-- Automatisch erkannt – bitte prüfen und einordnen -->"]
        for t in fristen:
            zeilen.append(f"- {t['match']} ({kategorien_label(t['kategorie'])})")
        fristen_hinweise = "\n".join(zeilen)

    print(f"\nSende an Claude API ({modell})...")

    try:
        analyse_text, token_info = analysiere_vertrag(
            rohtext=rohtext,
            vertrag_titel=display_name(pdf_path.stem),
            seiten=seiten,
            fristen_hinweise=fristen_hinweise,
            modell=modell,
        )
    except (ImportError, ValueError) as e:
        print(f"\nFehler: {e}")
        sys.exit(1)

    print(f"  {formatiere_token_info(token_info)}")

    # Output speichern (mit Rohtext-Anhang)
    output_dir = ensure_output_dir()
    datum = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(pdf_path.stem)
    output_path = output_dir / f"vertragsanalyse_{slug}_{datum}.md"

    rohtext_vorschau = rohtext[:3000]
    if len(rohtext) > 3000:
        rohtext_vorschau += "\n\n[... gekürzt – vollständiger Text unten ...]"

    volltext = (
        analyse_text
        + f"\n\n---\n\n"
        f"## 7. Rohtext (Quelle)\n\n"
        f"```\n{rohtext_vorschau}\n```\n\n"
        f"*Vollständiger Rohtext: {len(rohtext)} Zeichen | {rohtext.count(chr(10))} Zeilen*\n"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(volltext)

    print(f"\nAnalyse gespeichert: {output_path}")
    print(f"Nächster Schritt:    python tools/vertrags_datenbank.py")


if __name__ == "__main__":
    main()
