# QA-Review: Erster echter Pipeline-Test

**Vertrag:** `saas_dienstleistungsvertrag_realistisch.pdf` (5 Seiten, 13 §§, 9.724 Zeichen)
**Modell:** `claude-haiku-4-5-20251001`, max_tokens=8192
**Datum:** 17.04.2026
**Kosten:** $0.0458 USD (ca. 4,2 Cent)

---

## 1. Datenextraktion (strukturierte Felder)

| Feld | Original (PDF) | KI-Analyse | Status |
|---|---|---|---|
| Partei A | Helios Medtech Solutions GmbH, HRB 248193 | Helios Medtech Solutions GmbH, HRB 248193 | korrekt |
| Partei B | Nordlicht Cloud Services AG, HRB 165782 | Nordlicht Cloud Services AG, HRB 165782 | korrekt |
| Vertragsbeginn | 01.06.2026 | 01.06.2026 | korrekt |
| Mindestlaufzeit | 36 Mon., bis 31.05.2029 | 36 Mon., bis 31.05.2029 | korrekt |
| Verlängerung | 12 Mon. automatisch | 12 Mon. automatisch | korrekt |
| Kündigungsfrist ordentl. | 6 Mon. zum Ablauf | 6 Mon. zum Ende Verl.-Periode | korrekt |
| Außerord. Kündigung | § 9 Abs. 1 a–d, 4 Wo. ab Kenntnis | Alle 4 Tatbestände erfasst | korrekt |
| Monatsentgelt | 4.850 EUR netto | 4.850 EUR netto | korrekt |
| Impl.-Pauschale | 18.500 EUR in 40/40/20 | 18.500 EUR in 40/40/20 | korrekt |
| SLA-Verfügbarkeit | 99,5 % | 99,5 % | korrekt |
| Haftungs-Cap | 250k/Ereignis, 500k/Jahr | 250k / 500k | korrekt |
| Datenrückgabe | 60 Tage | 60 Tage | korrekt |
| Vertraulichkeit | 5 Jahre | 5 Jahre | korrekt |
| Datenschutzmeldung | 24 Stunden | 24 Stunden | korrekt |
| Pilot-Mitteilungsfrist | 15.09.2026 | 15.09.2026 | korrekt |
| Zahlungsfrist | 14 Tage | 14 Tage | korrekt |
| Gesamtsumme 36 Mon. | (nicht im Vertrag) | 193.100 EUR netto (4.850×36+18.500) | eigenständig berechnet, korrekt |

Trefferquote Rohdaten: **16/16 (100 %)**

---

## 2. Juristische Analysetiefe

| Kategorie | Anzahl | Bewertung |
|---|---|---|
| Kritische Risiken | 10 | substanziell und vertragsrelevant |
| Mittlere Risiken | 7 | sinnvoll, aber z.T. redundant |
| Handlungsempfehlungen | 20 | sauber nach Muss/Sollte/Kann priorisiert |

Stärken:

- Erkennt Fiktion beim Pilotbetrieb (§ 2 Abs. 3) und deren Bindungswirkung
- Sieht Beweislastproblem bei Datenverlust-Haftung (§ 7 Abs. 4)
- Hebt Asymmetrie zwischen garantierter Verfügbarkeit (99,5 %) und Kündigungsgrund (< 97 %) hervor — das ist ein echtes Senior-Argument
- Fordert Cyber-Haftpflichtversicherung und verknüpft sie mit § 7
- Erkennt fehlendes Abnahmeverfahren bei Implementierungsrate und leitet konkrete Klauselvorschläge ab

---

## 3. Gefundene Fehler / Schwachstellen

| # | Fehler | Schwere | Lokation |
|---|---|---|---|
| 1 | Zeitangabe "SOFORT (vor 17.04.2026)" — das Datum liegt in der Vergangenheit (heute ist der 17.04.2026) | mittel | Prioritäten-Zusammenfassung |
| 2 | Tippfehler "Augtraggeberin" statt "Auftraggeberin" | kosmetisch | Handlungsempfehlung 8 |
| 3 | "§ 307 BGB Umdeutungsrisiko" — juristisch falsch, gemeint ist Transparenzgebot § 307 Abs. 1 S. 2 BGB | juristisch relevant | Risiko 10 |
| 4 | Widerspruch im Vertrag nicht erkannt: § 8 Abs. 3 verlangt Schriftform iSd § 126 BGB, lässt aber gleichzeitig Telefax zu — das ist kein § 126 BGB, sondern § 127 BGB (vereinbarte Schriftform). Ein Senior hätte das gesehen | mittel | unbehandelt |
| 5 | Adressen der Parteien fehlen in der Zusammenfassung (nur HRB-Nr. und GF) | kosmetisch | Abschnitt 1 |
| 6 | Prompt-Caching greift nicht (0 cache_creation / 0 cache_read in Token-Log) — System-Prompt vermutlich unter dem 1024-Token-Minimum für Haiku-Caching | Performance | Token-Log |

---

## 4. Token- und Kosten-Analyse

| Run | max_tokens | Output-Tokens | Kosten | Status |
|---|---|---|---|---|
| 1 | 4096 | 4096 (Limit erreicht) | $0,0254 | Analyse abgeschnitten |
| 2 | 8192 | 8175 | $0,0458 | vollständig |

Ableitungen:

- Bei Haiku 4.5 kostet eine vollständige Vertragsanalyse realistisch ca. **$0,04–0,06**
- Bei 100 Verträgen/Monat: ca. **$4–6**; bei 1.000 Verträgen: **$40–60**. Preismodell bleibt problemlos kalkulierbar
- Caching-Ersparnis (90 % auf System-Prompt) ist aktuell nicht aktiv, daher Budget noch mit Puffer kalkulieren

---

## 5. Datenbank-Status

Nach Pipeline-Lauf 7 Einträge in `vertrags_datenbank.csv`. Davon:

- 2 komplett befüllt (Demo `arbeitsvertrag_demo`, `dienstleistungsvertrag_demo`)
- 1 komplett befüllt (neu: `saas_dienstleistungsvertrag_realistisch`) — **unser Test**
- 4 Einträge enthalten unparsbare Template-Platzhalter ("- **Partei B:**") statt Daten. Das sind Altläufe mit `--no-ki` oder abgebrochenen Runs.

Bug in `vertrags_datenbank.py`: Parser sollte Einträge mit Platzhaltern verwerfen oder als "fehlerhaft" flaggen, nicht in die CSV schreiben.

---

## 6. Gesamtbewertung

Die Pipeline funktioniert End-to-End und produziert auf dem ersten komplexen Vertrag **90–95 % belastbare Ergebnisse**. Die strukturierte Datenextraktion ist einwandfrei, die juristische Tiefenanalyse ist für einen B2B-Erstcheck einsetzbar. Die gefundenen Fehler sind größtenteils kosmetisch; die juristische Unschärfe bei § 307/§ 126/§ 127 BGB ist real, aber nicht geschäftskritisch — ein echter Kunde würde die Analyse ohnehin von einem Anwalt gegenzeichnen lassen.

Was vor dem nächsten Schritt getan werden sollte:

1. `max_tokens=8192` ist jetzt der neue Default (bereits gesetzt)
2. Prompt-Caching-Ursache klären (System-Prompt-Länge prüfen oder Beispiel-Vertrag in den Cache packen)
3. Bug in `vertrags_datenbank.py`: Template-Platzhalter als Fehler werten
4. System-Prompt um zwei Hinweise ergänzen:
   - Aktuelles Datum als Referenz mitgeben (vermeidet Halluzinationen wie „vor 17.04.2026")
   - Explizit prüfen, ob Schriftformklauseln § 126 oder § 127 BGB meinen
