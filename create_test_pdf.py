#!/usr/bin/env python3
"""Erstellt einen minimalen Test-Vertrag als PDF für den Workflow-Test."""

def create_test_pdf():
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
    except ImportError:
        print("reportlab nicht installiert. Installiere mit: pip install reportlab")
        import sys
        sys.exit(1)

    import os
    os.makedirs(".tmp", exist_ok=True)
    output = ".tmp/test_vertrag.pdf"

    c = canvas.Canvas(output, pagesize=A4)
    width, height = A4

    lines = [
        "DIENSTLEISTUNGSVERTRAG",
        "",
        "zwischen",
        "",
        "Mustermann GmbH, Leopoldstrasse 10, 80802 München",
        "(nachfolgend: Auftraggeber)",
        "",
        "und",
        "",
        "TechService UG, Maximilianstrasse 5, 80539 München",
        "(nachfolgend: Auftragnehmer)",
        "",
        "§ 1 Gegenstand",
        "Der Auftragnehmer erbringt IT-Beratungsleistungen im Bereich",
        "Datenschutz und DSGVO-Compliance.",
        "",
        "§ 2 Vergütung",
        "Die monatliche Vergütung beträgt 2.500 EUR netto.",
        "Zahlung innerhalb von 14 Tagen nach Rechnungsstellung.",
        "",
        "§ 3 Laufzeit und Kündigung",
        "Der Vertrag beginnt am 01.05.2026 und läuft auf unbestimmte Zeit.",
        "Ordentliche Kündigung mit 3 Monaten Frist zum Monatsende.",
        "Außerordentliche Kündigung bei schwerwiegenden Vertragsverletzungen.",
        "",
        "§ 4 Geheimhaltung",
        "Der Auftragnehmer verpflichtet sich zur Verschwiegenheit über alle",
        "betrieblichen Informationen auch nach Vertragsende.",
        "",
        "§ 5 Haftung",
        "Die Haftung des Auftragnehmers ist auf Vorsatz und grobe Fahrlässigkeit",
        "beschränkt. Die maximale Haftungssumme beträgt 10.000 EUR.",
        "",
        "§ 6 Schlussbestimmungen",
        "Gerichtsstand ist München. Es gilt deutsches Recht.",
        "Änderungen bedürfen der Schriftform.",
        "",
        "München, den 15.04.2026",
        "",
        "____________________          ____________________",
        "Mustermann GmbH               TechService UG",
    ]

    y = height - 60
    c.setFont("Helvetica-Bold", 14)
    c.drawString(180, y, lines[0])
    c.setFont("Helvetica", 11)
    y -= 30

    for line in lines[1:]:
        if y < 60:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - 60
        if line.startswith("§"):
            c.setFont("Helvetica-Bold", 11)
        else:
            c.setFont("Helvetica", 11)
        c.drawString(60, y, line)
        y -= 18

    c.save()
    print(f"Test-PDF erstellt: {output}")
    return output

if __name__ == "__main__":
    create_test_pdf()
