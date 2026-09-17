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
import json
from pathlib import Path
from functools import lru_cache

import requests

ALPHAFOLD_BASE = "https://alphafold.ebi.ac.uk/api/prediction"
GENE_REFERENCE_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "reference" / "resistance_genes.json"
)


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


def load_gene_reference() -> dict:
    """
    Loads data/reference/resistance_genes.json fresh on every call (it's a
    small file maintained by hand, not worth caching across edits during
    development). Only the top-level "genes" object is trusted - the
    "_needs_verification_before_adding" block is intentionally never read
    here, so an unverified candidate accession can never reach the API by
    accident.
    """
    with open(GENE_REFERENCE_PATH) as f:
        data = json.load(f)
    return data.get("genes", {})


def get_structure_for_gene(gene_name: str) -> dict | None:
    """
    Looks up gene_name (e.g. "CTX-M-15") in the verified reference table,
    then fetches its AlphaFold prediction.

    IMPORTANT CAVEAT to surface wherever this is displayed: this returns
    the predicted structure of the *canonical/reference allele* as
    deposited in UniProt - not a structure folded from the exact isolate
    sequence in any particular evidence record. Two evidence records that
    both cite "NDM-1" will show the same structure here even if they're
    different studies in different years/countries, because they're
    reporting carriage of the same named gene, not two different folded
    sequences. Treat this as "here is what the reported mechanism looks
    like structurally", not "here is this isolate's exact protein".
    """
    genes = load_gene_reference()
    entry = genes.get(gene_name)
    if entry is None or not entry.get("verified", False):
        return None
    structure = get_structure(entry["uniprot_id"])
    if structure is None:
        return None
    structure["gene_name"] = gene_name
    structure["mechanism_family"] = entry.get("mechanism_family")
    structure["ambler_class"] = entry.get("ambler_class")
    structure["reference_note"] = (
        "Predicted structure of the canonical UniProt-deposited allele for "
        f"{gene_name}, not a structure folded from any single isolate's sequence."
    )
    return structure


# Example wiring for a Flask/FastAPI-style route - see backend/main.py for
# the actual route (GET /gene/{gene_name}/structure), which calls
# get_structure_for_gene() above.
