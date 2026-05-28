"""
streamlit_app.py — ProteoSage v2.0
------------------------------------
AI-powered protein research platform.
Evidence-tagged · Confidence-scored · Conflict-detected
"""

import time
import re
import sys
import io
import streamlit as st
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

st.set_page_config(
    page_title="ProteoSage — AI Protein Research",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #f0f4f8; }

    .main-header {
        background: linear-gradient(135deg, #0f2942 0%, #1a3a5c 50%, #2c5f8a 100%);
        color: white; padding: 2rem 2.5rem; border-radius: 14px;
        margin-bottom: 1.5rem; box-shadow: 0 6px 24px rgba(15,41,66,0.4);
    }
    .main-header h1 { color: white; margin: 0; font-size: 2.4rem; letter-spacing: -0.5px; }
    .main-header p  { color: #8bbfe0; margin: 0.5rem 0 0; font-size: 0.95rem; }

    .metric-card {
        background: white; border: 1px solid #dce8f5; border-radius: 12px;
        padding: 1.2rem; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        transition: box-shadow 0.2s;
    }
    .metric-card:hover { box-shadow: 0 4px 18px rgba(0,0,0,0.10); }
    .metric-card h3 { color: #1a3a5c; font-size: 2rem; margin: 0; font-weight: 700; }
    .metric-card p  { color: #5a6a7a; margin: 0.3rem 0 0; font-size: 0.82rem; }

    .badge-box {
        background: linear-gradient(135deg, #e8f0fe, #dce8f5);
        border: 1px solid #b8d4f0; border-radius: 10px;
        padding: 0.9rem 1.2rem; margin: 0.8rem 0;
        font-size: 0.92rem; color: #1a3a5c; font-weight: 600;
        display: flex; flex-wrap: wrap; justify-content: center; gap: 0.6rem;
    }
    .badge-pill {
        background: white; border: 1px solid #b8d4f0; border-radius: 20px;
        padding: 0.3rem 0.8rem; font-size: 0.85rem; color: #1a3a5c;
        white-space: nowrap;
    }

    .evidence-bar {
        background: #e8f5e9; border-left: 4px solid #2e7d32;
        padding: 0.5rem 0.8rem; border-radius: 0 6px 6px 0;
        margin: 0.4rem 0; font-size: 0.82rem; color: #1b5e20;
    }
    .evidence-bar.medium {
        background: #fff8e1; border-left-color: #f9a825; color: #6d4c00;
    }
    .evidence-bar.low {
        background: #fce4ec; border-left-color: #c62828; color: #7f0000;
    }
    .evidence-bar.note {
        background: #e3f2fd; border-left-color: #1565c0; color: #0d3a6b;
    }

    .conflict-box {
        background: #fff3e0; border: 1px solid #ff9800; border-radius: 8px;
        padding: 0.8rem 1rem; margin: 0.5rem 0; font-size: 0.88rem;
    }
    .conflict-box.gap {
        background: #e3f2fd; border-color: #2196f3;
    }

    .section-tag {
        display: inline-block; background: #1a3a5c; color: white;
        border-radius: 4px; padding: 0.15rem 0.5rem;
        font-size: 0.72rem; font-weight: 600; margin-left: 0.5rem;
        vertical-align: middle;
    }

    .chief-header {
        background: linear-gradient(135deg, #0f2942, #1a3a5c);
        color: white; padding: 1rem 1.4rem; border-radius: 10px;
        margin-bottom: 1rem;
    }
    .chief-header b   { font-size: 1.05rem; }
    .chief-header small { color: #8bbfe0; }

    .data-notice {
        background: #fffde7; border: 1px solid #f9a825; border-radius: 8px;
        padding: 0.6rem 1rem; margin: 0.5rem 0; font-size: 0.82rem; color: #5d4037;
    }

    .db-pill {
        display: inline-block; background: #e8f0fe; border: 1px solid #b8d4f0;
        border-radius: 20px; padding: 0.2rem 0.7rem; margin: 0.15rem;
        font-size: 0.78rem; color: #1a3a5c; font-weight: 500;
    }

    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🧬 ProteoSage</h1>
    <p>AI-powered protein intelligence · Evidence-tagged · Confidence-scored · 9 biomedical databases</p>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧬 ProteoSage v2.0")
    st.markdown("*AI Protein Research Platform*")
    st.markdown("---")

    st.markdown("**🔬 Example Proteins**")
    examples = {
        "P04637": "TP53 — Tumor Suppressor",
        "P00533": "EGFR — Growth Factor Receptor",
        "P15056": "BRAF — Serine/Threonine Kinase",
        "P35222": "CTNNB1 — Beta-catenin",
        "P38398": "BRCA1 — DNA repair",
        "P01116": "KRAS — GTPase Oncogene",
    }
    for uid_ex, label in examples.items():
        if st.button(f"🔬 {uid_ex}", help=label, key=f"ex_{uid_ex}"):
            st.session_state["uid_input"] = uid_ex

    st.markdown("---")
    st.markdown("**📊 Data Sources**")
    dbs = {
        "UniProt": "✅ Verified",
        "PubMed": "✅ Verified",
        "ClinVar": "✅ Verified",
        "AlphaFold": "🔮 Predicted",
        "RCSB PDB": "✅ Experimental",
        "STRING DB": "🟡 Mixed",
        "Reactome": "✅ Curated",
        "GTEx": "✅ Verified",
        "Open Targets": "✅ Curated",
    }
    for db, tag in dbs.items():
        st.markdown(f"<span class='db-pill'>{db}</span> <small>{tag}</small>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
**🔑 Evidence Legend**
- ✅ Experimentally verified
- 📋 Curated database record
- 🔮 Computationally predicted
- 🤖 AI-inferred / synthesized
- 📚 Literature-derived
    """)
    st.markdown("---")
    st.markdown("[GitHub](https://github.com/sakeermr/proteosage) · "
                "[Report Issues](https://github.com/sakeermr/proteosage/issues)")


# ── Input ─────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    uid = st.text_input(
        "Enter UniProt Accession ID",
        value=st.session_state.get("uid_input", ""),
        placeholder="e.g. P04637  (TP53)   ·   P00533 (EGFR)   ·   P15056 (BRAF)",
        help="UniProt accession IDs: 6 alphanumeric characters (e.g. P04637)",
        key="uid_input_field",
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_btn = st.button("🔬 Analyze", type="primary", use_container_width=True)

st.markdown("""
<div class="data-notice">
⚠️ <b>Research use only.</b> Reports combine verified database records with AI synthesis.
Each data point is tagged with its evidence level. Not for clinical decision-making.
</div>
""", unsafe_allow_html=True)


# ── Analysis ──────────────────────────────────────────────────
if analyze_btn and uid:
    uid = uid.strip().upper()

    if not re.match(r"^[A-Z][0-9][A-Z0-9]{3}[0-9]", uid):
        st.error("❌ Invalid UniProt ID format. Examples: P04637 · P00533 · P15056")
        st.stop()

    st.markdown("---")
    st.markdown(f"### 🔄 Researching: `{uid}`")

    progress_bar = st.progress(0)
    status_text  = st.empty()

    def update_progress(pct, msg):
        progress_bar.progress(pct)
        status_text.info(msg)

    try:
        from app.services.research_engine import run_research_pipeline, extract_badges
        from app.services.pdf_service import generate_pdf

        result = run_research_pipeline(uid, progress_callback=update_progress)

        if "error" in result.get("errors", {}):
            st.error(f"❌ {result['errors'].get('uniprot', 'Unknown error')}")
            st.stop()

        progress_bar.progress(100)
        status_text.success("✅ Research complete!")

        p   = result.get("protein", {})
        m   = result.get("mutations", {})
        s   = result.get("structure", {})
        lit = result.get("literature", {})
        drg = result.get("drugs", {})

        # ── Summary Metrics ────────────────────────────────────
        st.markdown("---")
        cols = st.columns(6)
        metrics = [
            (p.get("sequence_length", "N/A"), "Amino Acids",        "✅ UniProt"),
            (m.get("total_pathogenic", m.get("total", 0)), "Pathogenic Variants", "✅ ClinVar"),
            (s.get("pdb_count", 0),            "PDB Structures",     "✅ RCSB PDB"),
            (lit.get("count", 0),              "Papers Retrieved",   "📚 PubMed"),
            (len(drg.get("drugs", [])),         "Known Drugs",        "📋 Curated"),
            (len(result.get("pathways", {}).get("pathways", [])), "Pathways", "✅ Reactome"),
        ]
        for col, (val, label, src) in zip(cols, metrics):
            with col:
                st.markdown(
                    f'<div class="metric-card"><h3>{val}</h3>'
                    f'<p>{label}</p><p style="font-size:0.7rem;color:#9aabb8">{src}</p></div>',
                    unsafe_allow_html=True,
                )

        # ── Classification Badges ──────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        badges = extract_badges(result.get("classification", ""))
        badge_pills = "".join([
            f"<span class='badge-pill'>🔴 {badges['primary_class']}</span>",
            f"<span class='badge-pill'>📊 {badges['expression_class']}</span>",
            f"<span class='badge-pill'>🏗️ {badges['structural_class']}</span>",
            f"<span class='badge-pill'>⚡ {badges['mutation_mechanism']}</span>",
            f"<span class='badge-pill'>💊 {badges['therapeutic_tier']}</span>",
        ])
        st.markdown(f'<div class="badge-box">{badge_pills}</div>', unsafe_allow_html=True)

        # ── Conflict / Quality Flags ───────────────────────────
        contradictions = result.get("contradictions", [])
        if contradictions:
            with st.expander(f"⚠️ Data Quality Flags ({len(contradictions)} detected)", expanded=True):
                for c in contradictions:
                    ctype = c.get("type", "note")
                    sev   = c.get("severity", "low")
                    icon  = {"conflict": "🟡", "gap": "🔵", "note": "ℹ️"}.get(ctype, "ℹ️")
                    sources = " vs ".join(c.get("sources", []))
                    css_cls = "conflict-box gap" if ctype == "gap" else "conflict-box"
                    st.markdown(
                        f'<div class="{css_cls}">'
                        f'{icon} <b>{ctype.upper()}</b> [{sources}]: {c["message"]}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        # ── Downloads ──────────────────────────────────────────
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            try:
                pdf_bytes = generate_pdf(result.get("markdown", ""), uid)
                st.download_button(
                    "📥 Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"{uid}_proteosage_v2_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"PDF generation failed: {e}")
        with col_d2:
            md = result.get("markdown", "")
            if md:
                st.download_button(
                    "📝 Download Markdown",
                    data=md,
                    file_name=f"{uid}_proteosage_v2_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

        st.markdown("---")

        # ═══════════════════════════════════════════════════════
        # REPORT SECTIONS
        # ═══════════════════════════════════════════════════════

        with st.expander("🧬 1. Protein Overview", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Protein Name:** {p.get('protein_name', 'N/A')}")
                st.markdown(f"**Gene:** `{p.get('gene_name', 'N/A')}`")
                st.markdown(f"**Organism:** {p.get('organism', 'N/A')}")
                st.markdown(f"**UniProt:** [{uid}](https://www.uniprot.org/uniprotkb/{uid})")
                kw = p.get("keywords", [])
                if kw:
                    st.markdown(f"**Keywords:** {', '.join(kw[:6])}")
            with c2:
                st.markdown(f"**Sequence:** {p.get('sequence_length', 'N/A')} amino acids")
                locs = p.get("subcellular_locations", [])
                st.markdown(f"**Location:** {', '.join(locs[:3]) if locs else 'N/A'}")
                diseases = p.get("diseases", [])
                st.markdown(f"**Disease Associations:** {len(diseases)}")
                act = p.get("active_sites", [])
                if act:
                    st.markdown(f"**Active Sites:** {len(act)} annotated")
            st.markdown('<div class="evidence-bar">✅ Source: UniProt (manually reviewed Swiss-Prot entry)</div>',
                        unsafe_allow_html=True)
            if p.get("function_description"):
                st.markdown("**Function:**")
                st.info(p["function_description"][:900])

        with st.expander("🔬 2. GO Annotations"):
            st.markdown('<div class="evidence-bar">✅ Source: UniProt GO annotations '
                        '| EXP/IDA = experimental · IEA = inferred (lower confidence)</div>',
                        unsafe_allow_html=True)
            go_terms = p.get("go_terms", [])
            if go_terms:
                from app.services.research_engine import EVIDENCE_ICONS
                for cat in ["biological_process", "molecular_function", "cellular_component"]:
                    terms = [g for g in go_terms if g["category"] == cat]
                    if terms:
                        st.markdown(f"**{cat.replace('_', ' ').title()}**")
                        for t in terms[:8]:
                            ev_icon = EVIDENCE_ICONS.get(t.get("evidence_type", "verified"), "✅")
                            st.markdown(f"- `{t['id']}` {t['name']} {ev_icon} "
                                       f"<small style='color:#9aabb8'>`{t.get('evidence_code','')}`</small>",
                                       unsafe_allow_html=True)
            else:
                st.info("No GO annotations available.")

        with st.expander("🧫 3. Expression Analysis (GTEx)"):
            expr = result.get("expression", {})
            tissues = expr.get("tissues", [])
            ev = expr.get("evidence", {})
            conf_css = {"High": "", "Medium": " medium", "Low": " low"}.get(
                ev.get("confidence_label", "Medium"), " medium") if ev else " medium"
            st.markdown(
                f'<div class="evidence-bar{conf_css}">'
                f'{ev.get("evidence_icon","📋") if ev else "📋"} Source: {expr.get("source","GTEx v8")} | '
                f'Confidence: {ev.get("confidence_label","Medium") if ev else "Medium"}'
                f'</div>', unsafe_allow_html=True)
            if tissues:
                import pandas as pd
                df = pd.DataFrame(tissues)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Expression data not available.")

        with st.expander("🦠 4. Disease Associations"):
            st.markdown('<div class="evidence-bar">✅ Source: UniProt curated disease annotations</div>',
                        unsafe_allow_html=True)
            diseases = p.get("diseases", [])
            if diseases:
                for d in diseases:
                    name = d["name"] if isinstance(d, dict) else d
                    did  = d.get("id", "") if isinstance(d, dict) else ""
                    st.markdown(f"- **{name}** {f'`{did}`' if did else ''}")
            else:
                st.info("No disease associations found in UniProt.")

        with st.expander("🧬 5. Mutation & Variant Analysis (ClinVar)"):
            mut = result.get("mutations", {})
            st.markdown('<div class="evidence-bar">✅ Source: ClinVar (NCBI) '
                        '| Showing Pathogenic / Likely Pathogenic / VUS only</div>',
                        unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Pathogenic / Likely Pathogenic",
                          mut.get("total_pathogenic", mut.get("total", 0)))
            with c2:
                st.metric("Total ClinVar Variants", mut.get("total_all", mut.get("total", 0)))

            variants = [v for v in mut.get("variants", [])
                        if v.get("significance") not in ("Benign", "Likely Benign")]
            if variants:
                import pandas as pd
                display = []
                for v in variants:
                    display.append({
                        "Variant": v.get("change", "")[:60],
                        "Classification": f"{v.get('significance_icon','⚪')} {v.get('significance','N/A')}",
                        "Condition": v.get("condition", "N/A")[:50],
                        "ClinVar": v.get("url", ""),
                    })
                df = pd.DataFrame(display)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No high-significance variants retrieved.")

        with st.expander("🏗️ 6. Structural Information"):
            struct = result.get("structure", {})
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**AlphaFold (AI-predicted)**")
                if struct.get("alphafold"):
                    st.success("🔮 AlphaFold structure available")
                    st.markdown(f"[🔗 View on AlphaFold DB]({struct.get('alphafold_url')})")
                    if struct.get("alphafold_confidence"):
                        st.caption(struct["alphafold_confidence"])
                    st.markdown('<div class="evidence-bar medium">🔮 AI-predicted — '
                                'verify high-confidence regions (pLDDT > 90) for drug design</div>',
                                unsafe_allow_html=True)
                else:
                    st.warning("No AlphaFold structure found")
            with c2:
                st.markdown("**RCSB PDB (Experimental)**")
                pdb_details = struct.get("pdb_details", [])
                if pdb_details:
                    st.success(f"✅ {struct.get('pdb_count', 0)} experimental structures")
                    import pandas as pd
                    df = pd.DataFrame(pdb_details)[["id", "method", "resolution", "chains"]]
                    df.columns = ["PDB ID", "Method", "Resolution", "Chains"]
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.markdown('<div class="evidence-bar">✅ Experimental — '
                                'preferred for drug docking and structural analysis</div>',
                                unsafe_allow_html=True)
                elif struct.get("pdb_ids"):
                    st.success(f"✅ {struct.get('pdb_count', 0)} PDB structures")
                    for pid in struct["pdb_ids"][:6]:
                        st.markdown(f"[`{pid}`](https://www.rcsb.org/structure/{pid})")
                else:
                    st.warning("No experimental PDB structures found")

        with st.expander("🔗 7. Protein–Protein Interactions (STRING DB)"):
            inter = result.get("interactions", {})
            st.markdown(
                f'<div class="evidence-bar medium">🟡 Source: STRING DB | '
                f'{inter.get("note", "Scores are combined confidence (0–1)")}</div>',
                unsafe_allow_html=True)
            partners = inter.get("partners", [])
            if partners:
                st.markdown(f"**Top interaction partners:** `{'` · `'.join(partners)}`")
                inter_list = inter.get("interactions", [])
                if inter_list:
                    import pandas as pd
                    from app.services.research_engine import EVIDENCE_ICONS
                    display = []
                    for item in inter_list:
                        ev_icon = EVIDENCE_ICONS.get(item.get("evidence_type", "predicted"), "🔮")
                        display.append({
                            "Partner": item["partner"],
                            "Combined Score": item["score"],
                            "Experimental": item["experimental"],
                            "Evidence": f"{ev_icon} {item.get('evidence_label','Predicted')}",
                        })
                    df = pd.DataFrame(display)
                    st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("STRING interaction data not available.")

        with st.expander("🔬 8. Biological Pathways (Reactome)"):
            pathways_data = result.get("pathways", {})
            pathway_list  = pathways_data.get("pathways", [])
            st.markdown('<div class="evidence-bar">✅ Source: Reactome — Human pathways only</div>',
                        unsafe_allow_html=True)
            if pathway_list:
                st.markdown(f"**{pathways_data.get('count', 0)} human pathways identified**")
                for pw in pathway_list:
                    st.markdown(f"- [{pw['name']}]({pw['url']}) `{pw['id']}`")
            else:
                st.info("Reactome pathway data not available.")

        with st.expander("💊 9. Drug & Therapeutic Landscape"):
            drug_data = result.get("drugs", {})
            drugs = drug_data.get("drugs", [])
            ev = drug_data.get("evidence", {})
            ev_icon = ev.get("evidence_icon", "📋") if ev else "📋"
            conf_css = {"High": "", "Medium": " medium", "Low": " low"}.get(
                ev.get("confidence_label", "High"), "") if ev else ""
            st.markdown(
                f'<div class="evidence-bar{conf_css}">{ev_icon} Source: {drug_data.get("source","N/A")} '
                f'| Phase 4 = FDA/EMA Approved</div>',
                unsafe_allow_html=True)
            if drugs:
                import pandas as pd
                display = []
                for d in drugs:
                    display.append({
                        "Drug": d["name"],
                        "Type": d.get("type", "N/A"),
                        "Phase": d.get("phase", "N/A"),
                        "Status": d.get("status", ""),
                        "Mutations": d.get("mutations", "—"),
                        "Indication": d.get("disease", "N/A"),
                        "Mechanism": d.get("mechanism", "N/A"),
                    })
                df = pd.DataFrame(display)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No drug data available.")

        with st.expander("📚 10. Literature Review"):
            st.markdown('<div class="evidence-bar">📚 Source: PubMed · '
                        '[Paper N] citations are inline within the review text</div>',
                        unsafe_allow_html=True)
            review = result.get("literature_review", "")
            if review:
                st.markdown(review)
            papers = lit.get("papers", [])
            if papers:
                st.markdown("---")
                st.markdown("**📖 Retrieved Papers:**")
                for i, paper in enumerate(papers[:12], 1):
                    authors = ", ".join(paper.get("authors", [])[:2])
                    if len(paper.get("authors", [])) > 2:
                        authors += " et al."
                    year  = paper.get("year", "")
                    title = paper.get("title", "")
                    pmid  = paper.get("pmid", "")
                    ptype = paper.get("paper_type", "")
                    badge = f" `{ptype}`" if ptype else ""
                    st.markdown(
                        f"{i}. {authors} ({year}). "
                        f"[{title}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/){badge}"
                    )

        with st.expander("💡 11. Research Insights"):
            st.markdown('<div class="evidence-bar note">🤖 AI-generated analysis '
                        '— grounded in data retrieved above. Speculative points are flagged.</div>',
                        unsafe_allow_html=True)
            insights = result.get("insights", "")
            if insights:
                st.markdown(insights)

        with st.expander("🏆 12. Chief Scientist Classification", expanded=True):
            st.markdown("""
            <div class="chief-header">
                <b>🏆 Expert Multi-Dimensional Protein Classification</b><br>
                <small>AI computational analysis — confidence level stated per section | For research use</small>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<div class="evidence-bar note">🤖 AI classification — '
                        'each section includes a confidence rating (High/Medium/Low) '
                        'and evidence basis. Not a substitute for expert review.</div>',
                        unsafe_allow_html=True)
            classification = result.get("classification", "")
            if classification:
                st.markdown(classification)

        with st.expander("📝 13. Conclusion"):
            conclusion = result.get("conclusion", "")
            if conclusion:
                st.markdown(conclusion)

        with st.expander("📄 14. Full Markdown Report"):
            st.markdown("*Copy below or use the download button above.*")
            st.code(result.get("markdown", ""), language="markdown")

    except Exception as exc:
        progress_bar.empty()
        status_text.error(f"❌ Pipeline error: {exc}")
        st.exception(exc)

elif analyze_btn and not uid:
    st.warning("⚠️ Please enter a UniProt ID first.")


# ── Footer ────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<center><small>"
    "ProteoSage v2.0 · AI-powered protein intelligence · "
    "UniProt · PubMed · ClinVar · AlphaFold · STRING · Reactome · GTEx · Open Targets"
    "<br>⚠️ For research use only · Not for clinical decision-making"
    "</small></center>",
    unsafe_allow_html=True,
)
