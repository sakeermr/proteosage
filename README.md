# 🧬 ProteoSage v2.0 — AI Protein Research Platform

> **Evidence-tagged · Confidence-scored · Conflict-detected · Publication-quality reports**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://proteosage-4yoyf2qoi76p76chc8mevl.streamlit.app/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

ProteoSage is a free, open-source AI research platform that takes a **UniProt accession ID** (e.g. `P04637` for TP53) and autonomously generates a comprehensive, 17-section scientific report by querying **9 biomedical databases** in parallel and synthesising the results with **GPT-4o-mini**.

---

## 🎯 What Makes v2.0 Different

v1.0 was a capable report generator. v2.0 is a more scientifically honest platform:

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Evidence tagging per data point | ❌ | ✅ |
| Confidence scoring (High / Medium / Low) | ❌ | ✅ |
| Cross-source conflict detection | ❌ | ✅ |
| Pathogenic-only variant filtering | ❌ | ✅ (Benign filtered out) |
| PDB structure details (method, resolution) | ❌ | ✅ |
| STRING interaction evidence type | ❌ | ✅ (Experimental vs Predicted) |
| Mutation-specific drug annotation | ❌ | ✅ |
| Data quality notice in report | ❌ | ✅ |
| Inline PubMed citations in LLM text | ❌ | ✅ |
| Human-only Reactome pathways | ❌ | ✅ |

---

## ✨ Core Features

- **17-section scientific report** covering protein biology, mutations, structure, expression, pathways, drugs, and AI insights
- **9 live databases**: UniProt · PubMed · GTEx · ClinVar · AlphaFold · RCSB PDB · STRING DB · Reactome · Open Targets
- **Evidence legend** on every data point:
  - ✅ Experimentally verified
  - 📋 Curated database record
  - 🔮 Computationally predicted (AlphaFold)
  - 🤖 AI-inferred / synthesised
  - 📚 Literature-derived
- **Conflict detector** — automatically flags contradictions between data sources
- **Drug landscape** with FDA approval status, mutation specificity, and clinical lines
- **PDF download** (Nature/Cell journal style) + **Markdown download**
- **Completely free** — runs on Streamlit Community Cloud, no server needed

---

## 🚀 Quick Start

### Run locally

```bash
# 1. Clone the repo
git clone https://github.com/sakeermr/proteosage.git
cd proteosage

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up API keys
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Run
streamlit run streamlit_app.py
```

### Streamlit Cloud (free hosting)

1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → select your fork
3. In **Settings → Secrets**, add:

```toml
OPENAI_API_KEY = "sk-your-key-here"
LLM_MODEL      = "gpt-4o-mini"
NCBI_EMAIL     = "you@example.com"
NCBI_API_KEY   = "your-ncbi-key"   # optional
```

4. Deploy — your app will be live in ~60 seconds.

---

## 🔑 API Keys

| Key | Required | Purpose | Get it |
|-----|----------|---------|--------|
| `OPENAI_API_KEY` | **Yes** | AI synthesis (GPT-4o-mini) | [platform.openai.com](https://platform.openai.com/api-keys) |
| `NCBI_EMAIL` | Recommended | PubMed / ClinVar access | Any valid email |
| `NCBI_API_KEY` | Optional | Higher NCBI rate limit (10 req/s) | [ncbi.nlm.nih.gov/account](https://www.ncbi.nlm.nih.gov/account/) |
| `GEMINI_API_KEY` | Optional | Fallback LLM if OpenAI fails | [aistudio.google.com](https://aistudio.google.com/app/apikey) |

> 💡 **Cost:** GPT-4o-mini costs approximately $0.002–0.005 per full protein report.

---

## 🗂️ Project Structure

```
proteosage/
├── streamlit_app.py              # Main Streamlit UI (evidence-tagged sections)
├── requirements.txt              # Python dependencies
├── .env.example                  # API key template (no real keys!)
├── .gitignore
│
├── app/
│   ├── config/
│   │   └── settings.py           # Config — reads Streamlit secrets or .env
│   └── services/
│       ├── llm_service.py        # OpenAI / Gemini wrapper
│       ├── research_engine.py    # Core pipeline — 9 databases + evidence tagging
│       └── pdf_service.py        # Nature/Cell-style PDF generator
│
└── tests/
    └── test_research_engine.py   # Unit tests
```

---

## 🔬 How It Works

```
User enters UniProt ID
        │
        ▼
  1. UniProt (sequential — gene name needed for all others)
        │
        ▼
  2. Parallel queries (7 threads simultaneously):
     ├── PubMed       → literature papers
     ├── ClinVar      → pathogenic variants
     ├── AlphaFold    → predicted structure
     ├── RCSB PDB     → experimental structures
     ├── STRING DB    → interaction partners
     ├── Reactome     → biological pathways
     ├── GTEx         → tissue expression
     └── Open Targets → drug landscape
        │
        ▼
  3. Conflict detector (cross-reference validation)
        │
        ▼
  4. LLM synthesis (GPT-4o-mini):
     ├── Evidence-cited literature review
     ├── Chief Scientist classification
     ├── Research insights
     └── Conclusion
        │
        ▼
  5. Report builder (17 sections, evidence tags, PDF/Markdown)
```

---

## 📊 Report Sections

| # | Section | Primary Source | Evidence Level |
|---|---------|---------------|----------------|
| 1 | Protein Overview | UniProt | ✅ Verified |
| 2 | Gene Information | UniProt / Ensembl | ✅ Verified |
| 3 | Protein Function | UniProt | ✅ Verified |
| 4 | GO Annotations | UniProt GO | ✅ / 🔮 Mixed |
| 5 | Expression Analysis | GTEx v8 | ✅ Verified |
| 6 | Disease Associations | UniProt | ✅ Verified |
| 7 | Mutation Analysis | ClinVar | ✅ Verified |
| 8 | Structural Information | AlphaFold + PDB | 🔮 + ✅ |
| 9 | Protein Interactions | STRING DB | 🟡 Mixed |
| 10 | Biological Pathways | Reactome | ✅ Curated |
| 11 | Drug Landscape | Open Targets + Curated | 📋 Curated |
| 12 | Data Quality Flags | Cross-source | 🔍 Auto-detected |
| 13 | Literature Review | PubMed + GPT | 📚 + 🤖 |
| 14 | Research Insights | All sources + GPT | 🤖 AI |
| 15 | Chief Scientist Classification | All sources + GPT | 🤖 AI |
| 16 | Conclusion | All sources + GPT | 🤖 AI |
| 17 | References | PubMed | 📚 Literature |

---

## 🔭 Roadmap

### ✅ Phase 1 — Completed (v2.0)
- [x] Evidence tagging system (verified / predicted / curated / AI)
- [x] Confidence scoring per section
- [x] Pathogenic-only variant filtering
- [x] Cross-source conflict detection
- [x] Mutation-specific drug annotations
- [x] Inline citation in LLM text
- [x] Human-only Reactome pathways
- [x] PDB structure details (method, resolution)
- [x] STRING evidence classification (experimental vs predicted)

### 🔄 Phase 2 — Next (v2.5)
- [ ] **COSMIC integration** — cancer somatic mutation database
- [ ] **Mutation → drug sensitivity matrix** (L858R → Osimertinib ✔✔✔)
- [ ] **Drug resistance pathways** (T790M → bypass via KRAS)
- [ ] **Pathway visualisation** — interactive network diagram
- [ ] **Gene expression heatmap** — visual GTEx tissue chart
- [ ] **Multi-protein comparison mode** (EGFR vs BRAF side by side)

### 🚀 Phase 3 — Advanced (v3.0 — may require paid APIs)
- [ ] **Protein Digital Twin** — simulate mutation effects in silico
- [ ] **Clinical Decision Tree** — patient mutation → therapy pathway
- [ ] **AI Hypothesis Generator** — ranked, confidence-tagged research hypotheses
- [ ] **Proteomics data integration** — PRIDE / ProteomicsDB
- [ ] **scRNA-seq expression** — single-cell level tissue analysis
- [ ] **Drug combination predictor** — synergy/resistance modelling

---

## ⚠️ Important Disclaimers

1. **Research use only.** Not for clinical diagnosis, treatment decisions, or patient management.
2. **AI synthesis is probabilistic.** The LLM sections (literature review, classification, insights) are AI-generated and may contain errors. Always verify against primary sources.
3. **AlphaFold structures are predictions.** Use experimental PDB structures when available for drug docking.
4. **Drug information may be incomplete.** Always check FDA/EMA databases for current approval status.
5. **ClinVar data reflects submissions** and may not capture all known variants.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| UI | Streamlit (free hosting) |
| LLM | OpenAI GPT-4o-mini (Gemini fallback) |
| PDF | fpdf2 |
| HTTP | requests |
| Concurrency | ThreadPoolExecutor (7 parallel DB queries) |
| Language | Python 3.11+ |

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/cosmic-integration`
3. Make your changes with tests
4. Submit a pull request

### Ideas for contribution
- Add COSMIC somatic mutation data
- Improve PDF styling
- Add unit tests for database fetchers
- Add new curated drug entries

---

## 📄 License

MIT License — see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgements

ProteoSage integrates data from these excellent free resources:
- [UniProt](https://www.uniprot.org/) — Swiss-Prot manually reviewed protein database
- [NCBI PubMed & ClinVar](https://www.ncbi.nlm.nih.gov/) — literature and variant data
- [GTEx](https://gtexportal.org/) — tissue expression atlas
- [AlphaFold DB](https://alphafold.ebi.ac.uk/) — AI protein structure predictions
- [RCSB PDB](https://www.rcsb.org/) — experimental protein structures
- [STRING DB](https://string-db.org/) — protein interaction network
- [Reactome](https://reactome.org/) — curated pathway database
- [Open Targets](https://www.opentargets.org/) — drug-target evidence

---

*Built with ❤️ for the open science community.*
