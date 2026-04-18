#!/usr/bin/env python3
"""
Gemeinsame Hilfsfunktionen für alle Vertragsmanagement-Tools.
Wird von vertragsanalyse.py, batch_vertragsanalyse.py und
fristen_extraktor.py importiert.
"""

import re
import sys
from pathlib import Path


# Projekt-Wurzel = Elternordner von tools/
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / ".tmp"


def ensure_output_dir() -> Path:
    """Stellt sicher, dass .tmp/ existiert, und gibt den Pfad zurück."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    return OUTPUT_DIR


def slugify(text: str) -> str:
    """
    Wandelt einen Text in einen sicheren Dateinamen um.
    Entfernt numerische Präfixe: '04_arbeitsvertrag' → 'arbeitsvertrag'
    """
    text = re.sub(r"^\d+[_\-\s]+", "", text)   # "04_name" → "name"
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "_", text.strip())
    return text[:50]


def display_name(stem: str) -> str:
    """
    Erstellt einen lesbaren Anzeigenamen aus einem Dateinamen-Stem.
    '04_arbeitsvertrag' → 'Arbeitsvertrag'
    'muster-consultingvertrag' → 'Muster Consultingvertrag'
    """
    name = re.sub(r"^\d+[_\-\s]+", "", stem)       # Numerischen Präfix entfernen
    name = re.sub(r"[_\-]+", " ", name)             # Underscores/Bindestriche → Leerzeichen
    return name.strip().title()


def extract_text_from_pdf(pdf_path: str) -> tuple:
    """
    Extrahiert den vollständigen Text aus einer PDF-Datei.
    Gibt (rohtext: str, seitenanzahl: int) zurück.
    Wirft Exception bei Fehler – Aufrufer entscheidet über Behandlung.
    """
    try:
        import pdfplumber
    except ImportError:
        print("pdfplumber nicht installiert. Führe aus: pip install pdfplumber")
        sys.exit(1)

    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text and text.strip():
                text_parts.append(f"[Seite {i}]\n{text}")
            else:
                text_parts.append(f"[Seite {i} – kein Text extrahierbar]")

    return "\n\n".join(text_parts), total_pages
