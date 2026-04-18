#!/usr/bin/env python3
"""
Erstellt einen realistischen Test-Vertrag (SaaS-Dienstleistungsvertrag),
ca. 10 Seiten, verschachtelte Fristen, mehrere Kuendigungsvarianten,
Haftungsabstufungen, SLA, Datenschutz, AGB-Verweis.

Zweck: Aussagekraeftiger Pipeline-Test mit Vertrag, der typischen
B2B-Komplexitaet entspricht.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
)
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
import os

OUTPUT = ".tmp/saas_dienstleistungsvertrag_realistisch.pdf"

# HTML-Entities fuer deutsche Anfuehrungszeichen, damit ReportLab sie sauber rendert
LQ = "&#8222;"  # Anfuehrung unten (kleine 99)
RQ = "&#8220;"  # Anfuehrung oben (kleine 66)
DASH = "&#8211;"  # Halbgeviertstrich
EMDASH = "&#8212;"  # Geviertstrich

def build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="H1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=14,
    ))
    styles.add(ParagraphStyle(
        name="H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        spaceBefore=10,
        spaceAfter=6,
    ))
    return styles


def para(text, style):
    return Paragraph(text, style)


def build_story(s):
    st = []

    # Titel
    st.append(para("SOFTWARE- UND DIENSTLEISTUNGSVERTRAG", s["H1"]))
    st.append(para(
        "Vertragsnummer: SDV-2026-0417-1138<br/>"
        "Abgeschlossen zwischen:", s["Body"]))
    st.append(Spacer(1, 0.3 * cm))

    st.append(para(
        f"<b>Helios Medtech Solutions GmbH</b>, eingetragen im Handelsregister "
        f"des Amtsgerichts M&uuml;nchen unter HRB 248193, "
        f"Gesch&auml;ftsanschrift: Nymphenburger Stra&szlig;e 86, 80636 M&uuml;nchen, "
        f"vertreten durch die Gesch&auml;ftsf&uuml;hrer Dr. Sabine Hartwig und Jonas Kr&auml;mer "
        f"{EMDASH} nachfolgend <b>{LQ}Auftraggeberin{RQ}</b> genannt {EMDASH}",
        s["Body"]))
    st.append(Spacer(1, 0.2 * cm))
    st.append(para("und", s["Body"]))
    st.append(Spacer(1, 0.2 * cm))
    st.append(para(
        f"<b>Nordlicht Cloud Services AG</b>, eingetragen im Handelsregister "
        f"des Amtsgerichts Hamburg unter HRB 165782, "
        f"Gesch&auml;ftsanschrift: Alstertor 9, 20095 Hamburg, "
        f"vertreten durch den Vorstand Markus Bergmann "
        f"{EMDASH} nachfolgend <b>{LQ}Auftragnehmerin{RQ}</b> genannt {EMDASH}",
        s["Body"]))
    st.append(Spacer(1, 0.2 * cm))
    st.append(para(
        f"{EMDASH} Auftraggeberin und Auftragnehmerin nachfolgend einzeln {LQ}Partei{RQ}, "
        f"gemeinsam {LQ}Parteien{RQ} {EMDASH}", s["Body"]))

    # Paragraph 1
    st.append(para("&sect; 1 Vertragsgegenstand", s["H2"]))
    st.append(para(
        f"(1) Die Auftragnehmerin stellt der Auftraggeberin die cloudbasierte "
        f"Software {LQ}MediSecure Vault{RQ} (nachfolgend <b>{LQ}Software{RQ}</b>) zur "
        f"Verwaltung, Speicherung und Analyse medizinischer Dokumente gem&auml;&szlig; "
        f"Leistungsbeschreibung in Anlage 1 zur Verf&uuml;gung.",
        s["Body"]))
    st.append(para(
        "(2) Zus&auml;tzlich erbringt die Auftragnehmerin Implementierungs-, "
        "Schulungs- und Wartungsleistungen nach Ma&szlig;gabe der Anlage 2 "
        "(Service Level Agreement &#8212; SLA).",
        s["Body"]))
    st.append(para(
        "(3) Erg&auml;nzend gelten die Allgemeinen Gesch&auml;ftsbedingungen der "
        "Auftragnehmerin in der Fassung vom 01.02.2026 (Anlage 3), soweit "
        "dieser Vertrag keine abweichenden Regelungen enth&auml;lt. Im Falle von "
        "Widerspr&uuml;chen gehen die Regelungen dieses Vertrages den AGB vor.",
        s["Body"]))

    # Paragraph 2
    st.append(para("&sect; 2 Laufzeit", s["H2"]))
    st.append(para(
        "(1) Der Vertrag beginnt am <b>01.06.2026</b> (Vertragsbeginn) und wird "
        "auf eine Mindestlaufzeit von <b>36 Monaten</b> abgeschlossen. "
        "Die Mindestlaufzeit endet mit Ablauf des 31.05.2029.",
        s["Body"]))
    st.append(para(
        "(2) Der Vertrag verl&auml;ngert sich nach Ablauf der Mindestlaufzeit "
        "automatisch jeweils um weitere <b>12 Monate</b>, sofern er nicht mit "
        "einer Frist von <b>6 Monaten zum Ablauf</b> der jeweiligen Laufzeit "
        "schriftlich gek&uuml;ndigt wird.",
        s["Body"]))
    st.append(para(
        "(3) Der Pilotbetrieb gem&auml;&szlig; Anlage 1 Ziffer 4 endet am 31.08.2026. "
        "Bis sp&auml;testens <b>15.09.2026</b> teilt die Auftraggeberin schriftlich "
        "mit, ob sie den Produktivbetrieb aufnimmt. Unterbleibt diese "
        "Mitteilung, gilt der Produktivbetrieb als aufgenommen.",
        s["Body"]))

    # Paragraph 3
    st.append(para("&sect; 3 Verg&uuml;tung und Zahlungsbedingungen", s["H2"]))
    st.append(para(
        "(1) Die Auftraggeberin zahlt f&uuml;r die Nutzung der Software ein "
        "monatliches Entgelt von <b>4.850,00 EUR netto</b> zzgl. der jeweils "
        "geltenden gesetzlichen Umsatzsteuer.",
        s["Body"]))
    st.append(para(
        "(2) Die einmalige Implementierungspauschale betr&auml;gt "
        "<b>18.500,00 EUR netto</b> und wird in drei Raten f&auml;llig: "
        "40 % bei Vertragsunterzeichnung, 40 % nach Abschluss der "
        "Systemintegration, 20 % nach erfolgreicher Abnahme.",
        s["Body"]))
    st.append(para(
        "(3) Rechnungen sind innerhalb von <b>14 Tagen nach Zugang</b> ohne "
        "Abzug zur Zahlung f&auml;llig. Bei Zahlungsverzug schuldet die Auftraggeberin "
        "Verzugszinsen in H&ouml;he von 9 Prozentpunkten &uuml;ber dem Basiszinssatz "
        "(&sect; 288 Abs. 2 BGB).",
        s["Body"]))
    st.append(para(
        "(4) Die Auftragnehmerin ist berechtigt, die monatlichen Entgelte mit "
        "einer Vorank&uuml;ndigungsfrist von 3 Monaten, erstmals nach Ablauf der "
        "Mindestlaufzeit, einmal j&auml;hrlich um bis zu maximal die Steigerung des "
        "Verbraucherpreisindex (VPI, Basis 2020=100) anzupassen.",
        s["Body"]))

    st.append(PageBreak())

    # Paragraph 4
    st.append(para("&sect; 4 Service Level Agreement (SLA)", s["H2"]))
    st.append(para(
        "(1) Die Auftragnehmerin garantiert eine Systemverf&uuml;gbarkeit der "
        "Software von <b>99,5 %</b> im Monatsmittel, gemessen 24/7 au&szlig;erhalb "
        "der in Anlage 2 definierten Wartungsfenster.",
        s["Body"]))
    st.append(para(
        "(2) Wartungsfenster liegen regelm&auml;&szlig;ig sonntags zwischen 02:00 und "
        "06:00 Uhr MEZ/MESZ und werden mit mindestens 72 Stunden "
        "Vorank&uuml;ndigung per E-Mail angek&uuml;ndigt.",
        s["Body"]))
    st.append(para(
        "(3) Reaktionszeiten f&uuml;r St&ouml;rungsmeldungen:", s["Body"]))
    st.append(para(
        "&nbsp;&nbsp;&bull; <b>Priorit&auml;t 1 (Totalausfall)</b>: Reaktion innerhalb "
        "1 Stunde, Wiederherstellung sp&auml;testens innerhalb 4 Stunden.<br/>"
        "&nbsp;&nbsp;&bull; <b>Priorit&auml;t 2 (eingeschr&auml;nkte Nutzung)</b>: Reaktion "
        "innerhalb 4 Stunden, Behebung innerhalb 24 Stunden.<br/>"
        "&nbsp;&nbsp;&bull; <b>Priorit&auml;t 3 (geringf&uuml;gige St&ouml;rung)</b>: Reaktion "
        "innerhalb 1 Werktag, Behebung innerhalb 5 Werktagen.",
        s["Body"]))
    st.append(para(
        "(4) Bei Unterschreitung der Verf&uuml;gbarkeit gew&auml;hrt die Auftragnehmerin "
        "eine Gutschrift auf das Folgemonatsentgelt in H&ouml;he von 5 % je angefangenen "
        "0,5 Prozentpunkten Unterschreitung, maximal jedoch 50 % des Monatsentgelts.",
        s["Body"]))

    # Paragraph 5
    st.append(para("&sect; 5 Datenschutz und Vertraulichkeit", s["H2"]))
    st.append(para(
        "(1) Die Parteien schlie&szlig;en zeitgleich mit diesem Vertrag einen "
        "Auftragsverarbeitungsvertrag (AVV) gem&auml;&szlig; Art. 28 DSGVO ab (Anlage 4).",
        s["Body"]))
    st.append(para(
        "(2) Die Auftragnehmerin verarbeitet personenbezogene Daten "
        "ausschlie&szlig;lich innerhalb der Europ&auml;ischen Union. Eine &Uuml;bermittlung in "
        "Drittl&auml;nder ist nur mit vorheriger schriftlicher Zustimmung der "
        "Auftraggeberin und unter Einhaltung der Art. 44 ff. DSGVO zul&auml;ssig.",
        s["Body"]))
    st.append(para(
        "(3) Die Parteien verpflichten sich, alle im Rahmen dieses Vertrages "
        "erlangten Informationen, die als vertraulich gekennzeichnet sind oder "
        "ihrer Natur nach als vertraulich anzusehen sind, geheim zu halten. "
        "Diese Pflicht gilt f&uuml;r einen Zeitraum von <b>5 Jahren</b> nach "
        "Beendigung dieses Vertrages fort.",
        s["Body"]))
    st.append(para(
        "(4) Meldungen &uuml;ber Datenschutzvorf&auml;lle erfolgen unverz&uuml;glich, "
        "sp&auml;testens innerhalb von <b>24 Stunden</b> nach Kenntniserlangung.",
        s["Body"]))

    # Paragraph 6
    st.append(para("&sect; 6 Mitwirkungspflichten", s["H2"]))
    st.append(para(
        "(1) Die Auftraggeberin stellt der Auftragnehmerin alle f&uuml;r die "
        "Leistungserbringung erforderlichen Informationen, Zug&auml;nge und "
        "Testdaten rechtzeitig zur Verf&uuml;gung.",
        s["Body"]))
    st.append(para(
        "(2) Die Auftraggeberin benennt einen qualifizierten Ansprechpartner "
        "sowie einen Stellvertreter, die f&uuml;r die Dauer der Vertragslaufzeit zur "
        "Verf&uuml;gung stehen.",
        s["Body"]))
    st.append(para(
        "(3) Kommt die Auftraggeberin ihren Mitwirkungspflichten trotz "
        "schriftlicher Aufforderung mit angemessener Fristsetzung nicht nach, "
        "ist die Auftragnehmerin berechtigt, daraus entstehenden Mehraufwand "
        "nach Aufwand zu verg&uuml;ten.",
        s["Body"]))

    st.append(PageBreak())

    # Paragraph 7
    st.append(para("&sect; 7 Haftung", s["H2"]))
    st.append(para(
        "(1) Die Auftragnehmerin haftet unbeschr&auml;nkt f&uuml;r Sch&auml;den aus der "
        "Verletzung des Lebens, des K&ouml;rpers oder der Gesundheit, die auf einer "
        "vors&auml;tzlichen oder fahrl&auml;ssigen Pflichtverletzung beruhen, sowie f&uuml;r "
        "sonstige Sch&auml;den, die auf Vorsatz oder grober Fahrl&auml;ssigkeit beruhen.",
        s["Body"]))
    st.append(para(
        "(2) F&uuml;r leicht fahrl&auml;ssig verursachte Sch&auml;den haftet die Auftragnehmerin "
        "nur bei Verletzung wesentlicher Vertragspflichten (Kardinalpflichten). "
        "In diesem Fall ist die Haftung pro Schadensereignis auf "
        "<b>250.000,00 EUR</b>, insgesamt je Vertragsjahr auf "
        "<b>500.000,00 EUR</b>, begrenzt.",
        s["Body"]))
    st.append(para(
        "(3) Die Haftung f&uuml;r entgangenen Gewinn, mittelbare Sch&auml;den sowie "
        "Folgesch&auml;den ist &#8212; au&szlig;er in F&auml;llen des Absatzes 1 &#8212; ausgeschlossen.",
        s["Body"]))
    st.append(para(
        "(4) F&uuml;r den Verlust von Daten haftet die Auftragnehmerin nur in dem "
        "Umfang, in dem auch bei ordnungsgem&auml;&szlig;er und regelm&auml;&szlig;iger "
        "Datensicherung durch die Auftraggeberin Datenverluste entstanden w&auml;ren.",
        s["Body"]))

    # Paragraph 8
    st.append(para("&sect; 8 Ordentliche K&uuml;ndigung", s["H2"]))
    st.append(para(
        "(1) W&auml;hrend der Mindestlaufzeit nach &sect; 2 Absatz 1 ist die ordentliche "
        "K&uuml;ndigung ausgeschlossen.",
        s["Body"]))
    st.append(para(
        "(2) Nach Ablauf der Mindestlaufzeit kann der Vertrag mit einer Frist "
        "von <b>6 Monaten zum Ende</b> der jeweiligen Verl&auml;ngerungsperiode "
        "ordentlich gek&uuml;ndigt werden.",
        s["Body"]))
    st.append(para(
        "(3) K&uuml;ndigungen bed&uuml;rfen der Schriftform im Sinne des &sect; 126 BGB. "
        "Die &Uuml;bermittlung per Telefax oder als elektronisch signiertes PDF ist "
        "ausreichend. E-Mail ohne qualifizierte elektronische Signatur gen&uuml;gt "
        "nicht.",
        s["Body"]))

    # Paragraph 9
    st.append(para("&sect; 9 Au&szlig;erordentliche K&uuml;ndigung", s["H2"]))
    st.append(para(
        "(1) Das Recht zur au&szlig;erordentlichen K&uuml;ndigung aus wichtigem Grund "
        "bleibt unber&uuml;hrt. Ein wichtiger Grund liegt insbesondere vor, wenn:",
        s["Body"]))
    st.append(para(
        "&nbsp;&nbsp;a) die andere Partei gegen wesentliche Vertragspflichten "
        "verst&ouml;&szlig;t und diesen Versto&szlig; nicht innerhalb einer angemessenen "
        "Nachfrist von mindestens 30 Tagen nach schriftlicher Abmahnung beseitigt;",
        s["Body"]))
    st.append(para(
        "&nbsp;&nbsp;b) die andere Partei mit f&auml;lligen Zahlungen von mehr als "
        "zwei Monatsentgelten in Verzug ist;",
        s["Body"]))
    st.append(para(
        "&nbsp;&nbsp;c) &uuml;ber das Verm&ouml;gen der anderen Partei ein Insolvenzverfahren "
        "er&ouml;ffnet oder mangels Masse abgelehnt wird;",
        s["Body"]))
    st.append(para(
        "&nbsp;&nbsp;d) die Verf&uuml;gbarkeit gem&auml;&szlig; &sect; 4 Absatz 1 in drei "
        "aufeinanderfolgenden Kalendermonaten unter 97 % liegt.",
        s["Body"]))
    st.append(para(
        "(2) Die au&szlig;erordentliche K&uuml;ndigung muss innerhalb von 4 Wochen ab "
        "Kenntnis vom K&uuml;ndigungsgrund erkl&auml;rt werden.",
        s["Body"]))

    st.append(PageBreak())

    # Paragraph 10
    st.append(para("&sect; 10 Datenr&uuml;ckgabe und Datenl&ouml;schung", s["H2"]))
    st.append(para(
        "(1) Nach Vertragsende stellt die Auftragnehmerin der Auftraggeberin "
        "s&auml;mtliche Daten f&uuml;r einen Zeitraum von <b>60 Tagen</b> im g&auml;ngigen "
        "Exportformat (JSON, CSV) zum Download bereit.",
        s["Body"]))
    st.append(para(
        "(2) Nach Ablauf dieser Frist werden die Daten vollst&auml;ndig und "
        "unwiderruflich gel&ouml;scht. Die L&ouml;schung wird der Auftraggeberin "
        "schriftlich best&auml;tigt.",
        s["Body"]))
    st.append(para(
        "(3) Gesetzliche Aufbewahrungspflichten bleiben unber&uuml;hrt.",
        s["Body"]))

    # Paragraph 11
    st.append(para("&sect; 11 Geistige Eigentumsrechte", s["H2"]))
    st.append(para(
        "(1) Die Auftragnehmerin r&auml;umt der Auftraggeberin f&uuml;r die Dauer des "
        "Vertrages ein nicht ausschlie&szlig;liches, nicht &uuml;bertragbares und nicht "
        "unterlizenzierbares Nutzungsrecht an der Software ein.",
        s["Body"]))
    st.append(para(
        "(2) Die Auftraggeberin bleibt Inhaberin aller Rechte an den von ihr "
        "in die Software eingestellten Daten und Inhalten.",
        s["Body"]))
    st.append(para(
        "(3) Individualentwicklungen, die im Rahmen dieses Vertrages f&uuml;r die "
        "Auftraggeberin erstellt werden, gehen mit vollst&auml;ndiger Zahlung der "
        "vereinbarten Verg&uuml;tung in das Eigentum der Auftraggeberin &uuml;ber. "
        "Vorbestehende Komponenten der Auftragnehmerin bleiben davon ausgenommen.",
        s["Body"]))

    # Paragraph 12
    st.append(para("&sect; 12 &Auml;nderungen und Erg&auml;nzungen", s["H2"]))
    st.append(para(
        "(1) &Auml;nderungen und Erg&auml;nzungen dieses Vertrages bed&uuml;rfen zu ihrer "
        "Wirksamkeit der Schriftform. Dies gilt auch f&uuml;r die &Auml;nderung oder "
        "Aufhebung dieser Schriftformklausel selbst.",
        s["Body"]))
    st.append(para(
        "(2) M&uuml;ndliche Nebenabreden bestehen nicht.",
        s["Body"]))

    # Paragraph 13
    st.append(para("&sect; 13 Schlussbestimmungen", s["H2"]))
    st.append(para(
        "(1) Erf&uuml;llungsort und ausschlie&szlig;licher Gerichtsstand f&uuml;r alle "
        "Streitigkeiten aus oder im Zusammenhang mit diesem Vertrag ist "
        "<b>M&uuml;nchen</b>, sofern die Auftraggeberin Kaufmann im Sinne des HGB ist.",
        s["Body"]))
    st.append(para(
        "(2) Auf diesen Vertrag findet ausschlie&szlig;lich das Recht der "
        "Bundesrepublik Deutschland unter Ausschluss des UN-Kaufrechts (CISG) "
        "Anwendung.",
        s["Body"]))
    st.append(para(
        "(3) Sollten einzelne Bestimmungen dieses Vertrages unwirksam oder "
        "undurchf&uuml;hrbar sein oder werden, so bleibt die Wirksamkeit der &uuml;brigen "
        "Bestimmungen hiervon unber&uuml;hrt. An die Stelle der unwirksamen oder "
        "undurchf&uuml;hrbaren Bestimmung tritt diejenige wirksame und durchf&uuml;hrbare "
        "Regelung, deren Wirkungen der wirtschaftlichen Zielsetzung am n&auml;chsten "
        "kommen, die die Parteien mit der unwirksamen bzw. undurchf&uuml;hrbaren "
        "Bestimmung verfolgt haben.",
        s["Body"]))

    st.append(Spacer(1, 1 * cm))

    # Unterschriften
    st.append(para(
        "M&uuml;nchen / Hamburg, den 17.04.2026",
        s["Body"]))
    st.append(Spacer(1, 1.5 * cm))
    st.append(para(
        "_______________________________________ &nbsp;&nbsp;&nbsp;&nbsp;"
        "_______________________________________<br/>"
        "Dr. Sabine Hartwig &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "&nbsp;&nbsp;&nbsp;&nbsp; Markus Bergmann<br/>"
        "Helios Medtech Solutions GmbH &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Nordlicht Cloud Services AG",
        s["Body"]))

    return st


def main():
    os.makedirs(".tmp", exist_ok=True)
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="Software- und Dienstleistungsvertrag",
    )
    styles = build_styles()
    doc.build(build_story(styles))
    size_kb = os.path.getsize(OUTPUT) / 1024
    print(f"Realistisches Test-PDF erstellt: {OUTPUT} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
