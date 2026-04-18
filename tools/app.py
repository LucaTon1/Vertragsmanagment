#!/usr/bin/env python3
"""
Vertragsmanagement – Streamlit UI

Starten mit: python3 -m streamlit run tools/app.py --server.headless true
"""

import sys
import os
import csv
import traceback
import tempfile
from pathlib import Path
from datetime import datetime

# Pfad-Setup damit lokale Module importierbar sind
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

# ── Seitenkonfiguration ───────────────────────────────────────────────────────

st.set_page_config(
    page_title="Vertragsmanagement",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Pfade ─────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
TMP_DIR = ROOT / ".tmp"
OUTPUT_DIR = ROOT / "output"
DB_PFAD = OUTPUT_DIR / "vertrags_datenbank.csv"
TOKEN_LOG_PFAD = OUTPUT_DIR / "token_log.csv"

TMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚖️ Vertragsmanagement")
    st.markdown("---")
    seite = st.radio(
        "Navigation",
        ["📤 Analyse", "📋 Datenbank", "💰 Kosten"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("v2.0 · WAT-Framework")

# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def lade_csv(pfad: Path) -> list[dict]:
    """Liest CSV sicher; gibt leere Liste bei Fehler zurück."""
    if not pfad.exists():
        return []
    try:
        with open(pfad, encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def modell_id(label: str) -> str:
    mapping = {
        "Haiku 4.5 – schnell (~0,05 $)": "claude-haiku-4-5-20251001",
        "Sonnet 4.6 – präzise (~0,15 $)": "claude-sonnet-4-6",
    }
    return mapping.get(label, "claude-haiku-4-5-20251001")


# ── Seite 1: Analyse ──────────────────────────────────────────────────────────

if seite == "📤 Analyse":
    st.header("Vertrag analysieren")

    uploaded = st.file_uploader(
        "PDF-Vertrag hochladen",
        type=["pdf"],
        help="Einzelne PDF-Datei – max. 200 MB",
    )

    modell_label = st.selectbox(
        "Modell",
        ["Haiku 4.5 – schnell (~0,05 $)", "Sonnet 4.6 – präzise (~0,15 $)"],
        help="Haiku: günstig & schnell. Sonnet: präziser bei komplexen Verträgen.",
    )

    # Modell-Empfehlung basierend auf Dateigröße
    if uploaded is not None:
        groesse_kb = len(uploaded.getvalue()) / 1024
        if groesse_kb > 500:
            st.info(f"Datei ist {groesse_kb:.0f} KB – Sonnet 4.6 empfohlen für lange Verträge.")

    analysieren = st.button("Analysieren", type="primary", disabled=uploaded is None)

    if analysieren and uploaded is not None:
        if not uploaded.name.lower().endswith(".pdf"):
            st.error("Bitte nur PDF-Dateien hochladen.")
        else:
            # PDF in .tmp/ speichern
            pdf_pfad = TMP_DIR / uploaded.name
            pdf_pfad.write_bytes(uploaded.getvalue())

            status_box = st.empty()
            status_box.info("⏳ Analyse läuft...")

            try:
                from ki_analyse import analysiere_vertrag, berechne_kosten, formatiere_token_info
                from utils import extract_text_from_pdf, display_name
                from fristen_extraktor import extrahiere_fristen, kategorien_label
                from generate_report import generiere_report
                from vertrags_datenbank import aktualisiere_db

                rohtext, seiten = extract_text_from_pdf(str(pdf_pfad))

                fristen = extrahiere_fristen(rohtext)
                fristen_hinweise = ""
                if fristen:
                    zeilen = ["<!-- Automatisch erkannt – bitte prüfen -->"]
                    for t in fristen:
                        zeilen.append(f"- {t['match']} ({kategorien_label(t['kategorie'])})")
                    fristen_hinweise = "\n".join(zeilen)

                gewaehltes_modell = modell_id(modell_label)
                analyse_text, token_info = analysiere_vertrag(
                    rohtext=rohtext,
                    vertrag_titel=display_name(pdf_pfad.stem),
                    seiten=seiten,
                    fristen_hinweise=fristen_hinweise,
                    modell=gewaehltes_modell,
                )

                # .md speichern
                datum_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                from utils import slugify
                md_pfad = TMP_DIR / f"vertragsanalyse_{slugify(pdf_pfad.stem)}_{datum_str}.md"
                rohtext_vorschau = rohtext[:3000]
                volltext = (
                    analyse_text
                    + f"\n\n---\n\n## 7. Rohtext (Quelle)\n\n```\n{rohtext_vorschau}\n```\n\n"
                    f"*Vollständiger Rohtext: {len(rohtext)} Zeichen*\n"
                )
                md_pfad.write_text(volltext, encoding="utf-8")

                # HTML-Report
                html_pfad = generiere_report(md_pfad, output_dir=OUTPUT_DIR)

                # Datenbank aktualisieren
                aktualisiere_db(TMP_DIR, DB_PFAD)

                status_box.success(
                    f"Analyse abgeschlossen | Kosten: ~${berechne_kosten(token_info):.4f} | "
                    f"Modell: {token_info.get('modell', '')}"
                )

                # Report anzeigen
                html_inhalt = Path(html_pfad).read_text(encoding="utf-8")
                st.components.v1.html(html_inhalt, height=800, scrolling=True)

                # Download-Button
                st.download_button(
                    label="HTML-Report herunterladen",
                    data=html_inhalt,
                    file_name=Path(html_pfad).name,
                    mime="text/html",
                )

                # DOCX-Download-Button
                try:
                    from generate_report import generiere_docx
                    docx_pfad = generiere_docx(md_pfad, output_dir=OUTPUT_DIR)
                    with open(docx_pfad, "rb") as docx_f:
                        st.download_button(
                            label="Word-Dokument herunterladen (.docx)",
                            data=docx_f.read(),
                            file_name=Path(docx_pfad).name,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        )
                except Exception as e:
                    st.caption(f"DOCX-Export nicht verfügbar: {e}")

                # Token-Details
                with st.expander("Token-Details"):
                    st.code(formatiere_token_info(token_info))

            except ValueError as e:
                status_box.empty()
                fehler_str = str(e)
                if "ANTHROPIC_API_KEY" in fehler_str:
                    st.error(
                        "**API-Key fehlt.** Trage deinen Key in `.env` ein:\n\n"
                        "```\nANTHROPIC_API_KEY=sk-ant-...\n```\n\n"
                        "Key holen: https://console.anthropic.com/settings/keys"
                    )
                else:
                    st.error(f"Fehler: {fehler_str}")
            except Exception as e:
                status_box.empty()
                st.error(f"Pipeline-Fehler: {e}")
                with st.expander("Vollständiger Traceback"):
                    st.code(traceback.format_exc())


# ── Seite 2: Datenbank ────────────────────────────────────────────────────────

elif seite == "📋 Datenbank":
    st.header("Vertrags-Datenbank")

    zeilen = lade_csv(DB_PFAD)
    vollstaendig = [z for z in zeilen if z.get("partei_a") or z.get("partei_b")]

    if not vollstaendig:
        st.info("Noch keine Verträge analysiert. Gehe zu 📤 Analyse.")
    else:
        # Metriken
        heute = datetime.now().strftime("%Y-%m")
        diesen_monat = sum(
            1 for z in vollstaendig
            if z.get("analysedatum", "").startswith(heute)
        )
        abgeschlossen = sum(1 for z in vollstaendig if z.get("status") == "Abgeschlossen")

        col1, col2, col3 = st.columns(3)
        col1.metric("Verträge gesamt", len(vollstaendig))
        col2.metric("Abgeschlossen", abgeschlossen)
        col3.metric("Dieses Monat", diesen_monat)

        # Filter nach Vertragstyp
        typen = sorted({z.get("vertragstyp", "Unbekannt")[:40] for z in vollstaendig})
        gewaehlt = st.selectbox("Filter: Vertragstyp", ["Alle"] + typen)

        gefiltert = vollstaendig if gewaehlt == "Alle" else [
            z for z in vollstaendig if z.get("vertragstyp", "").startswith(gewaehlt)
        ]

        # Angezeigte Spalten
        anzeigespalten = [
            "quelldatei", "analysedatum", "partei_a", "partei_b",
            "vertragstyp", "vertragsbeginn", "vertragsende", "kuendigungsfrist", "status"
        ]
        anzeige = [{k: z.get(k, "") for k in anzeigespalten} for z in gefiltert]
        st.dataframe(anzeige, use_container_width=True)

        # Fristen-Sektion
        st.markdown("---")
        st.subheader("🔔 Ablaufende Fristen")
        try:
            from fristen_reminder import pruefe_fristen
            fristen = pruefe_fristen(DB_PFAD)
            if not fristen:
                st.success("Keine ablaufenden Fristen in den nächsten 90 Tagen.")
            else:
                for f in fristen:
                    farbe = {"KRITISCH": "🔴", "DRINGEND": "🟠", "HINWEIS": "🟡"}.get(f["kategorie"], "⚪")
                    st.markdown(
                        f"{farbe} **{f['kategorie']}** – {f['vertragstyp'] or f['quelldatei']} | "
                        f"Frist: {f['frist_datum']} (in {f['tage_verbleibend']} Tagen) | "
                        f"{f['fristtyp']}"
                    )
        except ImportError:
            st.caption("fristen_reminder.py nicht verfügbar.")
        except Exception as e:
            st.warning(f"Fristen-Check Fehler: {e}")


# ── Seite 3: Kosten ───────────────────────────────────────────────────────────

elif seite == "💰 Kosten":
    st.header("API-Kosten")

    zeilen = lade_csv(TOKEN_LOG_PFAD)

    if not zeilen:
        st.info("Noch keine API-Calls aufgezeichnet. Führe zuerst eine Analyse durch.")
    else:
        # Kosten berechnen
        try:
            gesamt = sum(float(z.get("kosten_usd", 0)) for z in zeilen)
            vertraege = len({z.get("datei", "") for z in zeilen if z.get("datei")})
            durchschnitt = gesamt / len(zeilen) if zeilen else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Gesamtkosten USD", f"${gesamt:.4f}")
            col2.metric("API-Calls", len(zeilen))
            col3.metric("Ø pro Call", f"${durchschnitt:.4f}")
        except (ValueError, ZeroDivisionError):
            pass

        # Tabelle
        st.dataframe(zeilen, use_container_width=True)

        # Linechart: Kosten pro Call über Zeit
        try:
            import json
            chart_daten = []
            for i, z in enumerate(zeilen):
                try:
                    chart_daten.append({
                        "index": i + 1,
                        "kosten": float(z.get("kosten_usd", 0)),
                    })
                except ValueError:
                    pass
            if chart_daten:
                st.subheader("Kosten pro Analyse")
                st.line_chart(
                    data=[d["kosten"] for d in chart_daten],
                    use_container_width=True,
                )
        except Exception:
            pass


# Starten mit: python3 -m streamlit run tools/app.py --server.headless true
