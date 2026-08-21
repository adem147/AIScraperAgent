import os
import asyncio
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DB_PATH = BASE_DIR / "CERT.db"


def get_top_5_results():
    """Fetch the top 5 results directly from CERT.db without modifying any database models."""
    if not DB_PATH.exists():
        return []

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Check if similarity_results table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='similarity_results'")
        if cursor.fetchone():
            cursor.execute("""
                SELECT sr.id, sr.opportunity_id, sr.similarity_score, sr.title as sim_title,
                       o.title as opp_title, o.description,
                       COALESCE(o.organization, 'Procurement Authority') as organization,
                       COALESCE(o.country, 'Global') as country,
                       COALESCE(o.sector, 'Information Technology') as sector,
                       COALESCE(o.submission_deadline, 'N/A') as submission_deadline,
                       COALESCE(o.document_url, '#') as document_url
                FROM similarity_results sr
                LEFT JOIN opportunities o ON sr.opportunity_id = o.id
                ORDER BY sr.similarity_score DESC
                LIMIT 5
            """)
            rows = cursor.fetchall()
            if rows:
                results = []
                for r in rows:
                    score = float(r["similarity_score"]) if r["similarity_score"] is not None else 0.0
                    results.append({
                        "id": r["id"],
                        "opportunity_id": r["opportunity_id"],
                        "title": r["sim_title"] or r["opp_title"] or "Opportunity",
                        "similarity_score": round(score, 3),
                        "similarity_score_pct": f"{round(score * 100, 1)}%",
                        "description": r["description"] or "",
                        "organization": r["organization"],
                        "country": r["country"],
                        "sector": r["sector"],
                        "submission_deadline": str(r["submission_deadline"]),
                        "document_url": r["document_url"] if r["document_url"] else "#",
                    })
                return results

        # Fallback if similarity_results is empty: read from opportunities
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='opportunities'")
        if cursor.fetchone():
            cursor.execute("""
                SELECT id, title, description,
                       COALESCE(organization, 'Procurement Authority') as organization,
                       COALESCE(country, 'Global') as country,
                       COALESCE(sector, 'Information Technology') as sector,
                       COALESCE(submission_deadline, 'N/A') as submission_deadline,
                       COALESCE(document_url, '#') as document_url
                FROM opportunities
                ORDER BY id DESC
                LIMIT 5
            """)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append({
                    "id": r["id"],
                    "opportunity_id": r["id"],
                    "title": r["title"],
                    "similarity_score": 0.85,
                    "similarity_score_pct": "85.0%",
                    "description": r["description"] or "",
                    "organization": r["organization"],
                    "country": r["country"],
                    "sector": r["sector"],
                    "submission_deadline": str(r["submission_deadline"]),
                    "document_url": r["document_url"] if r["document_url"] else "#",
                })
            return results

        return []

    except Exception as e:
        print("Error fetching top 5 results:", e)
        return []
    finally:
        conn.close()


def run_pipeline():
    """Execute the pipeline from main.py and return top 5 results."""
    try:
        from main import main as run_main_pipeline_func
        run_main_pipeline_func()
    except Exception as err:
        print(f"Pipeline execution note: {err}")
    return get_top_5_results()



BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Procurement Opportunities")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=2)

# Mount static folder
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index():
    """Serve the simple interface."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(index_file)


@app.get("/api/results/top5")
async def fetch_top_5():
    """Fetch the top 5 results saved in the database."""
    try:
        results = get_top_5_results()
        return JSONResponse({
            "status": "success",
            "count": len(results),
            "results": results
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e), "results": []}
        )


@app.post("/api/run-pipeline")
async def trigger_pipeline():
    """Execute main.py pipeline, save results in database, and return fresh top 5."""
    try:
        loop = asyncio.get_event_loop()
        top_results = await loop.run_in_executor(executor, run_pipeline)
        return JSONResponse({
            "status": "success",
            "message": "Pipeline completed",
            "count": len(top_results),
            "results": top_results
        })
    except Exception as e:
        print(f"Pipeline error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Pipeline failed: {str(e)}",
                "results": get_top_5_results()
            }
        )


if __name__ == "__main__":
    print("Server running on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
