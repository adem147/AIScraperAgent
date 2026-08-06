import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"

import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
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


@app.post("/api/scrape")
def trigger_scrape():
    """Trigger Playwright live browser scraping and vector embedding."""
    try:
        print("Launching Playwright web interception flow...")
        filtered_df = get_filtered_df()
        
        stored_points = []
        if filtered_df is not None and not filtered_df.empty:
            stored_points = embed_and_store_ami_descriptions(filtered_df)

        return {
            "status": "success",
            "message": f"Scraped and filtered {len(filtered_df) if filtered_df is not None else 0} opportunities.",
            "stored_count": len(stored_points),
            "top_endpoints": ENDPOINT_RESULTS[:5],
        }
    except Exception as e:
        print("Scrape trigger error:", e)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


class SendEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str
    is_html: bool = False


@app.post("/api/send-email")
def send_email(payload: SendEmailRequest):
    """
    Send an email via SMTP (e.g., Gmail SMTP using an App Password).
    Environment variables:
      - SMTP_SERVER (default: smtp.gmail.com)
      - SMTP_PORT (default: 587)
      - SMTP_USER
      - SMTP_PASSWORD (Gmail App Password)
      - SMTP_SENDER_EMAIL (optional, defaults to SMTP_USER)
    """
    load_dotenv()
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com").strip()
    try:
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
    except ValueError:
        smtp_port = 587

    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    sender_email = os.getenv("SMTP_SENDER_EMAIL", "").strip() or smtp_user

    if not smtp_user or not smtp_password or smtp_password == "your_gmail_app_password_here":
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": (
                    "SMTP credentials are missing or unconfigured. "
                    "Please set SMTP_USER and SMTP_PASSWORD (Gmail App Password) in your .env file."
                ),
            },
        )

    try:
        msg = EmailMessage()
        msg["Subject"] = payload.subject
        msg["From"] = sender_email
        msg["To"] = payload.to_email

        if payload.is_html:
            msg.add_alternative(payload.body, subtype="html")
        else:
            msg.set_content(payload.body)

        with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return {
            "status": "success",
            "message": f"Email successfully sent to {payload.to_email}",
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Failed to send email: {str(e)}"},
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

