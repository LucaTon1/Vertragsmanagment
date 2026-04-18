#!/usr/bin/env python3
"""Erstellt 4 verschiedene Test-Verträge für den Batch-Test."""

import os
from pathlib import Path


def schreibe_pdf(output_path: str, titel: str, zeilen: list):
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
    except ImportError:
        print("Installiere: pip install reportlab")
        import sys
        sys.exit(1)

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    y = height - 60

    c.setFont("Helvetica-Bold", 13)
    c.drawString(60, y, titel)
    c.setFont("Helvetica", 10)
    y -= 30

    for zeile in zeilen:
        if y < 60:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 60
        if zeile.startswith("§") or zeile.isupper():
            c.setFont("Helvetica-Bold", 10)
        else:
            c.setFont("Helvetica", 10)
        c.drawString(60, y, zeile)
        y -= 16

    c.save()
    print(f"  Erstellt: {output_path}")


def main():
    ordner = Path(".tmp/test_vertraege")
    ordner.mkdir(parents=True, exist_ok=True)

    # Vertrag 1: Dienstleistungsvertrag
    schreibe_pdf(str(ordner / "01_dienstleistungsvertrag.pdf"),
        "DIENSTLEISTUNGSVERTRAG",
        [
            "zwischen Mustermann GmbH, Leopoldstr. 10, 80802 München (Auftraggeber)",
            "und TechService UG, Maximilianstr. 5, 80539 München (Auftragnehmer)",
            "",
            "§ 1 Gegenstand",
            "IT-Beratung im Bereich DSGVO-Compliance.",
            "",
            "§ 2 Vergütung",
            "Monatlich 2.500 EUR netto, zahlbar binnen 14 Tagen.",
            "",
            "§ 3 Laufzeit",
            "Beginn: 01.05.2026. Laufzeit: unbefristet.",
            "Kündigung: 3 Monate zum Monatsende.",
            "",
            "§ 4 Geheimhaltung",
            "Verschwiegenheitspflicht auch nach Vertragsende.",
            "",
            "§ 5 Haftung",
            "Haftung begrenzt auf Vorsatz und grobe Fahrlässigkeit.",
            "Maximale Haftungssumme: 10.000 EUR.",
            "",
            "Gerichtsstand: München. Recht: Deutschland.",
        ]
    )

    # Vertrag 2: Mietvertrag
    schreibe_pdf(str(ordner / "02_mietvertrag.pdf"),
        "MIETVERTRAG",
        [
            "zwischen Schmidt Immobilien GmbH, Sendlinger Str. 20, 80331 München",
            "(Vermieter) und Luca Langer, Nymphenburger Str. 5, 80335 München",
            "(Mieter)",
            "",
            "§ 1 Mietobjekt",
            "3-Zimmer-Wohnung, 75 qm, Nymphenburger Str. 5, 80335 München.",
            "",
            "§ 2 Miete",
            "Kaltmiete: 1.400 EUR. Nebenkosten: 200 EUR. Gesamt: 1.600 EUR.",
            "Fälligkeit: 1. Werktag des Monats.",
            "",
            "§ 3 Mietdauer",
            "Beginn: 01.06.2026. Unbefristet.",
            "Kündigung durch Mieter: 3 Monate. Vermieter: gesetzliche Fristen.",
            "",
            "§ 4 Kaution",
            "3 Monatskaltmieten = 4.200 EUR, zahlbar bis 01.06.2026.",
            "",
            "§ 5 Schönheitsreparaturen",
            "Mieter trägt Schönheitsreparaturen bei Auszug.",
            "",
            "Gerichtsstand: München.",
        ]
    )

    # Vertrag 3: Kaufvertrag
    schreibe_pdf(str(ordner / "03_kaufvertrag.pdf"),
        "KAUFVERTRAG",
        [
            "zwischen Elektronik AG, Rosenheimer Str. 145, 81671 München (Verkäufer)",
            "und Büro Solutions GmbH, Tal 12, 80331 München (Käufer)",
            "",
            "§ 1 Kaufgegenstand",
            "50 Laptops Modell ProBook 450, inkl. 3 Jahre Garantie.",
            "",
            "§ 2 Kaufpreis",
            "Gesamtpreis: 62.500 EUR netto (1.250 EUR pro Stück).",
            "Zahlung: 50% bei Bestellung, 50% bei Lieferung.",
            "",
            "§ 3 Lieferung",
            "Liefertermin: 15.05.2026. Lieferung frei Haus München.",
            "Verzug: 0,5% Vertragsstrafe pro Woche, max. 5%.",
            "",
            "§ 4 Gewährleistung",
            "Gewährleistung: 24 Monate ab Lieferdatum.",
            "",
            "§ 5 Eigentumsvorbehalt",
            "Ware bleibt bis vollständiger Bezahlung Eigentum des Verkäufers.",
            "",
            "Gerichtsstand: München.",
        ]
    )

    # Vertrag 4: Arbeitsvertrag
    schreibe_pdf(str(ordner / "04_arbeitsvertrag.pdf"),
        "ARBEITSVERTRAG",
        [
            "zwischen Consulting GmbH, Theatinerstr. 8, 80333 München (Arbeitgeber)",
            "und Max Müller, Schwabing, München (Arbeitnehmer)",
            "",
            "§ 1 Beginn und Tätigkeit",
            "Beginn: 01.07.2026. Tätigkeit: Junior-Berater.",
            "",
            "§ 2 Probezeit",
            "Probezeit: 6 Monate. Kündigung in Probezeit: 2 Wochen.",
            "",
            "§ 3 Arbeitszeit",
            "40 Stunden pro Woche. Überstunden nach Absprache.",
            "",
            "§ 4 Vergütung",
            "Bruttogehalt: 42.000 EUR jährlich, zahlbar monatlich.",
            "Bonus: bis 10% nach Zielerreichung.",
            "",
            "§ 5 Kündigung",
            "Nach Probezeit: 4 Wochen zum Monatsende.",
            "Nach 2 Jahren: 2 Monate zum Monatsende.",
            "",
            "§ 6 Wettbewerbsverbot",
            "12 Monate nach Austritt, Ausgleich 50% des Gehalts.",
            "",
            "Gerichtsstand: München.",
        ]
    )

    print(f"\n4 Test-Vertraege erstellt in: {ordner.resolve()}")
    print(f"Jetzt testen mit:")
    print(f"  python tools/batch_vertragsanalyse.py {ordner}")


if __name__ == "__main__":
    main()
