#!/usr/bin/env python3
"""
Setup-Check – Prüft ob alle Abhängigkeiten und Konfigurationen vorhanden sind.

Usage:
    python tools/check_setup.py
"""

import sys
import os
from pathlib import Path

BASE = Path(__file__).parent.parent


def check(label: str, ok: bool, hinweis: str = "") -> bool:
    if ok:
        print(f"[✓] {label}")
    else:
        suffix = f"  → {hinweis}" if hinweis else ""
        print(f"[✗] {label}{suffix}")
    return ok


def get_version(paket: str) -> str:
    try:
        import importlib.metadata
        return importlib.metadata.version(paket)
    except Exception:
        return None


def main():
    print("Vertragsmanagement – Setup Check")
    print("═══════════════════════════════")

    alle_ok = True

    # Python-Version
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    ok = v >= (3, 9)
    alle_ok &= check(f"Python 3.9+          ({version_str})", ok,
                     "Python 3.9 oder höher erforderlich")

    # Pakete
    for paket, min_version in [
        ("anthropic", "0.40.0"),
        ("pdfplumber", "0.10.0"),
        ("python-dotenv", "1.0.0"),
        ("streamlit", "1.30.0"),
        ("python-dateutil", "2.8.0"),
    ]:
        ver = get_version(paket)
        if ver:
            alle_ok &= check(f"{paket:<20} ({ver})", True)
        else:
            alle_ok &= check(f"{paket:<20}", False, f"pip install {paket}")

    # .env vorhanden
    env_pfad = BASE / ".env"
    alle_ok &= check(".env vorhanden", env_pfad.exists(),
                     ".env Datei mit ANTHROPIC_API_KEY erstellen")

    # API-Key gesetzt
    api_key = ""
    if env_pfad.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_pfad, override=True)
        except ImportError:
            pass
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    alle_ok &= check("ANTHROPIC_API_KEY gesetzt", bool(api_key),
                     "ANTHROPIC_API_KEY=sk-ant-... in .env eintragen")

    # Ordner
    for ordner in ["output", "prompts"]:
        p = BASE / ordner
        alle_ok &= check(f"{ordner}/ Ordner vorhanden", p.exists(),
                         f"mkdir {ordner}")

    print()
    if alle_ok:
        print("Alles bereit. Starte mit:")
        print("  python3 tools/vertragsanalyse.py <PDF>")
        print("  python3 tools/pipeline.py <PDF>")
        print("  python3 -m streamlit run tools/app.py  (Browser-UI)")
        sys.exit(0)
    else:
        print("Probleme gefunden – bitte oben aufgelistete Punkte beheben.")
        sys.exit(1)


if __name__ == "__main__":
    main()
