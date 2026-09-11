"""
Pattern A: fetch on demand, no bulk storage.

Call this from your backend route handler when a user opens a specific
resistance gene's page (e.g. NDM-1, CTX-M-15) — not in any batch job.
AlphaFold DB's API is free, unauthenticated, and keyed on UniProt
accession, so there's nothing to pre-download; the 200M-structure
database stays on EBI's servers, you just ask for the one you need,
when you need it.

Example: GET /api/gene/NDM-1/structure -> calls get_structure("C7C422")
"""
import requests
from functools import lru_cache

ALPHAFOLD_BASE = "https://alphafold.ebi.ac.uk/api/prediction"


@lru_cache(maxsize=512)
def get_structure(uniprot_id: str) -> dict | None:
    """
    Returns AlphaFold prediction metadata (including structure file URLs)
    for a single UniProt accession. lru_cache means repeat requests for
    the same gene in this process's lifetime don't re-hit the API — but
    nothing is written to disk or committed to the repo. Restart the
    process and the cache is empty again; that's fine, the next request
    just fetches fresh from AlphaFold.
    """
    resp = requests.get(f"{ALPHAFOLD_BASE}/{uniprot_id}", timeout=10)
    if resp.status_code == 404:
        return None  # no AlphaFold prediction for this accession
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return None
    entry = data[0]
    return {
        "alphafold_id": entry.get("entryId"),
        "uniprot_id": uniprot_id,
        "pdb_url": entry.get("pdbUrl"),
        "cif_url": entry.get("cifUrl"),
        "confidence_avg_plddt": entry.get("globalMetricValue"),
    }


# Example wiring for a Flask/FastAPI-style route:
#
# @app.get("/api/gene/{gene_name}/structure")
# def gene_structure(gene_name: str):
#     uniprot_id = GENE_TO_UNIPROT.get(gene_name)  # your own small mapping
#     if not uniprot_id:
#         return {"error": "no UniProt mapping for this gene"}, 404
#     structure = get_structure(uniprot_id)
#     if structure is None:
#         return {"error": "no AlphaFold prediction available"}, 404
#     return structure
