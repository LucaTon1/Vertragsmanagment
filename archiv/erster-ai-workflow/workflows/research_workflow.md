# Workflow: Juristisches & Business Research

## Zweck
Strukturierte Recherche zu einem juristischen oder geschäftlichen Thema.
Output ist eine vollständige Markdown-Datei, die zum Lernen (Studium) und zur
Business-Entwicklung (KI-Agentur) genutzt wird.

---

## Inputs (required)
- `thema`: Das zu recherchierende Thema
  - Beispiel: "DSGVO Art. 17 – Recht auf Löschung"
  - Beispiel: "Vertragsfreiheit im BGB – Grenzen und Schranken"
  - Beispiel: "Automatisierung von Compliance-Prozessen im Mittelstand"

---

## Schritt-für-Schritt-Ausführung

### Schritt 1: Output-Datei initialisieren
```bash
python tools/research.py "THEMA HIER EINGEBEN"
```
→ Erstellt Template-Datei in `.tmp/research_[thema]_[datum].md`

### Schritt 2: Jeden Abschnitt sequenziell befüllen

Arbeite jeden Abschnitt einzeln ab. Gehe nicht zum nächsten, bevor der aktuelle
vollständig und präzise ist.

**Abschnitt 1 – Kernaussage**
- Max. 3 Sätze
- Beantwortet: Was ist das Wesentliche? Was muss man wissen?
- Kein Juristenjargon ohne Erklärung

**Abschnitt 2 – Rechtliche Grundlagen**
- Primärnorm(en) mit Absatz/Nummer
- Verwandte Vorschriften (systematischer Zusammenhang)
- Relevante BGH/EuGH-Rechtsprechung (nur wenn gesichert bekannt)
- Bei EU-Recht: Verhältnis zum nationalen Recht klären

**Abschnitt 3 – Hauptargumente & Streitpunkte**
- Trenne: Was ist unbestritten? Was ist h.M.? Was ist umstritten?
- Bei Streit: welche Meinungen existieren, welche Argumente haben sie?

**Abschnitt 4 – Praktische Relevanz**
- 2–3 konkrete Beispielfälle / typische Konstellationen
- Wer ist in der Praxis betroffen? (Unternehmen, Bürger, Behörden)

**Abschnitt 5 – Business-Relevanz (KI-Agentur)**
- Welches Kundenproblem steckt dahinter?
- Welcher Teil davon ist automatisierbar?
- Welches konkrete Servicepaket könnte man daraus bauen?
- Zielmarkt: Mittelstand München, 20–500 Mitarbeiter

**Abschnitt 6 – Offene Fragen**
- Was konnte nicht abschließend geklärt werden?
- Was muss als eigenes Thema tiefer recherchiert werden?

### Schritt 3: Qualitäts-Check
Bevor du die Datei als "fertig" markierst, prüfe:
- [ ] Kernaussage ist in 3 Sätzen für einen Nicht-Juristen verständlich
- [ ] Business-Relevanz ist konkret (kein "könnte man automatisieren")
- [ ] Offene Fragen sind dokumentiert (nicht weggelassen)
- [ ] Datei-Status von "In Bearbeitung" auf "Abgeschlossen" setzen

---

## Expected Output
Datei: `.tmp/research_[thema-slug]_[YYYYMMDD].md`
Status: Vollständig ausgefüllt, alle 6 Abschnitte befüllt

## Edge Cases
- **Thema zu breit:** Eingrenzen (z.B. "DSGVO Art. 17 Abs. 1 lit. a" statt "DSGVO")
- **Wissen fehlt:** Offene Fragen dokumentieren – nie spekulieren
- **Business-Relevanz unklar:** Frage stellen: "Welches Problem hat ein Mittelständler hier?"
- **Widersprüchliche Quellen:** Beide Positionen dokumentieren, Hauptmeinung markieren
