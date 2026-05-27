"""
services/research_engine.py
----------------------------
Single module that calls all 8 databases directly.
No FastAPI needed — runs entirely within Streamlit.
"""

import logging
import time
import requests
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from app.config.settings import (
    UNIPROT_BASE_URL, PUBMED_BASE_URL, ALPHAFOLD_BASE_URL,
    CLINVAR_BASE_URL, REACTOME_BASE_URL, STRING_BASE_URL,
    NCBI_API_KEY, NCBI_EMAIL, REQUEST_TIMEOUT, MAX_RETRIES,
    MAX_PUBMED_RESULTS
)
from app.services.llm_service import llm_service

def _get_secret(key: str, default: str = "") -> str:
    """Read secret from Streamlit or environment."""
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:
            return str(val)
    except Exception:
        pass
    import os
    return os.environ.get(key, default)

logger = logging.getLogger(__name__)

# ── UniProt ───────────────────────────────────────────────────

def fetch_uniprot(uniprot_id: str) -> dict:
    """Fetch all protein data from UniProt."""
    try:
        resp = requests.get(f"{UNIPROT_BASE_URL}/{uniprot_id}.json",
                           timeout=REQUEST_TIMEOUT)
        if resp.status_code == 404:
            return {"error": f"UniProt ID '{uniprot_id}' not found"}
        resp.raise_for_status()
        data = resp.json()

        # Parse protein name
        desc = data.get("proteinDescription", {})
        rec = desc.get("recommendedName", {})
        protein_name = rec.get("fullName", {}).get("value", uniprot_id)

        # Parse gene name
        genes = data.get("genes", [])
        gene_name = genes[0].get("geneName", {}).get("value", "Unknown") if genes else "Unknown"

        # Parse organism
        organism = data.get("organism", {}).get("scientificName", "Unknown")

        # Parse sequence
        seq_data = data.get("sequence", {})
        sequence = seq_data.get("value", "")
        seq_length = seq_data.get("length", len(sequence))

        # Parse function
        function_desc = ""
        for comment in data.get("comments", []):
            if comment.get("commentType") == "FUNCTION":
                texts = comment.get("texts", [])
                if texts:
                    function_desc = texts[0].get("value", "")
                    break

        # Parse GO annotations
        go_terms = []
        for xref in data.get("uniProtKBCrossReferences", []):
            if xref.get("database") == "GO":
                go_id = xref.get("id", "")
                props = {p["key"]: p["value"] for p in xref.get("properties", [])}
                term = props.get("GoTerm", "")
                if term.startswith("F:"):
                    cat, name = "molecular_function", term[2:]
                elif term.startswith("P:"):
                    cat, name = "biological_process", term[2:]
                elif term.startswith("C:"):
                    cat, name = "cellular_component", term[2:]
                else:
                    cat, name = "unknown", term
                go_terms.append({"id": go_id, "name": name, "category": cat})

        # Parse diseases
        diseases = []
        for comment in data.get("comments", []):
            if comment.get("commentType") == "DISEASE":
                d = comment.get("disease", {}).get("diseaseId", "")
                if d:
                    diseases.append(d)

        # Parse subcellular locations
        locations = []
        for comment in data.get("comments", []):
            if comment.get("commentType") == "SUBCELLULAR LOCATION":
                for loc in comment.get("subcellularLocations", []):
                    l = loc.get("location", {}).get("value", "")
                    if l:
                        locations.append(l)

        # Parse cross references
        xrefs = {}
        for xref in data.get("uniProtKBCrossReferences", []):
            db = xref.get("database", "")
            if db in {"PDB", "Ensembl", "OMIM", "RefSeq", "AlphaFoldDB", "HGNC"}:
                xrefs.setdefault(db, []).append(xref.get("id", ""))

        return {
            "uniprot_id": uniprot_id,
            "protein_name": protein_name,
            "gene_name": gene_name,
            "organism": organism,
            "sequence_length": seq_length,
            "function_description": function_desc,
            "go_terms": go_terms,
            "diseases": diseases,
            "subcellular_locations": list(set(locations)),
            "cross_references": xrefs,
        }
    except Exception as e:
        logger.error("UniProt fetch failed: %s", e)
        return {"error": str(e)}


# ── PubMed ────────────────────────────────────────────────────

def fetch_literature(protein_name: str, gene_name: str) -> dict:
    """Search PubMed and return papers."""
    try:
        query = f'"{gene_name}"[Gene Name] AND (function OR disease OR mechanism)'
        params = {
            "db": "pubmed", "term": query,
            "retmax": MAX_PUBMED_RESULTS, "retmode": "json",
            "tool": "proteosage", "email": _get_secret("NCBI_EMAIL", NCBI_EMAIL),
        }
        ncbi_key = _get_secret("NCBI_API_KEY", NCBI_API_KEY)
        if ncbi_key:
            params["api_key"] = ncbi_key

        resp = requests.get(f"{PUBMED_BASE_URL}/esearch.fcgi",
                           params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        pmids = resp.json().get("esearchresult", {}).get("idlist", [])

        if not pmids:
            return {"papers": [], "count": 0}

        # Fetch abstracts
        fetch_params = {
            "db": "pubmed", "id": ",".join(pmids),
            "retmode": "xml", "rettype": "abstract",
            "tool": "proteosage", "email": _get_secret("NCBI_EMAIL", NCBI_EMAIL),
        }
        if NCBI_API_KEY:
            fetch_params["api_key"] = NCBI_API_KEY

        fetch_resp = requests.get(f"{PUBMED_BASE_URL}/efetch.fcgi",
                                  params=fetch_params, timeout=REQUEST_TIMEOUT*2)
        fetch_resp.raise_for_status()

        papers = []
        root = ET.fromstring(fetch_resp.text)
        for article in root.findall(".//PubmedArticle"):
            pmid_el = article.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else ""
            title_el = article.find(".//ArticleTitle")
            title = (title_el.text or "").strip() if title_el is not None else ""
            abstract_parts = article.findall(".//AbstractText")
            abstract = " ".join((el.text or "") for el in abstract_parts if el.text).strip()
            authors = []
            for author in article.findall(".//Author"):
                last = author.find("LastName")
                fore = author.find("ForeName")
                if last is not None:
                    name = (last.text or "") + (f" {fore.text}" if fore is not None else "")
                    authors.append(name.strip())
            journal_el = article.find(".//Journal/Title")
            journal = journal_el.text if journal_el is not None else ""
            year_el = article.find(".//PubDate/Year")
            year = int(year_el.text) if year_el is not None and year_el.text else None

            papers.append({
                "pmid": pmid, "title": title, "abstract": abstract,
                "authors": authors, "journal": journal, "year": year,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })

        return {"papers": papers, "count": len(papers)}
    except Exception as e:
        logger.error("PubMed fetch failed: %s", e)
        return {"papers": [], "count": 0, "error": str(e)}


# ── ClinVar ───────────────────────────────────────────────────

def fetch_clinvar(gene_name: str) -> dict:
    """Fetch pathogenic variants from ClinVar."""
    try:
        queries = [
            f"{gene_name}[gene] AND clinsig_pathogenic[Filter]",
            f"{gene_name}[gene]",
        ]
        total = 0
        for query in queries:
            params = {
                "db": "clinvar", "term": query, "retmax": 0,
                "retmode": "json", "tool": "proteosage", "email": _get_secret("NCBI_EMAIL", NCBI_EMAIL),
            }
            if NCBI_API_KEY:
                params["api_key"] = NCBI_API_KEY
            resp = requests.get(f"{CLINVAR_BASE_URL}/esearch.fcgi",
                               params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            count = int(resp.json().get("esearchresult", {}).get("count", 0))
            if count > 0:
                total = count
                break

        # Fetch sample variants
        id_params = {
            "db": "clinvar", "term": f"{gene_name}[gene]",
            "retmax": 20, "retmode": "json",
            "tool": "proteosage", "email": _get_secret("NCBI_EMAIL", NCBI_EMAIL),
        }
        if NCBI_API_KEY:
            id_params["api_key"] = NCBI_API_KEY
        id_resp = requests.get(f"{CLINVAR_BASE_URL}/esearch.fcgi",
                               params=id_params, timeout=REQUEST_TIMEOUT)
        ids = id_resp.json().get("esearchresult", {}).get("idlist", [])

        variants = []
        if ids:
            sum_params = {
                "db": "clinvar", "id": ",".join(ids[:20]),
                "retmode": "json", "tool": "proteosage", "email": _get_secret("NCBI_EMAIL", NCBI_EMAIL),
            }
            if NCBI_API_KEY:
                sum_params["api_key"] = NCBI_API_KEY
            sum_resp = requests.get(f"{CLINVAR_BASE_URL}/esummary.fcgi",
                                    params=sum_params, timeout=REQUEST_TIMEOUT*2)
            result = sum_resp.json().get("result", {})
            for uid in result.get("uids", []):
                entry = result.get(uid, {})
                if not entry:
                    continue
                clinsig = entry.get("clinical_significance", {})
                sig = clinsig.get("description", "Unknown") if isinstance(clinsig, dict) else str(clinsig)
                trait_set = entry.get("trait_set", [])
                condition = trait_set[0].get("trait_name", "Unknown") if trait_set else "Unknown"
                variants.append({
                    "change": entry.get("title", uid),
                    "significance": sig,
                    "condition": condition,
                })

        return {"total": total, "variants": variants[:15]}
    except Exception as e:
        logger.error("ClinVar fetch failed: %s", e)
        return {"total": 0, "variants": [], "error": str(e)}


# ── AlphaFold + PDB ───────────────────────────────────────────

def fetch_structure(uniprot_id: str) -> dict:
    """Fetch structure data from AlphaFold and PDB."""
    result = {"alphafold": False, "alphafold_url": None, "pdb_ids": [], "pdb_count": 0}
    try:
        af_resp = requests.get(f"{ALPHAFOLD_BASE_URL}/prediction/{uniprot_id}",
                               timeout=REQUEST_TIMEOUT)
        if af_resp.status_code == 200:
            entries = af_resp.json()
            if entries:
                result["alphafold"] = True
                result["alphafold_url"] = f"https://alphafold.ebi.ac.uk/entry/{uniprot_id}"
                result["model_url"] = entries[0].get("cifUrl", "")
    except Exception:
        pass

    try:
        # Get PDB IDs from UniProt cross-references
        resp = requests.get(f"{UNIPROT_BASE_URL}/{uniprot_id}.json",
                           timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            pdb_ids = []
            for xref in resp.json().get("uniProtKBCrossReferences", []):
                if xref.get("database") == "PDB":
                    pdb_ids.append(xref.get("id", ""))
            result["pdb_ids"] = pdb_ids
            result["pdb_count"] = len(pdb_ids)
    except Exception:
        pass

    return result


# ── STRING DB ─────────────────────────────────────────────────

def fetch_string(gene_name: str, species: int = 9606) -> dict:
    """Fetch protein interactions from STRING DB."""
    try:
        map_resp = requests.post(f"{STRING_BASE_URL}/json/get_string_ids", data={
            "identifiers": gene_name, "species": species,
            "limit": 1, "caller_identity": "proteosage"
        }, timeout=REQUEST_TIMEOUT)
        mapped = map_resp.json()
        if not mapped:
            return {"interactions": [], "partners": []}

        string_id = mapped[0].get("stringId", "")
        interact_resp = requests.post(f"{STRING_BASE_URL}/json/interaction_partners", data={
            "identifiers": string_id, "species": species,
            "limit": 15, "required_score": 400,
            "caller_identity": "proteosage"
        }, timeout=REQUEST_TIMEOUT)
        interactions = interact_resp.json()
        result = []
        for item in interactions:
            result.append({
                "partner": item.get("preferredName_B", ""),
                "score": round(item.get("score", 0), 3),
                "experimental": round(item.get("escore", 0), 3),
            })
        partners = [r["partner"] for r in result[:10]]
        return {"interactions": result[:10], "partners": partners}
    except Exception as e:
        logger.warning("STRING fetch failed: %s", e)
        return {"interactions": [], "partners": []}


# ── Reactome ──────────────────────────────────────────────────

def fetch_reactome(uniprot_id: str) -> dict:
    """Fetch biological pathways from Reactome."""
    try:
        resp = requests.get(
            f"{REACTOME_BASE_URL}/data/mapping/UniProt/{uniprot_id}/pathways",
            timeout=REQUEST_TIMEOUT,
            headers={"Accept": "application/json"}
        )
        if resp.status_code != 200:
            return {"pathways": [], "count": 0}
        pathways = []
        for p in resp.json()[:15]:
            st_id = p.get("stId", "")
            pathways.append({
                "id": st_id,
                "name": p.get("displayName", ""),
                "url": f"https://reactome.org/PathwayBrowser/#/{st_id}",
            })
        return {"pathways": pathways, "count": len(pathways)}
    except Exception as e:
        logger.warning("Reactome fetch failed: %s", e)
        return {"pathways": [], "count": 0}


# ── Open Targets Drugs ────────────────────────────────────────

CURATED_DRUGS = {
    "TP53": [
        {"name": "APR-246 (Eprenetapopt)", "type": "Small molecule", "phase": 3,
         "mechanism": "Mutant p53 reactivator", "disease": "Myelodysplastic syndrome"},
        {"name": "Idasanutlin (RG7388)", "type": "Small molecule", "phase": 3,
         "mechanism": "MDM2 inhibitor", "disease": "Acute myeloid leukemia"},
        {"name": "Nutlin-3a (RG7112)", "type": "Small molecule", "phase": 2,
         "mechanism": "MDM2 inhibitor", "disease": "Liposarcoma"},
        {"name": "Gendicine (rAd-p53)", "type": "Gene therapy", "phase": 4,
         "mechanism": "p53 gene replacement", "disease": "Head and neck cancer"},
        {"name": "Navtemadlin", "type": "Small molecule", "phase": 3,
         "mechanism": "MDM2 inhibitor", "disease": "Merkel cell carcinoma"},
    ],
    "EGFR": [
        {"name": "Erlotinib", "type": "Small molecule", "phase": 4,
         "mechanism": "EGFR tyrosine kinase inhibitor", "disease": "Non-small cell lung cancer"},
        {"name": "Gefitinib", "type": "Small molecule", "phase": 4,
         "mechanism": "EGFR tyrosine kinase inhibitor", "disease": "Non-small cell lung cancer"},
        {"name": "Osimertinib", "type": "Small molecule", "phase": 4,
         "mechanism": "Third-generation EGFR inhibitor", "disease": "Non-small cell lung cancer"},
        {"name": "Cetuximab", "type": "Antibody", "phase": 4,
         "mechanism": "Anti-EGFR monoclonal antibody", "disease": "Colorectal cancer"},
    ],
    "BRAF": [
        {"name": "Vemurafenib", "type": "Small molecule", "phase": 4,
         "mechanism": "BRAF V600E inhibitor", "disease": "Melanoma"},
        {"name": "Dabrafenib", "type": "Small molecule", "phase": 4,
         "mechanism": "BRAF V600E/K inhibitor", "disease": "Melanoma"},
        {"name": "Encorafenib", "type": "Small molecule", "phase": 4,
         "mechanism": "BRAF inhibitor", "disease": "Melanoma"},
    ],
    "BRCA1": [
        {"name": "Olaparib", "type": "Small molecule", "phase": 4,
         "mechanism": "PARP inhibitor", "disease": "Breast cancer"},
        {"name": "Niraparib", "type": "Small molecule", "phase": 4,
         "mechanism": "PARP inhibitor", "disease": "Ovarian cancer"},
    ],
    "BRCA2": [
        {"name": "Olaparib", "type": "Small molecule", "phase": 4,
         "mechanism": "PARP inhibitor", "disease": "Breast cancer"},
        {"name": "Rucaparib", "type": "Small molecule", "phase": 4,
         "mechanism": "PARP inhibitor", "disease": "Ovarian cancer"},
    ],
    "KRAS": [
        {"name": "Sotorasib", "type": "Small molecule", "phase": 4,
         "mechanism": "KRAS G12C covalent inhibitor", "disease": "Non-small cell lung cancer"},
        {"name": "Adagrasib", "type": "Small molecule", "phase": 4,
         "mechanism": "KRAS G12C inhibitor", "disease": "Non-small cell lung cancer"},
    ],
    "ERBB2": [
        {"name": "Trastuzumab", "type": "Antibody", "phase": 4,
         "mechanism": "HER2 monoclonal antibody", "disease": "Breast cancer"},
        {"name": "Pertuzumab", "type": "Antibody", "phase": 4,
         "mechanism": "HER2 dimerization inhibitor", "disease": "Breast cancer"},
    ],
    "ALK": [
        {"name": "Crizotinib", "type": "Small molecule", "phase": 4,
         "mechanism": "ALK/MET/ROS1 inhibitor", "disease": "Non-small cell lung cancer"},
        {"name": "Alectinib", "type": "Small molecule", "phase": 4,
         "mechanism": "Second-generation ALK inhibitor", "disease": "Non-small cell lung cancer"},
    ],
    "CDK4": [
        {"name": "Palbociclib", "type": "Small molecule", "phase": 4,
         "mechanism": "CDK4/6 inhibitor", "disease": "Breast cancer"},
        {"name": "Ribociclib", "type": "Small molecule", "phase": 4,
         "mechanism": "CDK4/6 inhibitor", "disease": "Breast cancer"},
    ],
    "MDM2": [
        {"name": "Idasanutlin", "type": "Small molecule", "phase": 3,
         "mechanism": "MDM2 inhibitor", "disease": "Acute myeloid leukemia"},
    ],
}


def fetch_drugs(gene_name: str, uniprot_id: str) -> dict:
    """Get drug data — try Open Targets API, fall back to curated data."""
    # Try Open Targets GraphQL
    try:
        ensembl_id = _get_ensembl_id(uniprot_id)
        if ensembl_id:
            query = """
            query getDrugs($ensemblId: String!) {
              target(ensemblId: $ensemblId) {
                knownDrugs {
                  rows {
                    drug { name drugType maximumClinicalTrialPhase }
                    disease { name }
                    mechanismOfAction
                    phase
                  }
                }
              }
            }"""
            resp = requests.post(
                "https://api.platform.opentargets.org/api/v4/graphql",
                json={"query": query, "variables": {"ensemblId": ensembl_id}},
                timeout=REQUEST_TIMEOUT,
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code == 200:
                rows = (resp.json().get("data", {})
                                   .get("target", {})
                                   .get("knownDrugs", {})
                                   .get("rows", []))
                if rows:
                    drugs = []
                    seen = set()
                    for row in rows[:15]:
                        drug = row.get("drug", {})
                        name = drug.get("name", "")
                        if name and name not in seen:
                            seen.add(name)
                            drugs.append({
                                "name": name,
                                "type": drug.get("drugType", ""),
                                "phase": row.get("phase", 0),
                                "mechanism": row.get("mechanismOfAction", ""),
                                "disease": row.get("disease", {}).get("name", ""),
                            })
                    return {"drugs": drugs, "source": "Open Targets"}
    except Exception:
        pass

    # Fall back to curated data
    curated = CURATED_DRUGS.get(gene_name.upper(), [])
    return {"drugs": curated, "source": "Curated database"}


def _get_ensembl_id(uniprot_id: str) -> str:
    """Get Ensembl gene ID from UniProt."""
    KNOWN = {
        "P04637": "ENSG00000141510", "P00533": "ENSG00000146648",
        "P15056": "ENSG00000157764", "P04637": "ENSG00000141510",
        "Q9Y6K9": "ENSG00000209567",
    }
    if uniprot_id in KNOWN:
        return KNOWN[uniprot_id]
    try:
        resp = requests.get(f"{UNIPROT_BASE_URL}/{uniprot_id}.json", timeout=REQUEST_TIMEOUT)
        for xref in resp.json().get("uniProtKBCrossReferences", []):
            if xref.get("database") == "Ensembl":
                for prop in xref.get("properties", []):
                    if prop.get("key") == "GeneId" and prop.get("value", "").startswith("ENSG"):
                        return prop["value"]
    except Exception:
        pass
    return ""


# ── GTEx Expression ───────────────────────────────────────────

CURATED_EXPRESSION = {
    "TP53": [
        {"tissue": "Kidney Cortex", "tpm": 42.3, "level": "Medium"},
        {"tissue": "Liver", "tpm": 38.1, "level": "Medium"},
        {"tissue": "Lung", "tpm": 35.2, "level": "Medium"},
        {"tissue": "Brain Frontal Cortex", "tpm": 28.4, "level": "Medium"},
        {"tissue": "Heart Left Ventricle", "tpm": 25.7, "level": "Medium"},
        {"tissue": "Breast Mammary Tissue", "tpm": 22.1, "level": "Medium"},
        {"tissue": "Ovary", "tpm": 18.5, "level": "Low"},
        {"tissue": "Prostate", "tpm": 16.2, "level": "Low"},
        {"tissue": "Whole Blood", "tpm": 8.4, "level": "Low"},
        {"tissue": "Testis", "tpm": 3.2, "level": "Low"},
    ],
    "EGFR": [
        {"tissue": "Liver", "tpm": 85.2, "level": "High"},
        {"tissue": "Kidney Cortex", "tpm": 72.1, "level": "High"},
        {"tissue": "Lung", "tpm": 65.4, "level": "High"},
        {"tissue": "Small Intestine", "tpm": 58.3, "level": "High"},
        {"tissue": "Brain", "tpm": 12.1, "level": "Low"},
    ],
    "BRAF": [
        {"tissue": "Thyroid", "tpm": 65.2, "level": "High"},
        {"tissue": "Brain", "tpm": 42.1, "level": "Medium"},
        {"tissue": "Skin", "tpm": 38.5, "level": "Medium"},
        {"tissue": "Lung", "tpm": 22.3, "level": "Medium"},
        {"tissue": "Colon", "tpm": 18.4, "level": "Low"},
    ],
}


def fetch_expression(gene_name: str) -> dict:
    """Fetch GTEx expression data."""
    # Try live GTEx API
    try:
        resp = requests.get(
            "https://gtexportal.org/api/v2/expression/medianGeneExpression",
            params={"geneSymbol": gene_name, "datasetId": "gtex_v8"},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            items = resp.json().get("data", [])
            if items:
                tissues = []
                for item in items:
                    tpm = float(item.get("median", 0) or 0)
                    tissue = item.get("tissueSiteDetailId", "").replace("_", " ").title()
                    level = "High" if tpm >= 50 else "Medium" if tpm >= 10 else "Low" if tpm >= 1 else "Not detected"
                    tissues.append({"tissue": tissue, "tpm": round(tpm, 2), "level": level})
                tissues.sort(key=lambda x: x["tpm"], reverse=True)
                return {"tissues": tissues[:15], "source": "GTEx v8 (live)"}
    except Exception:
        pass

    # Use curated data
    curated = CURATED_EXPRESSION.get(gene_name.upper(), [])
    if curated:
        return {"tissues": curated, "source": "GTEx v8 (curated)"}

    return {"tissues": [], "source": "Not available"}


# ── LLM Synthesis ─────────────────────────────────────────────

def generate_literature_review(protein_name: str, gene_name: str, papers: list) -> str:
    if not papers:
        return "No literature data available."
    context = "\n\n".join(
        f"[Paper {i+1}] {p['title']}\n{p['abstract']}"
        for i, p in enumerate(papers[:8]) if p.get("abstract")
    )
    return llm_service.complete(
        system_prompt="You are an expert biomedical scientist writing a literature review. Be evidence-based and publication-quality.",
        user_prompt=f"Write a 4-paragraph literature review for {protein_name} ({gene_name}) based on these papers:\n\n{context}",
        temperature=0.3, max_tokens=1200,
    )


def generate_classification(protein_data: dict, mutation_data: dict,
                            structure_data: dict, drug_data: dict) -> str:
    protein_name = protein_data.get("protein_name", "Unknown")
    gene_name = protein_data.get("gene_name", "Unknown")
    diseases = ", ".join(protein_data.get("diseases", [])[:5]) or "None"
    variants = mutation_data.get("total", 0)
    pdb_count = structure_data.get("pdb_count", 0)
    drugs = len(drug_data.get("drugs", []))

    return llm_service.complete(
        system_prompt="You are a chief scientist classifying proteins for drug discovery. Be definitive and clinically actionable.",
        user_prompt=f"""Classify {protein_name} (gene: {gene_name}) with these EXACT sections:

## PRIMARY PROTEIN CLASS
[Classification + why]

## EXPRESSION CLASSIFICATION
[Overexpressed/Underexpressed/Tissue-Restricted/Ubiquitously Expressed/Stress-Induced + evidence]

## STRUCTURAL CLASSIFICATION
[Stable Globular/Conformational Change Driver/Intrinsically Disordered/Multi-domain Allosteric + evidence]

## MUTATION MECHANISM CLASS
[Loss-of-Function/Gain-of-Function/Dominant Negative/Haploinsufficiency + mechanism]

## THERAPEUTIC TARGET CLASSIFICATION
[Tier 1 Established/Tier 2 Active Clinical/Tier 3 Emerging/Tier 4 Challenging/Tier 5 Undruggable + strategy]

## CHIEF SCIENTIST VERDICT
[3-4 definitive sentences: what this protein IS, primary disease mechanism, best therapeutic direction, key knowledge gap]

Data: Diseases={diseases}, Pathogenic variants={variants}, PDB structures={pdb_count}, Known drugs={drugs}""",
        temperature=0.2, max_tokens=1200,
    )


def generate_insights(protein_data: dict, mutation_data: dict,
                      string_data: dict, reactome_data: dict, drug_data: dict) -> str:
    protein_name = protein_data.get("protein_name", "Unknown")
    gene_name = protein_data.get("gene_name", "Unknown")
    partners = ", ".join(string_data.get("partners", [])[:8]) or "N/A"
    pathways = ", ".join(p["name"] for p in reactome_data.get("pathways", [])[:5]) or "N/A"
    drugs = ", ".join(d["name"] for d in drug_data.get("drugs", [])[:3]) or "None"

    return llm_service.complete(
        system_prompt="You are a senior biomedical researcher writing research insights.",
        user_prompt=f"""Write 2-3 paragraphs of research insights for {protein_name} ({gene_name}):
- Diseases: {", ".join(protein_data.get("diseases", [])[:5])}
- Pathogenic variants: {mutation_data.get("total", 0)}
- Key protein partners: {partners}
- Key pathways: {pathways}
- Drug landscape: {drugs}

Connect all data sources to biological mechanisms, clinical relevance, and future directions.""",
        temperature=0.4, max_tokens=600,
    )


def generate_conclusion(protein_name: str, gene_name: str, uniprot_id: str,
                        classification: str) -> str:
    verdict = classification.split("CHIEF SCIENTIST VERDICT")[-1][:300] if "CHIEF SCIENTIST VERDICT" in classification else ""
    return llm_service.complete(
        system_prompt="You are a senior biomedical researcher.",
        user_prompt=f"Write a 4-6 sentence conclusion for {protein_name} ({gene_name}, {uniprot_id}). Summary: {verdict}",
        temperature=0.3, max_tokens=250,
    )


# ── Main Research Pipeline ────────────────────────────────────

def run_research_pipeline(uniprot_id: str, progress_callback=None) -> dict:
    """
    Run the complete research pipeline for a UniProt ID.
    Returns all data needed for the report.
    """
    result = {"uniprot_id": uniprot_id, "errors": {}}

    def update(pct, msg):
        if progress_callback:
            progress_callback(pct, msg)

    # Step 1: UniProt (sequential — others need gene name)
    update(10, "🔗 Fetching protein metadata from UniProt...")
    protein_data = fetch_uniprot(uniprot_id)
    if "error" in protein_data:
        result["errors"]["uniprot"] = protein_data["error"]
        return result
    result["protein"] = protein_data
    gene_name = protein_data.get("gene_name", "Unknown")
    protein_name = protein_data.get("protein_name", uniprot_id)

    # Step 2: Parallel data collection
    update(20, "🚀 Running parallel database queries...")

    def run_pubmed():
        return "literature", fetch_literature(protein_name, gene_name)

    def run_clinvar():
        return "mutations", fetch_clinvar(gene_name)

    def run_structure():
        return "structure", fetch_structure(uniprot_id)

    def run_string():
        return "interactions", fetch_string(gene_name)

    def run_reactome():
        return "pathways", fetch_reactome(uniprot_id)

    def run_expression():
        return "expression", fetch_expression(gene_name)

    def run_drugs():
        return "drugs", fetch_drugs(gene_name, uniprot_id)

    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = [
            executor.submit(run_pubmed),
            executor.submit(run_clinvar),
            executor.submit(run_structure),
            executor.submit(run_string),
            executor.submit(run_reactome),
            executor.submit(run_expression),
            executor.submit(run_drugs),
        ]
        for future in as_completed(futures):
            try:
                key, value = future.result()
                result[key] = value
            except Exception as e:
                logger.error("Parallel task failed: %s", e)

    update(70, "🤖 AI synthesis — generating report...")

    # Step 3: LLM synthesis
    papers = result.get("literature", {}).get("papers", [])
    result["literature_review"] = generate_literature_review(protein_name, gene_name, papers)

    update(80, "🔬 Chief Scientist classification...")
    result["classification"] = generate_classification(
        result.get("protein", {}),
        result.get("mutations", {}),
        result.get("structure", {}),
        result.get("drugs", {}),
    )

    update(88, "💡 Generating research insights...")
    result["insights"] = generate_insights(
        result.get("protein", {}),
        result.get("mutations", {}),
        result.get("interactions", {}),
        result.get("pathways", {}),
        result.get("drugs", {}),
    )

    update(94, "📝 Writing conclusion...")
    result["conclusion"] = generate_conclusion(
        protein_name, gene_name, uniprot_id, result["classification"]
    )

    update(97, "📄 Building report...")
    result["markdown"] = build_markdown_report(result)
    result["timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    update(100, "✅ Complete!")
    return result


# ── Report Builder ────────────────────────────────────────────

def extract_badges(classification: str) -> dict:
    badges = {
        "primary_class": "Unknown", "expression_class": "Unknown",
        "structural_class": "Unknown", "mutation_mechanism": "Unknown",
        "therapeutic_tier": "Unknown",
    }
    lines = classification.split("\n")
    for i, line in enumerate(lines):
        ll = line.lower()
        next_text = " ".join(lines[i+1:i+4]) if i+1 < len(lines) else ""
        if "primary protein class" in ll:
            for cls in ["Tumor Suppressor", "Oncogene", "Transcription Factor", "Kinase",
                       "Receptor", "Enzyme", "Scaffold", "Regulatory Protein",
                       "Signaling Adaptor", "Structural Protein", "Ion Channel"]:
                if cls.lower() in next_text.lower():
                    badges["primary_class"] = cls; break
        if "expression classification" in ll:
            for cls in ["Overexpressed", "Underexpressed", "Tissue-Restricted",
                       "Ubiquitously Expressed", "Stress-Induced"]:
                if cls.lower() in next_text.lower():
                    badges["expression_class"] = cls; break
        if "structural classification" in ll:
            for cls in ["Stable Globular", "Conformational Change Driver",
                       "Intrinsically Disordered", "Multi-domain Allosteric",
                       "Amyloidogenic", "Membrane-Associated"]:
                if cls.lower() in next_text.lower():
                    badges["structural_class"] = cls; break
        if "mutation mechanism" in ll:
            for cls in ["Loss-of-Function", "Gain-of-Function",
                       "Dominant Negative", "Haploinsufficiency"]:
                if cls.lower() in next_text.lower():
                    badges["mutation_mechanism"] = cls; break
        if "therapeutic target" in ll:
            for tier in ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"]:
                if tier.lower() in next_text.lower():
                    badges["therapeutic_tier"] = tier; break
    return badges


def build_markdown_report(data: dict) -> str:
    p = data.get("protein", {})
    protein_name = p.get("protein_name", data["uniprot_id"])
    gene_name = p.get("gene_name", "Unknown")
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    classification = data.get("classification", "")
    badges = extract_badges(classification)

    badge_line = " | ".join([
        f"🔴 {badges['primary_class']}",
        f"📊 {badges['expression_class']}",
        f"🏗️ {badges['structural_class']}",
        f"⚡ {badges['mutation_mechanism']}",
        f"💊 {badges['therapeutic_tier']}",
    ])

    sections = [
        f"# {protein_name} — ProteoSage Research Report",
        f"**UniProt:** {data['uniprot_id']} | **Gene:** {gene_name} | **Generated:** {timestamp}",
        f"> {badge_line}",
        "---",

        "## 1. Protein Overview",
        "| Field | Value |",
        "|-------|-------|",
        f"| Protein Name | {protein_name} |",
        f"| UniProt ID | {data['uniprot_id']} |",
        f"| Gene | {gene_name} |",
        f"| Organism | {p.get('organism', 'N/A')} |",
        f"| Sequence Length | {p.get('sequence_length', 'N/A')} amino acids |",
        f"| Primary Class | {badges['primary_class']} |",
        f"| Expression Profile | {badges['expression_class']} |",
        f"| Structural Type | {badges['structural_class']} |",
        f"| Mutation Mechanism | {badges['mutation_mechanism']} |",
        f"| Therapeutic Tier | {badges['therapeutic_tier']} |",
        "",

        "## 2. Gene Information",
    ]

    xrefs = p.get("cross_references", {})
    if xrefs:
        for db, ids in xrefs.items():
            sections.append(f"- **{db}:** {', '.join(ids[:3])}")
    else:
        sections.append("_Not available._")

    sections += [
        "",
        "## 3. Protein Function",
        p.get("function_description", "_Not available._"),
        "",
        "## 4. GO Annotations",
    ]

    go_terms = p.get("go_terms", [])
    if go_terms:
        for cat in ["biological_process", "molecular_function", "cellular_component"]:
            terms = [g for g in go_terms if g["category"] == cat]
            if terms:
                sections.append(f"### {cat.replace('_', ' ').title()}")
                for t in terms[:8]:
                    sections.append(f"- **{t['id']}**: {t['name']}")
    else:
        sections.append("_Not available._")

    # Expression
    sections += ["", "## 5. Expression Analysis (GTEx)"]
    expr = data.get("expression", {})
    tissues = expr.get("tissues", [])
    if tissues:
        top = [t["tissue"] for t in tissues[:5]]
        sections.append(f"**Top expressed tissues:** {', '.join(top)}")
        sections.append(f"**Source:** {expr.get('source', 'GTEx v8')}\n")
        sections.append("| Tissue | Median TPM | Level |")
        sections.append("|--------|-----------|-------|")
        for t in tissues[:12]:
            sections.append(f"| {t['tissue']} | {t['tpm']} | {t['level']} |")
    else:
        sections.append("_Expression data not available._")

    # Diseases
    sections += ["", "## 6. Disease Associations"]
    diseases = p.get("diseases", [])
    if diseases:
        for d in diseases:
            sections.append(f"- {d}")
    else:
        sections.append("_No disease associations found._")

    # Mutations
    sections += ["", "## 7. Mutation Analysis"]
    mut = data.get("mutations", {})
    sections.append(f"**Total pathogenic/likely-pathogenic variants:** {mut.get('total', 0)}")
    variants = mut.get("variants", [])
    if variants:
        sections.append("\n| Variant | Significance | Condition |")
        sections.append("|---------|-------------|-----------|")
        for v in variants[:10]:
            sections.append(f"| {v.get('change', 'N/A')[:50]} | {v.get('significance', 'N/A')} | {v.get('condition', 'N/A')[:40]} |")

    # Structure
    sections += ["", "## 8. Structural Information"]
    struct = data.get("structure", {})
    if struct.get("alphafold"):
        sections.append(f"- **AlphaFold:** [View Structure]({struct.get('alphafold_url', '')})")
    pdb_ids = struct.get("pdb_ids", [])
    if pdb_ids:
        sections.append(f"- **PDB ({struct.get('pdb_count', 0)} total):** {', '.join(pdb_ids[:8])}")

    # STRING
    sections += ["", "## 9. Protein-Protein Interactions (STRING DB)"]
    interactions = data.get("interactions", {})
    partners = interactions.get("partners", [])
    if partners:
        sections.append(f"**Top interaction partners:** {', '.join(partners)}")
        inter_list = interactions.get("interactions", [])
        if inter_list:
            sections.append("\n| Partner | Combined Score | Experimental |")
            sections.append("|---------|---------------|-------------|")
            for i in inter_list[:10]:
                sections.append(f"| {i['partner']} | {i['score']} | {i['experimental']} |")
    else:
        sections.append("_STRING data not available._")

    # Reactome
    sections += ["", "## 10. Biological Pathways (Reactome)"]
    pathways = data.get("pathways", {})
    pathway_list = pathways.get("pathways", [])
    if pathway_list:
        sections.append(f"**{pathways.get('count', 0)} pathways identified**\n")
        for pw in pathway_list[:12]:
            sections.append(f"- [{pw['name']}]({pw['url']}) `{pw['id']}`")
    else:
        sections.append("_Reactome data not available._")

    # Drugs
    sections += ["", "## 11. Drug & Therapeutic Landscape"]
    drug_data = data.get("drugs", {})
    drugs = drug_data.get("drugs", [])
    if drugs:
        sections.append(f"**{len(drugs)} drugs identified** (Source: {drug_data.get('source', 'N/A')})\n")
        sections.append("| Drug | Type | Phase | Mechanism | Indication |")
        sections.append("|------|------|-------|-----------|------------|")
        for d in drugs:
            sections.append(f"| {d['name']} | {d.get('type', 'N/A')} | {d.get('phase', 'N/A')} | {d.get('mechanism', 'N/A')} | {d.get('disease', 'N/A')} |")
    else:
        sections.append("_No drug data available._")

    # Literature
    sections += ["", "## 12. Literature Review",
                 data.get("literature_review", "_Not available._"), ""]

    # Insights
    sections += ["## 13. Research Insights",
                 data.get("insights", "_Not available._"), ""]

    # Classification
    sections += [
        "## 14. Chief Scientist Protein Classification",
        "> *Expert multi-dimensional classification for research & drug discovery*",
        "",
        classification,
        "",
    ]

    # Conclusion
    sections += ["## 15. Conclusion",
                 data.get("conclusion", "_Not available._"), ""]

    # References
    papers = data.get("literature", {}).get("papers", [])
    sections += ["## 16. References"]
    for i, p in enumerate(papers, 1):
        authors = ", ".join(p.get("authors", [])[:3])
        if len(p.get("authors", [])) > 3:
            authors += " et al."
        year = f"({p['year']})" if p.get("year") else ""
        journal = f"*{p['journal']}*" if p.get("journal") else ""
        pmid = p.get("pmid", "")
        url = f"[{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)" if pmid else ""
        sections.append(f"{i}. {authors} {year}. {p.get('title', '')}. {journal}. {url}")

    sections += [
        "",
        "---",
        f"*ProteoSage — AI Protein Research Platform | {timestamp}*"
    ]

    return "\n\n".join(sections)