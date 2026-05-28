"""
config/settings.py
------------------
ProteoSage v2.0 — Configuration
Reads from Streamlit secrets (cloud) or .env / environment variables (local).
"""
import os


def get_secret(key: str, default: str = "") -> str:
    """Get secret from Streamlit Cloud secrets or environment variable."""
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)


# ── LLM ──────────────────────────────────────────────────────
OPENAI_API_KEY: str = get_secret("OPENAI_API_KEY")
GEMINI_API_KEY: str = get_secret("GEMINI_API_KEY")
LLM_MODEL: str      = get_secret("LLM_MODEL", "gpt-4o-mini")

# ── NCBI ─────────────────────────────────────────────────────
NCBI_API_KEY: str = get_secret("NCBI_API_KEY")
NCBI_EMAIL:   str = get_secret("NCBI_EMAIL", "proteosage@bioinformatics.ai")

# ── API Base URLs ─────────────────────────────────────────────
UNIPROT_BASE_URL  = "https://rest.uniprot.org/uniprotkb"
PUBMED_BASE_URL   = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ALPHAFOLD_BASE_URL = "https://alphafold.ebi.ac.uk/api"
CLINVAR_BASE_URL  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
REACTOME_BASE_URL = "https://reactome.org/ContentService"
STRING_BASE_URL   = "https://string-db.org/api"

# ── Request Settings ──────────────────────────────────────────
REQUEST_TIMEOUT:    int = 30
MAX_RETRIES:        int = 2
MAX_PUBMED_RESULTS: int = 15

# ── Report Settings ───────────────────────────────────────────
APP_VERSION = "2.0.0"
APP_NAME    = "ProteoSage"
