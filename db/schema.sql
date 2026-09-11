-- Evidence-record schema for Project AMR.
-- One row = one reported resistance figure, always traceable to a source.
-- This is intentionally denormalized (country/pathogen/antibiotic as text,
-- not foreign keys) for V1 - normalize into lookup tables once you have
-- enough sources that typos/inconsistent naming become a real problem.

CREATE TABLE IF NOT EXISTS sources (
    citation_doi        TEXT PRIMARY KEY,
    source_title         TEXT NOT NULL,
    source_authors        TEXT,
    source_institution     TEXT,
    source_journal        TEXT,
    source_url            TEXT,
    source_license         TEXT,
    collection_period       TEXT
);

CREATE TABLE IF NOT EXISTS evidence_records (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    pathogen             TEXT NOT NULL,
    antibiotic_class        TEXT NOT NULL,
    country              TEXT NOT NULL,
    region               TEXT,
    year                 TEXT NOT NULL,   -- TEXT not INT: some records are "2017-2021 aggregate"
    resistance_pct         REAL NOT NULL,
    ci_lower              REAL,
    ci_upper              REAL,
    specimen             TEXT,
    population             TEXT,
    source_type           TEXT NOT NULL,   -- e.g. "national reference laboratory surveillance"
    confidence_tier         TEXT NOT NULL,   -- high / moderate / low / very low
    citation_doi           TEXT NOT NULL REFERENCES sources(citation_doi),
    note                 TEXT,
    seed_file             TEXT NOT NULL     -- which data/evidence/*.json this came from, for traceability
);

CREATE INDEX IF NOT EXISTS idx_evidence_pathogen ON evidence_records(pathogen);
CREATE INDEX IF NOT EXISTS idx_evidence_country ON evidence_records(country);
CREATE INDEX IF NOT EXISTS idx_evidence_antibiotic ON evidence_records(antibiotic_class);
