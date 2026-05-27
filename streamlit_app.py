"""
streamlit_app.py - ProteoSage Main Application
Standalone Streamlit app — no FastAPI or ngrok needed.
Always online via Streamlit Community Cloud.
"""

import time
import io
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
        background: linear-gradient(135deg, #1a3a5c 0%, #2c5f8a 50%, #3a7abf 100%);
        color: white; padding: 2rem 2.5rem; border-radius: 12px;
        margin-bottom: 2rem; box-shadow: 0 4px 20px rgba(26,58,92,0.35);
    }
    .main-header h1 { color: white; margin: 0; font-size: 2.2rem; }
    .main-header p  { color: #b8d4f0; margin: 0.5rem 0 0; font-size: 1rem; }
    .metric-card {
        background: white; border: 1px solid #dce8f5; border-radius: 10px;
        padding: 1.2rem; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .metric-card h3 { color: #1a3a5c; font-size: 1.8rem; margin: 0; }
    .metric-card p  { color: #5a6a7a; margin: 0.3rem 0 0; font-size: 0.85rem; }
    .badge-box {
        background: linear-gradient(135deg, #e8f0fe, #dce8f5);
        border: 1px solid #b8d4f0; border-radius: 10px;
        padding: 1rem; margin: 1rem 0; text-align: center;
        font-size: 1rem; color: #1a3a5c; font-weight: 600;
    }
    .chief-header {
        background: linear-gradient(135deg, #1a3a5c, #2c5f8a);
        color: white; padding: 0.8rem 1.2rem; border-radius: 8px; margin-bottom: 1rem;
    }
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🧬 ProteoSage</h1>
    <p>AI-powered protein research · UniProt · PubMed · ClinVar · AlphaFold · STRING · Reactome · GTEx · Open Targets</p>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧬 ProteoSage")
    st.markdown("*AI Protein Research Platform*")
    st.markdown("---")

    st.markdown("**Example Proteins**")
    examples = {
        "P04637": "TP53 — Tumor Suppressor",
        "P00533": "EGFR — Growth Factor Receptor",
        "P15056": "BRAF — Kinase",
        "Q9Y6K9": "IKBKG — NF-kB Modulator",
        "P35222": "CTNNB1 — Beta-catenin",
        "P00533": "EGFR — Receptor Kinase",
    }
    for uid, label in examples.items():
        if st.button(f"🔬 {uid}", help=label, key=f"ex_{uid}"):
            st.session_state["uid_input"] = uid

    st.markdown("---")
    st.markdown("**Databases**")
    dbs = ["UniProt", "PubMed", "ClinVar", "AlphaFold",
           "RCSB PDB", "STRING DB", "Reactome", "GTEx", "Open Targets"]
    for db in dbs:
        st.markdown(f"✅ {db}")

    st.markdown("---")
    st.markdown("**About**")
    st.markdown("ProteoSage autonomously researches proteins using 8 biomedical databases and AI synthesis to produce publication-quality reports.")
    st.markdown("[GitHub](https://github.com/sakeermr/proteosage)")


# ── Input ─────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    uid = st.text_input(
        "Enter UniProt Accession ID",
        value=st.session_state.get("uid_input", ""),
        placeholder="e.g. P04637  (TP53 — Tumor Protein p53)",
        help="UniProt accession IDs: 6 alphanumeric characters (e.g. P04637)",
        key="uid_input_field",
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_btn = st.button("🔬 Analyze", type="primary", use_container_width=True)


# ── Analysis ──────────────────────────────────────────────────
if analyze_btn and uid:
    uid = uid.strip().upper()

    # Basic validation
    import re
    if not re.match(r"^[A-Z][0-9][A-Z0-9]{3}[0-9]", uid):
        st.error("❌ Invalid UniProt ID format. Example: P04637")
        st.stop()

    st.markdown("---")
    st.markdown(f"### 🔄 Researching: `{uid}`")

    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(pct, msg):
        progress_bar.progress(pct)
        status_text.info(msg)

    try:
        from app.services.research_engine import run_research_pipeline
        from app.services.pdf_service import generate_pdf

        result = run_research_pipeline(uid, progress_callback=update_progress)

        if "error" in result.get("errors", {}):
            st.error(f"❌ {result['errors'].get('uniprot', 'Unknown error')}")
            st.stop()

        progress_bar.progress(100)
        status_text.success("✅ Research complete!")

        # ── Metrics ───────────────────────────────────────────
        st.markdown("---")
        p = result.get("protein", {})
        m = result.get("mutations", {})
        s = result.get("structure", {})
        lit = result.get("literature", {})

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(f"""<div class="metric-card"><h3>{p.get("sequence_length", "N/A")}</h3><p>Amino Acids</p></div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class="metric-card"><h3>{m.get("total", 0)}</h3><p>Pathogenic Variants</p></div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div class="metric-card"><h3>{s.get("pdb_count", 0)}</h3><p>PDB Structures</p></div>""", unsafe_allow_html=True)
        with m4:
            st.markdown(f"""<div class="metric-card"><h3>{lit.get("count", 0)}</h3><p>Papers Retrieved</p></div>""", unsafe_allow_html=True)
        with m5:
            drugs = result.get("drugs", {})
            st.markdown(f"""<div class="metric-card"><h3>{len(drugs.get("drugs", []))}</h3><p>Known Drugs</p></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Badge Summary ──────────────────────────────────────
        from app.services.research_engine import extract_badges
        badges = extract_badges(result.get("classification", ""))
        st.markdown(f"""
        <div class="badge-box">
            🔴 {badges['primary_class']} &nbsp;|&nbsp;
            📊 {badges['expression_class']} &nbsp;|&nbsp;
            🏗️ {badges['structural_class']} &nbsp;|&nbsp;
            ⚡ {badges['mutation_mechanism']} &nbsp;|&nbsp;
            💊 {badges['therapeutic_tier']}
        </div>
        """, unsafe_allow_html=True)

        # ── Downloads ──────────────────────────────────────────
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            try:
                pdf_bytes = generate_pdf(result.get("markdown", ""), uid)
                st.download_button(
                    "📥 Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"{uid}_proteosage_report.pdf",
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
                    file_name=f"{uid}_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

        st.markdown("---")

        # ── Report Sections ────────────────────────────────────
        with st.expander("🧬 Protein Overview", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Protein Name:** {p.get('protein_name', 'N/A')}")
                st.markdown(f"**Gene:** `{p.get('gene_name', 'N/A')}`")
                st.markdown(f"**Organism:** {p.get('organism', 'N/A')}")
                st.markdown(f"**UniProt:** [{uid}](https://www.uniprot.org/uniprotkb/{uid})")
            with c2:
                st.markdown(f"**Sequence Length:** {p.get('sequence_length', 'N/A')} aa")
                locs = p.get("subcellular_locations", [])
                st.markdown(f"**Location:** {', '.join(locs[:3]) if locs else 'N/A'}")
                diseases = p.get("diseases", [])
                st.markdown(f"**Disease Associations:** {len(diseases)}")
            if p.get("function_description"):
                st.markdown("**Function:**")
                st.info(p["function_description"][:800])

        with st.expander("🔬 GO Annotations"):
            go_terms = p.get("go_terms", [])
            if go_terms:
                for cat in ["biological_process", "molecular_function", "cellular_component"]:
                    terms = [g for g in go_terms if g["category"] == cat]
                    if terms:
                        st.markdown(f"**{cat.replace('_', ' ').title()}**")
                        for t in terms[:6]:
                            st.markdown(f"- `{t['id']}` {t['name']}")
            else:
                st.info("No GO annotations available.")

        with st.expander("🧫 Expression Analysis (GTEx)"):
            expr = result.get("expression", {})
            tissues = expr.get("tissues", [])
            if tissues:
                import pandas as pd
                st.caption(f"Source: {expr.get('source', 'GTEx v8')}")
                df = pd.DataFrame(tissues)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Expression data not available.")

        with st.expander("🦠 Disease Associations"):
            diseases = p.get("diseases", [])
            if diseases:
                for d in diseases:
                    st.markdown(f"- {d}")
            else:
                st.info("No disease associations found.")

        with st.expander("🧬 Mutation & Variant Analysis (ClinVar)"):
            mut = result.get("mutations", {})
            st.metric("Total Pathogenic Variants", mut.get("total", 0))
            variants = mut.get("variants", [])
            if variants:
                import pandas as pd
                df = pd.DataFrame(variants)
                st.dataframe(df, use_container_width=True)

        with st.expander("🏗️ Structural Information"):
            struct = result.get("structure", {})
            c1, c2 = st.columns(2)
            with c1:
                if struct.get("alphafold"):
                    st.success("✅ AlphaFold structure available")
                    st.markdown(f"[🔗 View on AlphaFold DB]({struct.get('alphafold_url')})")
                else:
                    st.warning("⚠️ No AlphaFold structure")
            with c2:
                pdb_ids = struct.get("pdb_ids", [])
                if pdb_ids:
                    st.success(f"✅ {struct.get('pdb_count', 0)} PDB structures")
                    for pid in pdb_ids[:5]:
                        st.markdown(f"[`{pid}`](https://www.rcsb.org/structure/{pid})")
                else:
                    st.warning("⚠️ No PDB structures found")

        with st.expander("🔗 Protein-Protein Interactions (STRING DB)"):
            inter = result.get("interactions", {})
            partners = inter.get("partners", [])
            if partners:
                st.markdown(f"**Top partners:** {', '.join(partners)}")
                inter_list = inter.get("interactions", [])
                if inter_list:
                    import pandas as pd
                    df = pd.DataFrame(inter_list)
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("STRING interaction data not available.")

        with st.expander("🔬 Biological Pathways (Reactome)"):
            pathways = result.get("pathways", {})
            pathway_list = pathways.get("pathways", [])
            if pathway_list:
                st.markdown(f"**{pathways.get('count', 0)} pathways identified**")
                for pw in pathway_list:
                    st.markdown(f"- [{pw['name']}]({pw['url']}) `{pw['id']}`")
            else:
                st.info("Reactome pathway data not available.")

        with st.expander("💊 Drug & Therapeutic Landscape"):
            drug_data = result.get("drugs", {})
            drugs = drug_data.get("drugs", [])
            if drugs:
                st.caption(f"Source: {drug_data.get('source', 'N/A')}")
                import pandas as pd
                df = pd.DataFrame(drugs)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No drug data available.")

        with st.expander("📚 Literature Review"):
            review = result.get("literature_review", "")
            if review:
                st.markdown(review)
            papers = lit.get("papers", [])
            if papers:
                st.markdown("**References:**")
                for i, paper in enumerate(papers[:10], 1):
                    authors = ", ".join(paper.get("authors", [])[:2])
                    year = paper.get("year", "")
                    title = paper.get("title", "")
                    pmid = paper.get("pmid", "")
                    st.markdown(f"{i}. {authors} ({year}). [{title}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")

        with st.expander("💡 Research Insights"):
            insights = result.get("insights", "")
            if insights:
                st.markdown(insights)

        with st.expander("🔬 Chief Scientist Protein Classification", expanded=True):
            st.markdown("""
            <div class="chief-header">
                <b>🏆 Expert Multi-Dimensional Classification</b><br>
                <small>AI Chief Scientist analysis for research & drug discovery</small>
            </div>
            """, unsafe_allow_html=True)
            classification = result.get("classification", "")
            if classification:
                st.markdown(classification)

        with st.expander("📝 Conclusion"):
            conclusion = result.get("conclusion", "")
            if conclusion:
                st.markdown(conclusion)

        with st.expander("📄 Full Markdown Report"):
            st.markdown(result.get("markdown", ""))

    except Exception as exc:
        progress_bar.empty()
        status_text.error(f"❌ Pipeline error: {exc}")
        st.exception(exc)

elif analyze_btn and not uid:
    st.warning("⚠️ Please enter a UniProt ID first.")

# ── Footer ────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<center><small>ProteoSage v1.0 · Built with AI · "
    "Data from UniProt, PubMed, ClinVar, AlphaFold, STRING, Reactome, GTEx, Open Targets"
    "</small></center>",
    unsafe_allow_html=True,
)
