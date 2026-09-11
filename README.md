# Project AMR — Africa AMR Intelligence Platform

An evidence-mapped antimicrobial resistance (AMR) dashboard for Africa,
built to go beyond a standard "AMR dashboard" toward an evidence map:
every resistance figure traceable to its source, scored by confidence,
filterable by pathogen/antibiotic/country/specimen/population.

## Status: V1 data scaffolding

This repo currently holds the data pipeline scaffolding, not the app
itself yet. See `docs/roadmap.md` (TODO: add) for the phased plan.

## Structure

```
data/
  evidence/       Curated AMR evidence records, one file per source.
                   Manually collected/transcribed — not auto-fetched,
                   since none of the primary sources (MAAP, ATLAS)
                   expose a live per-record API.
  reference/       Small lookup tables (CARD gene ontology, WHO GLASS
                   country indicators) refreshed monthly by the
                   GitHub Action below. Populated after you fill in
                   the real source URLs in scripts/refresh_reference_data.py.

scripts/
  refresh_reference_data.py   Run by the GitHub Action on a monthly
                   cron. Needs the CARD download URL and WHO GLASS
                   endpoint filled in before it will run — see
                   NotImplementedError markers in the file.

.github/workflows/
  refresh-reference-data.yml   Monthly cron + manual trigger
                   (workflow_dispatch) that runs the script above and
                   commits any changes to data/reference/.

backend/
  alphafold_client.py   Fetch-on-demand client for AlphaFold DB —
                   called live per gene page view, nothing stored in
                   this repo. Needs a GENE_TO_UNIPROT mapping filled
                   in as you add resistance genes to the app.
```

## Data sources

| Source | Coverage | Access pattern |
|---|---|---|
| MAAP (ASLM/Africa CDC) | 14 African countries, 2016–2019 | Manual — published aggregate stats only; raw data is restricted (see `data/evidence/amr_seed_maap_2025.json` for the caveat). **Ethiopia is not covered.** |
| Pfizer ATLAS (via Vivli) | 70 countries, 2004–2017, 6.5M records | Manual browser export at atlas-surveillance.com |
| WHO GLASS / data.who.int | Country-level, CC BY 4.0 | Bulk download, refreshed via the GitHub Action |
| CARD (McMaster) | Resistance gene ontology | Bulk download, refreshed via the GitHub Action |
| AlphaFold DB | Protein structures | Live API, fetched on demand (no bulk storage) |

## Next steps

1. Fill in the two `NotImplementedError` spots in
   `scripts/refresh_reference_data.py` with the current CARD and WHO
   GLASS download URLs.
2. Run it locally (`pip install -r requirements.txt`, then
   `python scripts/refresh_reference_data.py`) before relying on the
   Action.
3. Add Ethiopia-specific evidence records to `data/evidence/` — MAAP
   doesn't cover Ethiopia, so this needs individual published studies.
4. Design and add the evidence-record schema/DB migration (not yet in
   this repo).
