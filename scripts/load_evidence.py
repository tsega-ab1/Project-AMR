"""
Loads every data/evidence/*.json seed file into db/amr.sqlite.

Run this whenever you add a new evidence file:
    python scripts/load_evidence.py

Safe to re-run: it wipes and reloads both tables each time, so the
JSON files in data/evidence/ remain the single source of truth, not
the database. Don't hand-edit the database directly - edit the JSON
and re-run this instead, or your edits vanish on the next load.
"""
import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = REPO_ROOT / "data" / "evidence"
SCHEMA_PATH = REPO_ROOT / "db" / "schema.sql"
DB_PATH = REPO_ROOT / "db" / "amr.sqlite"


def load_all():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_PATH.read_text())
    conn.execute("DELETE FROM evidence_records")
    conn.execute("DELETE FROM sources")

    seed_files = sorted(EVIDENCE_DIR.glob("*.json"))
    if not seed_files:
        print(f"No seed files found in {EVIDENCE_DIR}")
        return

    total_records = 0
    for seed_file in seed_files:
        data = json.loads(seed_file.read_text())
        meta = data.get("_meta", {})

        if meta.get("source_doi"):
            conn.execute(
                """INSERT OR REPLACE INTO sources
                   (citation_doi, source_title, source_authors, source_institution,
                    source_journal, source_url, source_license, collection_period)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    meta.get("source_doi"),
                    meta.get("source_title"),
                    meta.get("source_authors"),
                    meta.get("source_institution"),
                    meta.get("source_journal"),
                    meta.get("source_url"),
                    meta.get("source_license"),
                    meta.get("collection_period"),
                ),
            )

        for rec in data.get("records", []):
            conn.execute(
                """INSERT INTO evidence_records
                   (pathogen, antibiotic_class, country, region, year,
                    resistance_pct, ci_lower, ci_upper, specimen, population,
                    source_type, confidence_tier, citation_doi, note, seed_file)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    rec.get("pathogen"),
                    rec.get("antibiotic_class"),
                    rec.get("country"),
                    rec.get("region"),
                    str(rec.get("year")),
                    rec.get("resistance_pct"),
                    (rec.get("ci_95") or [None, None])[0],
                    (rec.get("ci_95") or [None, None])[1],
                    rec.get("specimen"),
                    rec.get("population"),
                    rec.get("source_type"),
                    rec.get("confidence_tier"),
                    rec.get("citation_doi"),
                    rec.get("note"),
                    seed_file.name,
                ),
            )
            total_records += 1

    conn.commit()
    print(f"Loaded {total_records} evidence records from {len(seed_files)} file(s) into {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    load_all()
