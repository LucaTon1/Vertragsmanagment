#!/usr/bin/env python3
"""
Supabase-Backend für die Vertrags-Datenbank.

Ersetzt die lokale CSV-Datenbank durch Supabase (PostgreSQL).
Fällt automatisch auf CSV zurück wenn Supabase nicht konfiguriert ist.

Einrichtung:
  1. Supabase-Projekt anlegen: https://supabase.com
  2. SQL aus dieser Datei ausführen (Tabelle anlegen)
  3. Credentials in .env oder Streamlit Secrets eintragen:
       SUPABASE_URL=https://xxxx.supabase.co
       SUPABASE_KEY=eyJ...  (anon key aus Settings → API)

Verwendung:
    from supabase_db import speichere_vertrag, lade_vertraege, ist_konfiguriert
"""

import os
import csv
from pathlib import Path
from datetime import datetime

# ── Supabase-SQL zum Anlegen der Tabelle ─────────────────────────────────────
#
# In Supabase Dashboard → SQL Editor ausführen:
#
# CREATE TABLE IF NOT EXISTS vertraege (
#   id               BIGSERIAL PRIMARY KEY,
#   quelldatei       TEXT,
#   analysedatum     TEXT,
#   partei_a         TEXT,
#   partei_b         TEXT,
#   vertragstyp      TEXT,
#   leistungsgegenstand TEXT,
#   verguetung       TEXT,
#   vertragsbeginn   TEXT,
#   vertragsende     TEXT,
#   kuendigungsfrist TEXT,
#   status           TEXT,
#   created_at       TIMESTAMPTZ DEFAULT NOW()
# );
#
# ALTER TABLE vertraege ENABLE ROW LEVEL SECURITY;
# CREATE POLICY "Public read/write" ON vertraege FOR ALL USING (true) WITH CHECK (true);

TABELLE = "vertraege"

# Spalten die aus der CSV in Supabase gespiegelt werden
# Neue Spalten einmalig in Supabase ausführen:
# ALTER TABLE vertraege ADD COLUMN IF NOT EXISTS risiko_score TEXT DEFAULT 'UNBEKANNT';
# ALTER TABLE vertraege ADD COLUMN IF NOT EXISTS risiko_begruendung TEXT;
# ALTER TABLE vertraege ADD COLUMN IF NOT EXISTS status_workflow TEXT DEFAULT 'Aktiv';

SPALTEN = [
    "quelldatei", "analysedatum", "partei_a", "partei_b",
    "vertragstyp", "leistungsgegenstand", "verguetung",
    "vertragsbeginn", "vertragsende", "kuendigungsfrist", "status",
    "risiko_score", "risiko_begruendung", "status_workflow",
]


def _lade_credentials() -> tuple[str, str]:
    """Lädt SUPABASE_URL und SUPABASE_KEY aus Streamlit Secrets oder .env."""
    url = ""
    key = ""

    # (1) Streamlit Secrets
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL", "").strip()
        key = st.secrets.get("SUPABASE_KEY", "").strip()
        if url and key:
            return url, key
    except Exception:
        pass

    # (2) .env / Umgebungsvariable
    try:
        from dotenv import load_dotenv
        env_pfad = Path(__file__).parent.parent / ".env"
        if env_pfad.exists():
            load_dotenv(env_pfad, override=False)
    except ImportError:
        pass

    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    return url, key


def ist_konfiguriert() -> bool:
    """Gibt True zurück wenn Supabase-Credentials vorhanden sind."""
    url, key = _lade_credentials()
    return bool(url and key)


def _client():
    """Erstellt einen Supabase-Client. Wirft ValueError wenn nicht konfiguriert."""
    try:
        from supabase import create_client
    except ImportError:
        raise ImportError(
            "supabase-Paket fehlt. Lösung: pip install supabase"
        )
    url, key = _lade_credentials()
    if not url or not key:
        raise ValueError(
            "SUPABASE_URL und SUPABASE_KEY nicht gesetzt.\n"
            "Lokal: in .env eintragen.\n"
            "Streamlit Cloud: unter Settings → Secrets eintragen."
        )
    return create_client(url, key)


# ── Kern-Funktionen ───────────────────────────────────────────────────────────

def speichere_vertrag(zeile: dict) -> bool:
    """
    Speichert einen Vertragseintrag in Supabase.
    Gibt True bei Erfolg zurück, False bei Fehler.
    """
    try:
        client = _client()
        eintrag = {k: zeile.get(k, "") for k in SPALTEN}
        client.table(TABELLE).insert(eintrag).execute()
        return True
    except Exception as e:
        print(f"Supabase-Fehler beim Speichern: {e}")
        return False


def lade_vertraege() -> list[dict]:
    """
    Lädt alle Verträge aus Supabase.
    Gibt eine Liste von Dicts zurück (gleiche Struktur wie CSV-Zeilen).
    """
    try:
        client = _client()
        result = client.table(TABELLE).select("*").order("id", desc=True).execute()
        return result.data or []
    except Exception as e:
        print(f"Supabase-Fehler beim Laden: {e}")
        return []


def loesche_vertrag(eintrag_id: str) -> bool:
    """Löscht einen Vertrag aus Supabase anhand der ID."""
    try:
        client = _client()
        client.table(TABELLE).delete().eq("id", eintrag_id).execute()
        return True
    except Exception as e:
        print(f"Supabase Delete-Fehler: {e}")
        return False


def suche_nach_hash(pdf_hash: str) -> dict | None:
    """Gibt gecachten Vertragseintrag zurück wenn Hash bekannt."""
    try:
        client = _client()
        res = client.table(TABELLE).select("*").eq("pdf_hash", pdf_hash).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def speichere_mit_hash(eintrag: dict, pdf_hash: str) -> bool:
    """Speichert Vertrag inkl. Hash-Fingerprint."""
    eintrag_mit_hash = {**eintrag, "pdf_hash": pdf_hash}
    return speichere_vertrag(eintrag_mit_hash)


def aktualisiere_status(eintrag_id: str, neuer_status: str) -> bool:
    """Setzt den Status-Workflow eines Vertrags."""
    try:
        client = _client()
        client.table(TABELLE).update({"status_workflow": neuer_status}).eq("id", eintrag_id).execute()
        return True
    except Exception as e:
        print(f"Status-Update Fehler: {e}")
        return False


def aktualisiere_tags(eintrag_id: str, tags: str) -> bool:
    """Speichert kommagetrennte Tags für einen Vertrag."""
    try:
        client = _client()
        client.table(TABELLE).update({"tags": tags}).eq("id", eintrag_id).execute()
        return True
    except Exception as e:
        print(f"Tags-Update Fehler: {e}")
        return False


def suche_vertraege(suchbegriff: str, daten: list) -> list:
    """Filtert eine Liste von Vertrags-Dicts nach Suchbegriff (client-seitig)."""
    if not suchbegriff.strip():
        return daten
    sb = suchbegriff.lower()
    felder = ["quelldatei", "partei_a", "partei_b", "vertragstyp", "tags", "notizen"]
    return [
        z for z in daten
        if any(sb in str(z.get(f, "")).lower() for f in felder)
    ]


def aktualisiere_notizen(eintrag_id: str, notizen: str) -> bool:
    """Speichert freie Notizen für einen Vertrag."""
    try:
        client = _client()
        client.table(TABELLE).update({"notizen": notizen}).eq("id", eintrag_id).execute()
        return True
    except Exception as e:
        print(f"Notizen-Update Fehler: {e}")
        return False


def log_aktion(aktion: str, vertrag_id: str = "", quelldatei: str = "", details: str = "") -> None:
    """Schreibt einen Eintrag in den Audit Log. Non-blocking – Fehler werden nur geloggt."""
    try:
        client = _client()
        client.table("audit_log").insert({
            "aktion": aktion,
            "vertrag_id": vertrag_id,
            "quelldatei": quelldatei,
            "details": details,
        }).execute()
    except Exception as e:
        print(f"Audit Log Fehler (non-blocking): {e}")


def sync_csv_zu_supabase(csv_pfad: Path) -> int:
    """
    Einmalige Migration: Importiert bestehende CSV in Supabase.
    Gibt Anzahl importierter Zeilen zurück.
    """
    if not csv_pfad.exists():
        return 0

    try:
        client = _client()
    except Exception as e:
        print(f"Supabase nicht erreichbar: {e}")
        return 0

    importiert = 0
    with open(csv_pfad, encoding="utf-8") as f:
        for zeile in csv.DictReader(f):
            if not (zeile.get("partei_a") or zeile.get("partei_b")):
                continue
            eintrag = {k: zeile.get(k, "") for k in SPALTEN}
            try:
                client.table(TABELLE).insert(eintrag).execute()
                importiert += 1
            except Exception:
                pass

    return importiert


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if not ist_konfiguriert():
        print("Supabase nicht konfiguriert (SUPABASE_URL + SUPABASE_KEY fehlen).")
        sys.exit(1)

    if "--sync" in sys.argv:
        root = Path(__file__).parent.parent
        csv_pfad = root / "output" / "vertrags_datenbank.csv"
        n = sync_csv_zu_supabase(csv_pfad)
        print(f"Migration abgeschlossen: {n} Zeilen in Supabase importiert.")
    else:
        vertraege = lade_vertraege()
        print(f"Verträge in Supabase: {len(vertraege)}")
        for v in vertraege[:5]:
            print(f"  {v.get('quelldatei', '?')} | {v.get('vertragstyp', '?')} | {v.get('partei_a', '?')}")
