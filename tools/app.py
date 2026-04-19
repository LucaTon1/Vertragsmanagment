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

# ── Datenbank-Backend ─────────────────────────────────────────────────────────
# Supabase wenn konfiguriert, sonst lokale CSV

try:
    from supabase_db import ist_konfiguriert as _sb_ok, lade_vertraege as _sb_lade, speichere_vertrag as _sb_speichere
    SUPABASE_AKTIV = _sb_ok()
except ImportError:
    SUPABASE_AKTIV = False

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚖️ Vertragsmanagement")
    st.markdown("---")
    seite = st.radio(
        "Navigation",
        ["📤 Analyse", "📋 Datenbank", "📊 Analytics", "⚖️ Vergleich", "💰 Kosten"],
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

    batch_modus = st.checkbox("🗂️ Batch-Modus (mehrere PDFs gleichzeitig)")

    if batch_modus:
        uploaded_files = st.file_uploader(
            "PDFs hochladen (mehrere möglich)",
            type=["pdf"],
            accept_multiple_files=True,
            help="Alle PDFs werden sequenziell analysiert.",
        )
        uploaded = None
    else:
        uploaded_files = []
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

    dsgvo_modus = st.checkbox(
        "⚖️ DSGVO-Check zusätzlich durchführen",
        help="Analysiert den Vertrag zusätzlich auf DSGVO-Konformität. Kleiner Extra-API-Call (~0,02 $)."
    )

    analysieren = st.button("Analysieren", type="primary", disabled=uploaded is None)

    batch_analysieren = st.button(
        f"Alle {len(uploaded_files)} PDFs analysieren",
        type="primary",
        disabled=len(uploaded_files) == 0,
    ) if batch_modus else False

    if analysieren and uploaded is not None:
        if not uploaded.name.lower().endswith(".pdf"):
            st.error("Bitte nur PDF-Dateien hochladen.")
        else:
            # PDF in .tmp/ speichern
            pdf_pfad = TMP_DIR / uploaded.name
            pdf_pfad.write_bytes(uploaded.getvalue())

            import hashlib
            pdf_hash = hashlib.sha256(uploaded.getvalue()).hexdigest()

            if SUPABASE_AKTIV:
                try:
                    from supabase_db import suche_nach_hash as _sb_suche_hash
                    cached = _sb_suche_hash(pdf_hash)
                    if cached:
                        st.success(
                            f"✅ Identische PDF bereits analysiert (Hash-Match). "
                            f"Gespeichertes Ergebnis aus Datenbank geladen. Kein API-Call nötig."
                        )
                        st.json({k: v for k, v in cached.items() if k not in ("id", "pdf_hash")})
                        st.stop()
                except Exception:
                    pass

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

                from ki_analyse import extrahiere_risiko_score
                risiko = extrahiere_risiko_score(analyse_text)

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

                # Datenbank aktualisieren (CSV immer; Supabase zusätzlich wenn aktiv)
                aktualisiere_db(TMP_DIR, DB_PFAD)
                if SUPABASE_AKTIV:
                    try:
                        from vertrags_datenbank import parse_analyse_datei
                        from supabase_db import speichere_mit_hash as _sb_speichere_mit_hash
                        eintrag = parse_analyse_datei(md_pfad)
                        if eintrag.get("partei_a") or eintrag.get("partei_b"):
                            eintrag["risiko_score"] = risiko["risiko_score"]
                            eintrag["risiko_begruendung"] = risiko["risiko_begruendung"]
                            _sb_speichere_mit_hash(eintrag, pdf_hash)
                    except Exception:
                        pass

                status_box.success(
                    f"Analyse abgeschlossen | Kosten: ~${berechne_kosten(token_info):.4f} | "
                    f"Modell: {token_info.get('modell', '')}"
                )
                if SUPABASE_AKTIV:
                    from supabase_db import log_aktion
                    log_aktion("ANALYSE", quelldatei=uploaded.name, details=f"Modell: {gewaehltes_modell}, Score: {risiko.get('risiko_score','')}")

                score_emoji = {"GRÜN": "🟢", "GELB": "🟡", "ROT": "🔴"}.get(risiko["risiko_score"], "⚪")
                st.markdown(f"### {score_emoji} Risiko-Score: **{risiko['risiko_score']}**")
                if risiko["risiko_begruendung"]:
                    st.caption(risiko["risiko_begruendung"])

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

                # DSGVO-Check
                if dsgvo_modus:
                    st.markdown("---")
                    st.subheader("⚖️ DSGVO-Check")
                    with st.spinner("DSGVO-Analyse läuft..."):
                        try:
                            from ki_analyse import dsgvo_check, berechne_kosten
                            dsgvo_text, dsgvo_token_info = dsgvo_check(rohtext, gewaehltes_modell)
                            dsgvo_kosten = berechne_kosten(dsgvo_token_info)
                            if "KONFORM" in dsgvo_text:
                                st.success("✅ DSGVO-Bewertung: KONFORM")
                            elif "KRITISCH" in dsgvo_text:
                                st.error("🔴 DSGVO-Bewertung: KRITISCH")
                            else:
                                st.warning("🟡 DSGVO-Bewertung: PRÜFBEDARF")
                            st.markdown(dsgvo_text)
                            st.caption(f"DSGVO-Check Kosten: ~${dsgvo_kosten:.4f}")
                            from utils import slugify
                            st.download_button(
                                "DSGVO-Report herunterladen (.md)",
                                data=dsgvo_text.encode("utf-8"),
                                file_name=f"dsgvo_check_{slugify(pdf_pfad.stem)}.md",
                                mime="text/markdown",
                            )
                        except Exception as e:
                            st.error(f"DSGVO-Check Fehler: {e}")

                # Rohtext für Q&A in Session State halten
                st.session_state["letzter_rohtext"] = rohtext
                st.session_state["letztes_modell"] = gewaehltes_modell

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

    # Q&A Interface (persistiert über Analyse hinaus)
    if "letzter_rohtext" in st.session_state:
        st.markdown("---")
        st.subheader("💬 Fragen zum Vertrag")
        st.caption("Stelle eine konkrete Frage zu diesem Vertrag. (Haiku 4.5, gecacht – günstig)")
        with st.form("qa_form", clear_on_submit=True):
            frage = st.text_input(
                "Frage zum Vertrag",
                placeholder="z.B. 'Welche Kündigungsfrist gilt?' oder 'Gibt es eine Haftungsbeschränkung?'"
            )
            qa_senden = st.form_submit_button("Fragen")
        if qa_senden and frage.strip():
            try:
                from ki_analyse import beantworte_frage
                with st.spinner("Analysiere..."):
                    antwort = beantworte_frage(
                        rohtext=st.session_state["letzter_rohtext"],
                        frage=frage,
                        modell=st.session_state.get("letztes_modell", "claude-haiku-4-5-20251001"),
                    )
                st.info(f"**Frage:** {frage}\n\n**Antwort:** {antwort}")
            except Exception as e:
                st.error(f"Q&A Fehler: {e}")

    if batch_analysieren and uploaded_files:
        progress = st.progress(0, text="Batch-Analyse läuft...")
        gesamt_kosten = 0.0
        ergebnisse = []

        for i, up in enumerate(uploaded_files):
            st.markdown(f"**Datei {i+1}/{len(uploaded_files)}: {up.name}**")
            progress.progress((i) / len(uploaded_files), text=f"Analysiere {up.name}...")

            try:
                import hashlib
                pdf_hash = hashlib.sha256(up.getvalue()).hexdigest()
                if SUPABASE_AKTIV:
                    try:
                        from supabase_db import suche_nach_hash as _sb_suche_hash
                        cached = _sb_suche_hash(pdf_hash)
                        if cached:
                            st.info(f"✅ {up.name}: Hash-Match – aus Cache geladen, kein API-Call.")
                            ergebnisse.append({"datei": up.name, "kosten": 0.0, "status": "cached"})
                            progress.progress((i+1) / len(uploaded_files))
                            continue
                    except Exception:
                        pass

                pdf_pfad = TMP_DIR / up.name
                pdf_pfad.write_bytes(up.getvalue())

                from ki_analyse import analysiere_vertrag, berechne_kosten, formatiere_token_info
                from utils import extract_text_from_pdf, display_name
                from fristen_extraktor import extrahiere_fristen, kategorien_label
                from generate_report import generiere_report
                from vertrags_datenbank import aktualisiere_db

                rohtext, seiten = extract_text_from_pdf(str(pdf_pfad))
                fristen = extrahiere_fristen(rohtext)
                fristen_hinweise = "\n".join([f"- {t['match']} ({kategorien_label(t['kategorie'])})" for t in fristen]) if fristen else ""

                gewaehltes_modell = modell_id(modell_label)
                analyse_text, token_info = analysiere_vertrag(
                    rohtext=rohtext,
                    vertrag_titel=display_name(pdf_pfad.stem),
                    seiten=seiten,
                    fristen_hinweise=fristen_hinweise,
                    modell=gewaehltes_modell,
                )

                kosten = berechne_kosten(token_info)
                gesamt_kosten += kosten

                datum_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                from utils import slugify
                md_pfad = TMP_DIR / f"vertragsanalyse_{slugify(pdf_pfad.stem)}_{datum_str}.md"
                md_pfad.write_text(analyse_text, encoding="utf-8")
                generiere_report(md_pfad, output_dir=OUTPUT_DIR)
                aktualisiere_db(TMP_DIR, DB_PFAD)

                if SUPABASE_AKTIV:
                    try:
                        from vertrags_datenbank import parse_analyse_datei
                        from supabase_db import speichere_mit_hash as _sb_speichere_mit_hash
                        eintrag = parse_analyse_datei(md_pfad)
                        if eintrag.get("partei_a") or eintrag.get("partei_b"):
                            _sb_speichere_mit_hash(eintrag, pdf_hash)
                    except Exception:
                        pass

                st.success(f"✅ {up.name} – ~${kosten:.4f}")
                ergebnisse.append({"datei": up.name, "kosten": kosten, "status": "analysiert"})

            except Exception as e:
                st.error(f"❌ {up.name}: {e}")
                ergebnisse.append({"datei": up.name, "kosten": 0.0, "status": f"fehler: {e}"})

            progress.progress((i+1) / len(uploaded_files), text=f"{i+1}/{len(uploaded_files)} abgeschlossen")

        progress.progress(1.0, text="Batch abgeschlossen.")
        st.info(f"**Gesamt: {len(uploaded_files)} PDFs | Kosten: ~${gesamt_kosten:.4f} USD**")
        if any(r["status"] == "cached" for r in ergebnisse):
            cached_count = sum(1 for r in ergebnisse if r["status"] == "cached")
            st.caption(f"💡 {cached_count} PDF(s) aus Cache geladen – kein API-Call.")



# ── Seite 2: Datenbank ────────────────────────────────────────────────────────

elif seite == "📋 Datenbank":
    st.header("Vertrags-Datenbank")

    if SUPABASE_AKTIV:
        st.success("☁️ Supabase aktiv – Daten bleiben dauerhaft gespeichert.")
        try:
            vollstaendig = [z for z in _sb_lade() if z.get("partei_a") or z.get("partei_b")]
        except Exception as e:
            st.error(f"Supabase-Fehler: {e}")
            vollstaendig = []
    else:
        try:
            if st.secrets.get("ANTHROPIC_API_KEY"):
                st.warning("⚠️ Cloud-Modus ohne Supabase: Datenbank wird bei App-Neustart zurückgesetzt. "
                           "Trage SUPABASE_URL und SUPABASE_KEY in Streamlit Secrets ein.")
        except Exception:
            pass
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

        suchbegriff = st.text_input(
            "🔍 Suche",
            placeholder="Partei, Vertragstyp, Tag ...",
            help="Durchsucht Dateiname, Parteien, Vertragstyp, Tags und Notizen"
        )
        from supabase_db import suche_vertraege
        gefiltert = suche_vertraege(suchbegriff, gefiltert)
        if suchbegriff and not gefiltert:
            st.warning(f'Keine Ergebnisse f\u00fcr "{suchbegriff}".')

        # Tabellenansicht mit Delete-Button
        hcols = st.columns([2, 2, 2, 1, 1, 1])
        for h, label in zip(hcols, ["Datei", "Partei A", "Typ", "Risiko", "Ende", ""]):
            h.caption(label)

        for i, z in enumerate(gefiltert):
            cols = st.columns([2, 2, 2, 1, 1, 1])
            cols[0].write(z.get("quelldatei", "")[:30])
            cols[1].write(z.get("partei_a", "")[:25])
            cols[2].write(z.get("vertragstyp", "")[:25])
            score_emoji = {"GRÜN": "🟢", "GELB": "🟡", "ROT": "🔴"}.get(z.get("risiko_score", ""), "⚪")
            cols[3].write(f"{score_emoji} {z.get('risiko_score', '–')}")
            cols[4].write(z.get("vertragsende", ""))
            if cols[5].button("🗑️", key=f"del_{i}", help="Vertrag löschen"):
                vid = z.get("id", "")
                if SUPABASE_AKTIV and vid:
                    from supabase_db import loesche_vertrag
                    loesche_vertrag(vid)
                    from supabase_db import log_aktion
                    log_aktion("GELÖSCHT", vertrag_id=vid, quelldatei=z.get("quelldatei", ""))
                st.rerun()

            status_optionen = ["Entwurf", "In Prüfung", "Aktiv", "Gekündigt", "Abgelaufen"]
            aktueller_status = z.get("status_workflow", "Aktiv")
            neuer_status = st.selectbox(
                "Status",
                status_optionen,
                index=status_optionen.index(aktueller_status) if aktueller_status in status_optionen else 2,
                key=f"status_{i}",
                label_visibility="collapsed",
            )
            if neuer_status != aktueller_status and SUPABASE_AKTIV:
                from supabase_db import aktualisiere_status
                aktualisiere_status(z.get("id", ""), neuer_status)
                from supabase_db import log_aktion
                log_aktion("STATUS", vertrag_id=z.get("id", ""), quelldatei=z.get("quelldatei", ""), details=f"{aktueller_status} → {neuer_status}")
                st.rerun()

            # Tags
            aktuelle_tags = z.get("tags", "")
            neue_tags = st.text_input(
                "Tags",
                value=aktuelle_tags,
                placeholder="z.B. aktiv, priorität, intern",
                key=f"tags_{i}",
                label_visibility="collapsed",
                help="Kommagetrennte Tags"
            )
            if neue_tags != aktuelle_tags and SUPABASE_AKTIV:
                from supabase_db import aktualisiere_tags
                aktualisiere_tags(z.get("id", ""), neue_tags)
                st.rerun()

            with st.expander(f"📝 Notizen – {z.get('quelldatei','')[:30]}"):
                aktuelle_notizen = z.get("notizen", "")
                neue_notizen = st.text_area(
                    "Notizen",
                    value=aktuelle_notizen,
                    height=100,
                    key=f"notizen_{i}",
                    label_visibility="collapsed",
                    placeholder="Interne Anmerkungen, Verhandlungsstand, Besonderheiten ..."
                )
                if st.button("Speichern", key=f"notizen_save_{i}"):
                    if SUPABASE_AKTIV:
                        from supabase_db import aktualisiere_notizen
                        aktualisiere_notizen(z.get("id", ""), neue_notizen)
                    st.success("Notiz gespeichert.")
                    st.rerun()

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

        st.markdown("---")
        smtp_bereit = bool(os.getenv("SMTP_HOST"))
        try:
            smtp_bereit = smtp_bereit or bool(st.secrets.get("SMTP_HOST"))
        except Exception:
            pass

        if not smtp_bereit:
            st.caption("📧 E-Mail-Reminder: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, REMINDER_EMPFAENGER in Streamlit Secrets eintragen.")

        if st.button("📧 Reminder-E-Mails senden", disabled=not smtp_bereit):
            try:
                from fristen_reminder import pruefe_und_sende_reminder
                result = pruefe_und_sende_reminder(DB_PFAD)
                if result["status"] == "ok":
                    st.success(result["message"])
                elif result["status"] == "config_fehlt":
                    st.warning(result["message"])
                else:
                    st.error(result["message"])
            except Exception as e:
                st.error(f"Reminder-Fehler: {e}")

        st.markdown("---")
        st.subheader("📥 Export")
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            if vollstaendig:
                import csv as _csv, io as _io_csv
                output = _io_csv.StringIO()
                felder = list(vollstaendig[0].keys()) if vollstaendig else []
                writer = _csv.DictWriter(output, fieldnames=felder)
                writer.writeheader()
                writer.writerows(vollstaendig)
                st.download_button(
                    "📄 CSV herunterladen",
                    data=output.getvalue().encode("utf-8"),
                    file_name=f"vertraege_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )
        with col_exp2:
            if vollstaendig:
                try:
                    import pandas as pd
                    import io as _io_xlsx
                    df_export = pd.DataFrame(vollstaendig)
                    excel_buffer = _io_xlsx.BytesIO()
                    df_export.to_excel(excel_buffer, index=False, engine="openpyxl")
                    st.download_button(
                        "📊 Excel herunterladen (.xlsx)",
                        data=excel_buffer.getvalue(),
                        file_name=f"vertraege_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                except ImportError:
                    st.caption("Excel-Export: `pip install openpyxl pandas` ausführen.")


# ── Seite 3: Analytics ────────────────────────────────────────────────────────

elif seite == "📊 Analytics":
    st.header("Portfolio-Übersicht")

    if SUPABASE_AKTIV:
        try:
            daten = [z for z in _sb_lade() if z.get("partei_a") or z.get("partei_b")]
        except Exception:
            daten = []
    else:
        daten = [z for z in lade_csv(DB_PFAD) if z.get("partei_a") or z.get("partei_b")]

    if not daten:
        st.info("Noch keine Verträge analysiert.")
    else:
        heute = datetime.now()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Verträge gesamt", len(daten))

        rot = sum(1 for z in daten if z.get("risiko_score") == "ROT")
        gelb = sum(1 for z in daten if z.get("risiko_score") == "GELB")
        gruen = sum(1 for z in daten if z.get("risiko_score") == "GRÜN")
        col2.metric("🔴 Hohes Risiko", rot)
        col3.metric("🟡 Mittleres Risiko", gelb)
        col4.metric("🟢 Niedriges Risiko", gruen)

        st.markdown("---")

        typen_count = {}
        for z in daten:
            t = z.get("vertragstyp", "Unbekannt")[:30]
            typen_count[t] = typen_count.get(t, 0) + 1

        if typen_count:
            st.subheader("Verträge nach Typ")
            import pandas as pd
            df_typen = pd.DataFrame(
                {"Typ": list(typen_count.keys()), "Anzahl": list(typen_count.values())}
            ).sort_values("Anzahl", ascending=False)
            st.bar_chart(df_typen.set_index("Typ"))

        st.subheader("Ablaufende Verträge")
        ablaufend = []
        for z in daten:
            ende_str = z.get("vertragsende", "")
            if not ende_str or ende_str in ("–", "unbefristet", ""):
                continue
            try:
                import re as _re
                match = _re.search(r'(\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4})', ende_str)
                if match:
                    ds = match.group(1)
                    if "-" in ds:
                        ende = datetime.strptime(ds, "%Y-%m-%d")
                    else:
                        ende = datetime.strptime(ds, "%d.%m.%Y")
                    tage = (ende - heute).days
                    if 0 <= tage <= 180:
                        ablaufend.append({
                            "Vertrag": z.get("quelldatei", "")[:25],
                            "Endet in (Tage)": tage,
                            "Typ": z.get("vertragstyp", "")[:20],
                            "Risiko": z.get("risiko_score", ""),
                        })
            except Exception:
                continue

        if ablaufend:
            import pandas as pd
            df_ablauf = pd.DataFrame(ablaufend).sort_values("Endet in (Tage)")
            st.dataframe(df_ablauf, use_container_width=True)
        else:
            st.success("Keine Verträge laufen in den nächsten 180 Tagen ab.")

        st.subheader("Risiko-Verteilung")
        risiko_count = {"🔴 ROT": rot, "🟡 GELB": gelb, "🟢 GRÜN": gruen}
        risiko_count = {k: v for k, v in risiko_count.items() if v > 0}
        if risiko_count:
            import pandas as pd
            df_risiko = pd.DataFrame(
                {"Risiko": list(risiko_count.keys()), "Anzahl": list(risiko_count.values())}
            )
            st.bar_chart(df_risiko.set_index("Risiko"))

        st.markdown("---")
        st.subheader("🕵️ Aktivitäts-Log")
        try:
            import supabase_db as _sdb
            client_raw = _sdb._client()
            log_data = client_raw.table("audit_log").select("*").order("erstellt_am", desc=True).limit(50).execute().data
            if log_data:
                import pandas as pd
                df_log = pd.DataFrame(log_data)[["erstellt_am", "aktion", "quelldatei", "details"]]
                df_log["erstellt_am"] = pd.to_datetime(df_log["erstellt_am"]).dt.strftime("%d.%m.%Y %H:%M")
                st.dataframe(df_log, use_container_width=True, hide_index=True)
            else:
                st.caption("Noch keine Aktivitäten protokolliert.")
        except Exception as e:
            st.caption(f"Audit-Log nicht verfügbar: {e}")


# ── Seite 4: Vergleich ────────────────────────────────────────────────────────

elif seite == "⚖️ Vergleich":
    st.header("Vertragsvergleich")
    st.caption("Zwei Verträge aus der Datenbank gegenüberstellen. KI erstellt eine strukturierte Analyse (~0,02 $).")

    if SUPABASE_AKTIV:
        try:
            alle = [z for z in _sb_lade() if z.get("partei_a") or z.get("partei_b")]
        except Exception:
            alle = []
    else:
        alle = [z for z in lade_csv(DB_PFAD) if z.get("partei_a") or z.get("partei_b")]

    if len(alle) < 2:
        st.info("Mindestens 2 analysierte Verträge nötig. Gehe zu 📤 Analyse.")
    else:
        optionen = {f"{z.get('quelldatei','?')} | {z.get('vertragstyp','?')[:25]}": z for z in alle}
        labels = list(optionen.keys())

        col1, col2 = st.columns(2)
        with col1:
            wahl_a = st.selectbox("Vertrag A", labels, key="vgl_a")
        with col2:
            verbleibend = [l for l in labels if l != wahl_a]
            wahl_b = st.selectbox("Vertrag B", verbleibend, key="vgl_b")

        if st.button("Vergleichen", type="primary"):
            vertrag_a = optionen[wahl_a]
            vertrag_b = optionen[wahl_b]

            st.markdown("---")
            st.subheader("📋 Metadaten-Gegenüberstellung")
            felder_anzeige = [
                ("Vertragstyp", "vertragstyp"), ("Laufzeit Start", "vertragsbeginn"),
                ("Laufzeit Ende", "vertragsende"), ("Kündigung", "kuendigungsfrist"),
                ("Status", "status_workflow"), ("Risiko", "risiko_score"),
            ]
            import pandas as pd
            df_vgl = pd.DataFrame([
                {"Feld": label, "Vertrag A": vertrag_a.get(key, "–"), "Vertrag B": vertrag_b.get(key, "–")}
                for label, key in felder_anzeige
            ])
            st.dataframe(df_vgl, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("🤖 KI-Analyse")
            with st.spinner("Vergleiche Verträge..."):
                try:
                    from ki_analyse import vergleiche_vertraege, berechne_kosten
                    vgl_text, vgl_tokens = vergleiche_vertraege(vertrag_a, vertrag_b)
                    st.markdown(vgl_text)
                    st.caption(f"Kosten: ~${berechne_kosten(vgl_tokens):.4f}")
                    if SUPABASE_AKTIV:
                        from supabase_db import log_aktion
                        log_aktion("VERGLEICH", details=f"{vertrag_a.get('quelldatei','')} vs. {vertrag_b.get('quelldatei','')}")
                except Exception as e:
                    st.error(f"Vergleich fehlgeschlagen: {e}")


# ── Seite 5: Kosten ───────────────────────────────────────────────────────────

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
