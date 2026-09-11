"""
Refreshes small, versioned reference lookup tables. Run monthly by
.github/workflows/refresh-reference-data.yml — NOT called per user request.

Output: data/reference/card_genes.json, data/reference/glass_countries.json
Both stay small (thousands of rows, not millions) — this is lookup data,
not the evidence dataset itself.
"""
import json
import os
import requests

OUT_DIR = "data/reference"
os.makedirs(OUT_DIR, exist_ok=True)


def refresh_card_genes():
    """
    CARD publishes a downloadable data archive (no simple per-gene REST
    endpoint). Check https://card.mcmaster.ca/download for the current
    stable download URL before wiring this up — it's versioned, so the
    filename changes with releases. This is a placeholder shape; confirm
    the real URL and file format (it's a .tar.bz2 containing JSON) before
    running for real.
    """
    CARD_DOWNLOAD_URL = "https://card.mcmaster.ca/latest/data"  # verify on download page
    resp = requests.get(CARD_DOWNLOAD_URL, timeout=60)
    resp.raise_for_status()
    # CARD's archive needs extraction (tar.bz2 -> card.json). Real
    # implementation: save the archive, extract aro_index.json /
    # card.json, then filter down to just the fields your resistance-
    # mechanism tree needs (ARO id, name, gene family, drug class).
    # Left as a TODO since the extraction step depends on the exact
    # archive layout at the time you build this.
    raise NotImplementedError(
        "Download and extract CARD archive, then map to your gene-tree schema"
    )


def refresh_glass_countries():
    """
    data.who.int publishes machine-readable datasets under CC BY 4.0.
    Check the current indicator/API structure on data.who.int before
    wiring this up — WHO has moved their API surface before.
    """
    # Placeholder — confirm actual endpoint from data.who.int's current
    # API docs when you build this; the portal explicitly supports
    # machine-readable access.
    raise NotImplementedError("Wire up to data.who.int's current API/download endpoint")


if __name__ == "__main__":
    # Wrap each in try/except so one source failing doesn't block the other
    for name, fn in [("CARD genes", refresh_card_genes), ("GLASS countries", refresh_glass_countries)]:
        try:
            fn()
            print(f"Refreshed: {name}")
        except NotImplementedError as e:
            print(f"Skipped {name}: {e}")
