# Research Workflow — Strukturiertes Juristisches & Business Research

## Zweck
Systematische Aufbereitung eines juristischen oder regulatorischen Themas für den Einsatz in einer KI-Automatisierungsagentur (Compliance, Vertragsmanagement, Mittelstand).

## Inputs
- `THEMA`: Der konkrete Rechtsbegriff oder Sachverhalt (z. B. "DSGVO Art. 17 – Recht auf Löschung")
- `DATUM`: Wird automatisch gesetzt

## Tool aufrufen
```bash
python tools/research.py "<THEMA>"
```
Öffnet eine Markdown-Datei in `.tmp/` mit leerem Template → Agent befüllt alle 6 Abschnitte.

---

## Abschnitte (auszufüllen)

### 1. Kernaussage
**Was regelt diese Norm / dieses Thema in einem Satz?**
→ Prägnante Zusammenfassung, verständlich ohne Vorkenntnisse.

### 2. Rechtliche Grundlagen
**Welche Gesetze, Artikel, Verordnungen, Urteile sind maßgeblich?**
→ Vollständige Zitate (Artikel, Absatz, Satz), relevante EuGH/BGH-Urteile, Erwägungsgründe.

### 3. Streitpunkte & Auslegungsfragen
**Wo ist das Recht unklar, umstritten oder in Bewegung?**
→ Offene Fragen in Rechtsprechung, divergierende Behördenpositionen, Praxisprobleme.

### 4. Praktische Relevanz
**Was bedeutet das für Unternehmen im Alltag?**
→ Pflichten, Fristen, Bußgeldrisiken, typische Fehler, Checkliste.

### 5. Business-Relevanz KI-Agentur
**Wie betrifft das unsere Agentur und unsere Mittelstandskunden?**
→ Produkt-/Service-Ansätze, Automatisierungspotenzial, Compliance-as-a-Service Chancen, konkrete Use Cases.

### 6. Offene Fragen
**Was ist noch ungeklärt oder braucht weitere Recherche?**
→ Fragen an Rechtsanwalt, noch fehlende Quellen, nächste Rechercheschritte.

---

## Qualitäts-Check
Vor Abschluss prüfen:
- [ ] Alle 6 Abschnitte sind inhaltlich befüllt (keine leeren Platzhalter)
- [ ] Rechtliche Grundlagen enthalten konkrete Artikel und Absätze
- [ ] Abschnitt 5 enthält mindestens einen konkreten KI-Agentur Use Case
- [ ] Offene Fragen sind als echte Fragen formuliert (nicht als Aussagen)

## Edge Cases
- **Thema zu breit:** Einschränken auf einen konkreten Artikel oder Sachverhalt
- **Keine Rechtsprechung vorhanden:** Behördliche Leitlinien (z. B. DSK, BfDI) als Ersatz nutzen
- **Widersprüchliche Quellen:** Im Abschnitt "Streitpunkte" explizit benennen
- **Nicht-EU-Recht:** Hinweis ergänzen, welches nationale Recht gilt
