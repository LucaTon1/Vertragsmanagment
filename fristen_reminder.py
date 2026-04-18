#!/usr/bin/env python3
"""
Fristen-Reminder – prüft Vertrags-DB auf ablaufende Fristen und sendet E-Mails.

Usage:
    python tools/fristen_reminder.py --check      # Nur anzeigen, keine Mail
    python tools/fristen_reminder.py --send        # Mails senden
    python tools/fristen_reminder.py --dry-run     # Simulieren (Mails ausgeben, nicht senden)
"""

import sys
import os
import csv
import re
import smtplib
import argparse
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# ── Konfiguration ─────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
DB_PFAD_DEFAULT = ROOT / "output" / "vertrags_datenbank.csv"

SCHWELLEN = {
    "KRITISCH": 7,
    "DRINGEND": 30,
    "HINWEIS":  90,
}

MONAT_MAP = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8, "september": 9,
    "oktober": 10, "november": 11, "dezember": 12,
}

# ── SMTP-Konfiguration aus .env ───────────────────────────────────────────────

def _lade_env():
    try:
        from dotenv import load_dotenv
        env_pfad = ROOT / ".env"
        if env_pfad.exists():
            load_dotenv(env_pfad, override=False)
    except ImportError:
        pass


def smtp_konfiguriert() -> bool:
    _lade_env()
    return bool(
        os.environ.get("SMTP_HOST")
        and os.environ.get("SMTP_USER")
        and os.environ.get("SMTP_PASSWORD")
        and os.environ.get("REMINDER_TO")
    )


# ── Datums-Parsing ────────────────────────────────────────────────────────────

def _parse_datum(text: str):
    """Parst ein Datumsfeld in verschiedenen deutschen Formaten."""
    if not text or text.strip() in ("", "-", "–", "Nicht angegeben"):
        return None

    text = text.strip()

    # Format: DD.MM.YYYY
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass

    # Format: YYYY-MM-DD
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass

    # Format: DD. Monatname YYYY (z.B. "31. Mai 2029")
    m = re.search(r"(\d{1,2})\.\s+([A-Za-zäöüÄÖÜ]+)\s+(\d{4})", text)
    if m:
        monat_str = m.group(2).lower()
        monat_nr = MONAT_MAP.get(monat_str)
        if monat_nr:
            try:
                return date(int(m.group(3)), monat_nr, int(m.group(1)))
            except ValueError:
                pass

    # Fallback: dateutil
    try:
        from dateutil import parser as du_parser
        dt = du_parser.parse(text, dayfirst=True)
        return dt.date()
    except Exception:
        pass

    return None


def _kategorisiere(tage: int):
    if tage <= SCHWELLEN["KRITISCH"]:
        return "KRITISCH"
    if tage <= SCHWELLEN["DRINGEND"]:
        return "DRINGEND"
    if tage <= SCHWELLEN["HINWEIS"]:
        return "HINWEIS"
    return None


# ── Kern-Funktion ─────────────────────────────────────────────────────────────

def pruefe_fristen(db_pfad: Path = None) -> list[dict]:
    """
    Liest die Vertrags-DB und gibt eine Liste aller ablaufenden Fristen zurück.
    Jeder Eintrag enthält: quelldatei, vertragstyp, partei_a, partei_b,
    frist_datum, fristtyp, tage_verbleibend, kategorie.
    """
    if db_pfad is None:
        db_pfad = DB_PFAD_DEFAULT

    if not db_pfad.exists():
        return []

    heute = date.today()
    ergebnisse = []

    with open(db_pfad, encoding="utf-8") as f:
        zeilen = list(csv.DictReader(f))

    fristfelder = [
        ("vertragsende", "Vertragsende / Laufzeit"),
        ("kuendigungsfrist", "Kündigungsfrist"),
    ]

    for zeile in zeilen:
        if not (zeile.get("partei_a") or zeile.get("partei_b")):
            continue  # Unvollständige Einträge überspringen

        for feldname, fristtyp in fristfelder:
            rohwert = zeile.get(feldname, "")
            datum = _parse_datum(rohwert)
            if datum is None:
                continue
            if datum < heute:
                continue  # Bereits abgelaufen

            tage = (datum - heute).days
            kategorie = _kategorisiere(tage)
            if kategorie is None:
                continue

            ergebnisse.append({
                "quelldatei":      zeile.get("quelldatei", ""),
                "vertragstyp":     zeile.get("vertragstyp", "")[:60],
                "partei_a":        zeile.get("partei_a", "")[:50],
                "partei_b":        zeile.get("partei_b", "")[:50],
                "frist_datum":     datum.strftime("%d.%m.%Y"),
                "fristtyp":        fristtyp,
                "tage_verbleibend": tage,
                "kategorie":       kategorie,
            })

    # Sortieren: kritischste zuerst
    ergebnisse.sort(key=lambda x: x["tage_verbleibend"])
    return ergebnisse


# ── E-Mail ────────────────────────────────────────────────────────────────────

def _formatiere_mail(frist: dict) -> tuple[str, str]:
    """Gibt (Betreff, Body) zurück."""
    kat = frist["kategorie"]
    betreff = (
        f"[{kat}] Frist läuft ab: "
        f"{frist['vertragstyp'] or frist['quelldatei']} "
        f"({frist['partei_a']} / {frist['partei_b']})"
    )
    body = (
        f"Vertragsmanagement – Automatische Erinnerung\n"
        f"{'─' * 45}\n"
        f"Vertrag:        {frist['vertragstyp'] or 'Unbekannt'}\n"
        f"Parteien:       {frist['partei_a']} / {frist['partei_b']}\n"
        f"Frist läuft ab: {frist['frist_datum']} (in {frist['tage_verbleibend']} Tagen)\n"
        f"Fristtyp:       {frist['fristtyp']}\n"
        f"\n"
        f"Handlung erforderlich: Prüfe Vertrag und reagiere bis {frist['frist_datum']}.\n"
        f"\n"
        f"Quelldatei: {frist['quelldatei']}\n"
        f"{'─' * 45}\n"
        f"Automatisch generiert von Vertragsmanagement v2.0\n"
    )
    return betreff, body


def sende_reminder(frist: dict, dry_run: bool = False) -> bool:
    """
    Sendet eine Reminder-E-Mail. Bei dry_run: nur ausgeben.
    Gibt True bei Erfolg zurück.
    """
    betreff, body = _formatiere_mail(frist)

    if dry_run:
        print(f"\n{'─' * 45}")
        print(f"[DRY-RUN] An: {os.environ.get('REMINDER_TO', '<REMINDER_TO nicht gesetzt>')}")
        print(f"Betreff: {betreff}")
        print(body)
        return True

    _lade_env()
    host     = os.environ.get("SMTP_HOST", "")
    port     = int(os.environ.get("SMTP_PORT", "587"))
    user     = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    empfaenger = os.environ.get("REMINDER_TO", "")

    if not all([host, user, password, empfaenger]):
        print("Warnung: SMTP nicht konfiguriert – falle auf dry-run zurück.")
        return sende_reminder(frist, dry_run=True)

    try:
        msg = MIMEMultipart()
        msg["From"] = user
        msg["To"] = empfaenger
        msg["Subject"] = betreff
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, empfaenger, msg.as_string())
        print(f"Mail gesendet: {betreff[:60]}")
        return True
    except Exception as e:
        print(f"Mail-Fehler: {e}")
        return False


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Fristen-Reminder für Vertragsmanagement"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Fristen anzeigen (keine Mail)"
    )
    parser.add_argument(
        "--send", action="store_true",
        help="Reminder-Mails senden"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Mails simulieren (Inhalt ausgeben, nicht senden)"
    )
    parser.add_argument(
        "--db", default=None,
        help=f"Pfad zur Vertrags-DB CSV (Standard: {DB_PFAD_DEFAULT})"
    )
    args = parser.parse_args()

    db_pfad = Path(args.db) if args.db else DB_PFAD_DEFAULT
    fristen = pruefe_fristen(db_pfad)

    if not fristen:
        print("Keine ablaufenden Fristen in den nächsten 90 Tagen.")
        return

    print(f"\nAblaufende Fristen (nächste 90 Tage):")
    print(f"{'─' * 70}")
    print(f"{'Kategorie':<12} {'Tage':>6}  {'Frist':>12}  {'Typ':<25}  Vertrag")
    print(f"{'─' * 70}")
    for f in fristen:
        print(
            f"{f['kategorie']:<12} {f['tage_verbleibend']:>6}  "
            f"{f['frist_datum']:>12}  {f['fristtyp']:<25}  "
            f"{(f['vertragstyp'] or f['quelldatei'])[:40]}"
        )
    print(f"{'─' * 70}")
    print(f"Gesamt: {len(fristen)} Frist(en)\n")

    if args.send or args.dry_run:
        if args.send and not smtp_konfiguriert():
            print("Warnung: SMTP-Variablen nicht gesetzt – falle auf --dry-run zurück.")
            dry_run = True
        else:
            dry_run = args.dry_run

        for f in fristen:
            sende_reminder(f, dry_run=dry_run)


if __name__ == "__main__":
    main()
