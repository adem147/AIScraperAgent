import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"

from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd

from database.db import engine, Base
from qdrant_connection import get_collection_name, get_qdrant_client
from qdrant_embedding import (
    EMBED_MODEL,
    CLIENT,
    ensure_collection,
    embed_and_store_ami_descriptions,
    retrieve_data,
)
from sc2 import get_filtered_df, ENDPOINT_RESULTS

app = FastAPI(
    title="AIScraperAgent Intelligence Portal",
    description="AI-Driven Automated Monitoring & Vector Search System for Public Procurement Opportunities (AMI/AO)",
    version="1.0.0",
)

# Static files setup
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Sample seed dataset so the dashboard always has data to display immediately
SAMPLE_SEED_DATA = [
    {
        "id": "WB-PROC-2026-001",
        "title": "Consulting Services for National Cybersecurity & Threat Detection System",
        "description": "Expression of Interest (EOI) for implementing an AI-powered national Security Operations Center (SOC), threat intelligence feed integration, and vulnerability assessment tools for critical infrastructure.",
        "organization": "World Bank / Ministry of Digital Economy",
        "country": "Tunisia",
        "sector": "Information & Communications Technologies",
        "submission_deadline": "2026-08-25",
        "url": "https://projects.worldbank.org/en/projects-operations/opportunities",
        "score": 0.942,
    },
    {
        "id": "WB-PROC-2026-002",
        "title": "Development of Enterprise AI Data Lake & Machine Learning Analytics Platform",
        "description": "Public procurement opportunity seeking software engineering firms to design, build, and deploy a scalable cloud data lake with machine learning predictive analytics for public sector decision-making.",
        "organization": "African Development Bank (AfDB)",
        "country": "Regional / Multi-Country",
        "sector": "Software Engineering & Data Science",
        "submission_deadline": "2026-09-10",
        "url": "https://projects.worldbank.org/en/projects-operations/opportunities",
        "score": 0.895,
    },
    {
        "id": "WB-PROC-2026-003",
        "title": "Digital Transformation & Cloud Infrastructure Migration Project",
        "description": "Call for tenders for cloud architecture consultancy, microservices refactoring, Kubernetes cluster management, and secure devops pipeline automation for government digital services.",
        "organization": "United Nations Procurement Division",
        "country": "Global",
        "sector": "Cloud Computing & Automation",
        "submission_deadline": "2026-08-30",
        "url": "https://www.un.org/procurement/eoi",
        "score": 0.861,
    },
    {
        "id": "WB-PROC-2026-004",
        "title": "Health Information System & Telemedicine Digital Platform Implementation",
        "description": "Tender notice for procuring an integrated electronic health records (EHR) platform, telemedicine video consultation portal, and secure medical data analytics dashboard.",
        "organization": "Ministry of Public Health / World Health Organization",
        "country": "Tunisia",
        "sector": "Healthcare & Digital Health",
        "submission_deadline": "2026-09-01",
        "url": "https://projects.worldbank.org/en/projects-operations/opportunities",
        "score": 0.814,
    },
]


def initialize_seed_data():
    """Ensure database and Qdrant collection exist and seed initial demo records if empty."""
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        print("Database metadata init info:", e)

    collection_name = get_collection_name()
    if CLIENT is not None and ensure_collection(collection_name):
        existing = retrieve_data(collection_name)
        if not existing:
            print("Seeding initial demonstration dataset into Qdrant vector database...")
            df = pd.DataFrame(SAMPLE_SEED_DATA)
            embed_and_store_ami_descriptions(df, collection_name=collection_name)


@app.on_event("startup")
def startup_event():
    initialize_seed_data()


@app.get("/", response_class=HTMLResponse)
def read_root():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>AIScraperAgent API Server is Running</h1><p>Visit <a href='/static/index.html'>/static/index.html</a></p>")


@app.get("/api/stats")
def get_stats():
    collection_name = get_collection_name()
    points_count = 0
    client_status = "Connected (In-Memory)" if CLIENT else "Disconnected"

    if CLIENT is not None:
        try:
            info = CLIENT.get_collection(collection_name)
            points_count = info.points_count
        except Exception:
            points_count = len(SAMPLE_SEED_DATA)

    return {
        "collection_name": collection_name,
        "points_count": points_count or len(SAMPLE_SEED_DATA),
        "vector_dimension": 384,
        "embedding_model": "all-MiniLM-L6-v2",
        "client_status": client_status,
        "intercepted_endpoints_count": len(ENDPOINT_RESULTS),
    }


@app.get("/api/opportunities")
def get_opportunities():
    collection_name = get_collection_name()
    items = []

    if CLIENT is not None:
        try:
            points = retrieve_data(collection_name)
            for p in points:
                payload = p.payload or {}
                items.append({
                    "id": payload.get("id", str(p.id)),
                    "title": payload.get("title", "Untitled Opportunity"),
                    "description": payload.get("description", ""),
                    "organization": payload.get("organization", "International Organization"),
                    "country": payload.get("country", "Global"),
                    "sector": payload.get("sector", "Public Procurement"),
                    "submission_deadline": payload.get("submission_deadline", "N/A"),
                    "url": payload.get("url", "https://projects.worldbank.org"),
                    "score": round(float(getattr(p, "score", 0.90)), 3) if hasattr(p, "score") else 0.90,
                })
        except Exception as e:
            print("Fallback to seed data:", e)

    if not items:
        items = SAMPLE_SEED_DATA

    return {"count": len(items), "items": items}


@app.get("/api/search")
def search_opportunities(query: str = Query(..., min_length=1)):
    collection_name = get_collection_name()
    results = []

    if CLIENT is not None:
        try:
            query_vector = EMBED_MODEL.encode(query).tolist()
            res = CLIENT.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=10,
            )

            for r in res.points:
                payload = r.payload or {}
                results.append({
                    "id": payload.get("id", str(r.id)),
                    "title": payload.get("title", "Untitled Opportunity"),
                    "description": payload.get("description", ""),
                    "organization": payload.get("organization", "International Organization"),
                    "country": payload.get("country", "Global"),
                    "sector": payload.get("sector", "Public Procurement"),
                    "submission_deadline": payload.get("submission_deadline", "N/A"),
                    "url": payload.get("url", "https://projects.worldbank.org"),
                    "score": round(float(r.score), 4),
                })
        except Exception as e:
            print("Vector search exception, falling back to substring scoring:", e)

    # Fallback in case Qdrant in-memory state is empty or fails
    if not results:
        query_vec = EMBED_MODEL.encode([query])
        for seed in SAMPLE_SEED_DATA:
            desc_vec = EMBED_MODEL.encode([seed["description"]])
            from sklearn.metrics.pairwise import cosine_similarity
            score = cosine_similarity(query_vec, desc_vec)[0][0]
            item = dict(seed)
            item["score"] = round(float(score), 4)
            results.append(item)
        results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "query": query,
        "count": len(results),
        "results": results,
    }


from pydantic import BaseModel
from LLM.pipeline import get_pipeline
from LLM.schemas import ProcurementNotice


class ExtractTextRequest(BaseModel):
    text: str
    source_name: Optional[str] = "Manual Ingestion"
    source_url: Optional[str] = None
    persist: bool = True


@app.post("/api/extract", response_model=ProcurementNotice)
def extract_from_notice_text(payload: ExtractTextRequest):
    """Phase 2 NLP Multilingual extraction & feasibility analysis for raw text or PDF/HTML content."""
    pipeline = get_pipeline()
    notice = pipeline.process(
        raw_input=payload.text,
        source_name=payload.source_name,
        source_url=payload.source_url,
        persist_db=payload.persist,
    )
    return notice


@app.post("/api/transform-json", response_model=ProcurementNotice)
def transform_heterogeneous_json(raw_json: dict, persist: bool = True):
    """Phase 2 JSON schema transformer: converts non-standard JSON into standardized ProcurementNotice."""
    pipeline = get_pipeline()
    notice = pipeline.process(
        raw_input=raw_json,
        persist_db=persist,
    )
    return notice


@app.get("/api/opportunities/detailed")
def get_detailed_opportunities(only_relevant: bool = False):
    """Retrieve all structured Phase 2 opportunities from SQLite database."""
    from database.db import SessionLocal
    from database.models import Opportunity
    
    session = SessionLocal()
    try:
        query = session.query(Opportunity)
        if only_relevant:
            query = query.filter(Opportunity.is_relevant == True)
        
        opps = query.order_by(Opportunity.id.desc()).all()
        results = []
        for opp in opps:
            results.append({
                "id": opp.id,
                "title": opp.title,
                "description": opp.description,
                "organization": opp.organization,
                "submission_deadline": opp.submission_deadline,
                "country": opp.country,
                "sector": opp.sector,
                "language": opp.language,
                "budget": opp.budget,
                "criteres": opp.criteres or [],
                "lots": opp.lots or [],
                "documents_requis": opp.documents_requis or [],
                "dates": opp.dates or {},
                "relevance_score": opp.relevance_score,
                "is_relevant": opp.is_relevant,
                "relevance_rationale": opp.relevance_rationale,
                "synthese_opportunite": opp.synthese_opportunite,
                "analyse_faisabilite": opp.analyse_faisabilite,
            })
        return {"count": len(results), "opportunities": results}
    finally:
        session.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

