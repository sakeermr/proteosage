# 🧬 ProteoSage — AI Protein Research Platform

> Autonomously research any human protein using 8 biomedical databases and AI synthesis.
> No installation needed — runs entirely in your browser.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://proteosage.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌐 Live Demo

👉 **https://proteosage.streamlit.app**

Just enter a UniProt ID and get a full scientific report in minutes!

---

## 🎯 What It Does

Enter a **UniProt ID** (e.g. `P04637` for TP53) and ProteoSage autonomously:

1. Fetches protein metadata from **UniProt**
2. Searches and AI-summarizes **PubMed** literature
3. Retrieves tissue expression from **GTEx** (54 tissues)
4. Queries **ClinVar** for pathogenic variants
5. Checks **AlphaFold** and **RCSB PDB** for 3D structures
6. Fetches protein interactions from **STRING DB**
7. Retrieves biological pathways from **Reactome**
8. Gets drug landscape from **Open Targets**
9. Generates a **16-section scientific report** (PDF + Markdown)

---

## 🔬 Report Sections

| # | Section |
|---|---------|
| 1 | Protein Overview + AI Badge Classification |
| 2 | Gene Information |
| 3 | Protein Function |
| 4 | GO Annotations |
| 5 | Expression Analysis (GTEx) |
| 6 | Disease Associations |
| 7 | Mutation Analysis (ClinVar) |
| 8 | Structural Information |
| 9 | Protein-Protein Interactions (STRING) |
| 10 | Biological Pathways (Reactome) |
| 11 | Drug & Therapeutic Landscape |
| 12 | Literature Review (AI-synthesized) |
| 13 | Research Insights (AI-generated) |
| 14 | Chief Scientist Classification |
| 15 | Conclusion |
| 16 | References |

---

## 🏆 Chief Scientist AI Classification

Every report includes:

- 🔴 **Primary Class** — Tumor Suppressor / Oncogene / Kinase / etc.
- 📊 **Expression Profile** — Overexpressed / Tissue-Restricted / Ubiquitous
- 🏗️ **Structural Type** — Stable Globular / IDP / Allosteric
- ⚡ **Mutation Mechanism** — Loss-of-Function / Gain-of-Function
- 💊 **Therapeutic Tier** — Tier 1 (Established) to Tier 5 (Undruggable)
- 🏆 **Chief Scientist Verdict** — Expert summary

---

## 🚀 Local Installation

```bash
git clone https://github.com/sakeermr/proteosage.git
cd proteosage
py -3.11 -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env         # Add your API keys
streamlit run streamlit_app.py
```

---

## 🔑 API Keys Required

| Key | Where to get |
|-----|-------------|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `NCBI_EMAIL` | Any email (required by NCBI) |
| `NCBI_API_KEY` | https://www.ncbi.nlm.nih.gov/account/ (free) |

---

## ☁️ Streamlit Cloud Secrets

```toml
OPENAI_API_KEY = "sk-..."
NCBI_EMAIL = "your@email.com"
NCBI_API_KEY = "your-key"
```

---

## 🗺️ Roadmap

- **v1.0** — Single protein analysis, 8 databases, PDF export ✅
- **v2.0** — Batch analysis, CSV upload
- **v3.0** — Protein comparison, network visualization
- **v4.0** — Molecular docking integration
- **v5.0** — Autonomous hypothesis generation

---

## 🙏 Data Sources

UniProt · PubMed · GTEx · ClinVar · AlphaFold · RCSB PDB · STRING DB · Reactome · Open Targets

---

*Built for the bioinformatics research community* 🧬
