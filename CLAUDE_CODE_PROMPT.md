# Claude Code Prompt – Research Workflow aufbauen

Kopiere den gesamten Text unterhalb der Trennlinie und füge ihn in
Claude Code (VS Code) ein.

---

## PROMPT ZUM EINFÜGEN:

Ich baue meinen ersten AI-Automatisierungsworkflow nach dem WAT-Framework
(Workflows → Agent → Tools). Mein Projekt heißt "erster AI Workflow" und
liegt in meinem aktuellen VS Code Arbeitsverzeichnis.

Bitte führe folgende Schritte aus:

**Schritt 1: Projektstruktur anlegen**
Erstelle diese Ordnerstruktur im aktuellen Verzeichnis, falls sie noch nicht existiert:
- workflows/
- tools/
- .tmp/

**Schritt 2: Workflow-Datei erstellen**
Erstelle die Datei `workflows/research_workflow.md` mit folgendem Inhalt:

[WORKFLOW-INHALT – siehe unten]

Die Datei beschreibt das SOP (Standard Operating Procedure) für strukturiertes
juristisches und Business-Research. Sie enthält: Zweck, Inputs, 6 Abschnitte
die auszufüllen sind (Kernaussage, Rechtliche Grundlagen, Streitpunkte,
Praktische Relevanz, Business-Relevanz KI-Agentur, Offene Fragen),
sowie Qualitäts-Check und Edge Cases.

**Schritt 3: Python-Tool erstellen**
Erstelle die Datei `tools/research.py`. Das Script:
- Nimmt ein Thema als Kommandozeilen-Argument entgegen
- Erstellt eine strukturierte Markdown-Datei in `.tmp/` mit dem Thema,
  aktuellem Datum und allen 6 leeren Abschnitten als Template
- Gibt den Dateipfad aus

**Schritt 4: Test-Durchlauf**
Führe das Script mit einem Beispielthema aus:
```
python tools/research.py "DSGVO Art. 17 – Recht auf Löschung"
```
Öffne die erstellte Datei und befülle alle 6 Abschnitte vollständig gemäß
dem Workflow in `workflows/research_workflow.md`. Nutze dein Wissen über
deutsches und EU-Recht. Der Abschnitt "Business-Relevanz" soll konkret auf
eine KI-Automatisierungsagentur für Mittelstandsunternehmen (Compliance,
Vertragsmanagement) ausgerichtet sein.

**Schritt 5: Ergebnis zeigen**
Zeige mir:
1. Die fertige Ordnerstruktur
2. Den Inhalt der befüllten Research-Datei
3. Erkläre kurz, was das Script macht und wie ich es zukünftig nutze

Wichtig: Erkläre jeden Schritt kurz während du ihn ausführst, damit ich
verstehe was passiert.
