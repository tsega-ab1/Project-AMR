"""
Thin API over db/amr.sqlite. Run with:
    uvicorn backend.main:app --reload --port 8000

Then try, e.g.:
    http://localhost:8000/records?country=Ethiopia&pathogen=Klebsiella pneumoniae
    http://localhost:8000/countries
    http://localhost:8000/pathogens
    http://localhost:8000/docs   <- interactive Swagger UI, free from FastAPI
"""
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "db" / "amr.sqlite"

app = FastAPI(title="Project AMR API", version="0.1")

# Allow your frontend dev server to call this during local development.
# Tighten this to your actual frontend domain before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
def root():
    return {"service": "Project AMR API", "docs": "/docs"}


@app.get("/records")
def get_records(
    country: Optional[str] = None,
    pathogen: Optional[str] = None,
    antibiotic_class: Optional[str] = None,
    year: Optional[str] = None,
    min_confidence: Optional[str] = None,
):
    """
    Filter evidence records. All filters are optional and combine with AND.
    This is the one endpoint the map, timeline, and matrix features all call -
    they just pass different filter combinations.
    """
    query = "SELECT * FROM evidence_records WHERE 1=1"
    params = []

    if country:
        query += " AND country = ?"
        params.append(country)
    if pathogen:
        query += " AND pathogen = ?"
        params.append(pathogen)
    if antibiotic_class:
        query += " AND antibiotic_class = ?"
        params.append(antibiotic_class)
    if year:
        query += " AND year = ?"
        params.append(year)
    if min_confidence:
        # simple ordinal filter - treat confidence tiers as ranked
        tiers = {"very low": 0, "low": 1, "moderate": 2, "high": 3}
        min_rank = tiers.get(min_confidence.lower(), 0)
        allowed = [t for t, rank in tiers.items() if rank >= min_rank]
        placeholders = ",".join("?" for _ in allowed)
        query += f" AND confidence_tier IN ({placeholders})"
        params.extend(allowed)

    conn = get_conn()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return {"count": len(rows), "records": [dict(r) for r in rows]}


@app.get("/countries")
def list_countries():
    """Distinct countries currently in the database - for populating filter dropdowns."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT country FROM evidence_records ORDER BY country"
    ).fetchall()
    conn.close()
    return {"countries": [r["country"] for r in rows]}


@app.get("/pathogens")
def list_pathogens():
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT pathogen FROM evidence_records ORDER BY pathogen"
    ).fetchall()
    conn.close()
    return {"pathogens": [r["pathogen"] for r in rows]}


@app.get("/antibiotics")
def list_antibiotics():
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT antibiotic_class FROM evidence_records ORDER BY antibiotic_class"
    ).fetchall()
    conn.close()
    return {"antibiotic_classes": [r["antibiotic_class"] for r in rows]}


@app.get("/stats")
def get_stats():
    """Summary numbers for dashboard stat cards."""
    conn = get_conn()
    total_records = conn.execute("SELECT COUNT(*) c FROM evidence_records").fetchone()["c"]
    countries = conn.execute("SELECT COUNT(DISTINCT country) c FROM evidence_records").fetchone()["c"]
    antibiotics = conn.execute("SELECT COUNT(DISTINCT antibiotic_class) c FROM evidence_records").fetchone()["c"]
    pathogens = conn.execute("SELECT COUNT(DISTINCT pathogen) c FROM evidence_records").fetchone()["c"]
    sources = conn.execute("SELECT COUNT(*) c FROM sources").fetchone()["c"]
    conn.close()
    return {
        "total_records": total_records,
        "countries_reporting": countries,
        "antibiotics_tracked": antibiotics,
        "pathogens_tracked": pathogens,
        "evidence_sources": sources,
    }


@app.get("/top-resistant")
def top_resistant(limit: int = 5):
    """Pathogens with the highest average reported resistance - powers the 'Top Resistant Microbes' list."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT pathogen, ROUND(AVG(resistance_pct), 1) as avg_resistance, COUNT(*) as n_records
           FROM evidence_records
           GROUP BY pathogen
           ORDER BY avg_resistance DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return {"pathogens": [dict(r) for r in rows]}


@app.get("/by-country")
def by_country(pathogen: Optional[str] = None, antibiotic_class: Optional[str] = None):
    """Average resistance per country for a given pathogen/antibiotic - powers the country list/map."""
    query = """SELECT country, ROUND(AVG(resistance_pct), 1) as avg_resistance, COUNT(*) as n_records
               FROM evidence_records WHERE 1=1"""
    params = []
    if pathogen:
        query += " AND pathogen = ?"
        params.append(pathogen)
    if antibiotic_class:
        query += " AND antibiotic_class = ?"
        params.append(antibiotic_class)
    query += " GROUP BY country ORDER BY avg_resistance DESC"

    conn = get_conn()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return {"countries": [dict(r) for r in rows]}


@app.get("/by-antibiotic")
def by_antibiotic(pathogen: Optional[str] = None, country: Optional[str] = None):
    """Average resistance per antibiotic class - powers the Antibiotics view."""
    query = """SELECT antibiotic_class, ROUND(AVG(resistance_pct), 1) as avg_resistance, COUNT(*) as n_records
               FROM evidence_records WHERE 1=1"""
    params = []
    if pathogen:
        query += " AND pathogen = ?"
        params.append(pathogen)
    if country:
        query += " AND country = ?"
        params.append(country)
    query += " GROUP BY antibiotic_class ORDER BY avg_resistance DESC"

    conn = get_conn()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return {"antibiotic_classes": [dict(r) for r in rows]}


@app.get("/sources")
def list_sources():
    """All cited sources - powers the 'publication explorer' feature."""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM sources").fetchall()
    conn.close()
    return {"sources": [dict(r) for r in rows]}
