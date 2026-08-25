import pandas as pd
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database.db import engine, Base, SessionLocal, insert_opportunities
from database.storage import get_all_sources
from qdrant_connection import get_collection_name, get_qdrant_client
from qdrant_embedding import embed_and_store_ami_descriptions, retrive_spesific_data
from sc2 import get_filtred_df_dynamic
from static_sc import get_filtred_df_static
from database.models import Opportunity, SimilarityResult
import json


SOURCE = []
FRONTEND_DIR = Path(__file__).parent / "frontend"
app = FastAPI(title="CERT Opportunity Monitor")
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

with open("tests/test_data.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)


def create_database():
    print("Creating database...")
    Base.metadata.create_all(engine)
    print("Database created successfully!")


def opportunity_to_dict(opportunity: Opportunity, score: float = 0.0) -> dict[str, Any]:
    return {
        "id": opportunity.id,
        "title": opportunity.title or "Untitled opportunity",
        "description": opportunity.description or "",
        "url": opportunity.url or "",
        "sector": opportunity.sector or "",
        "published_date": opportunity.published_date.isoformat() if opportunity.published_date else None,
        "submission_deadline": opportunity.submission_deadline.isoformat() if opportunity.submission_deadline else None,
        "score": round(score, 3),
    }


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/sources")
def sources():
    return [{"id": source.id, "title": source.title, "url": source.url, "scrape_type": source.scrape_type}
            for source in get_all_sources()]


@app.get("/api/stats")
def stats():
    session = SessionLocal()
    try:
        return {"opportunities": session.query(Opportunity).count(), "sources": len(get_all_sources())}
    finally:
        session.close()


@app.get("/api/opportunities")
def search_opportunities(query: str = Query(default="", max_length=200)):
    session = SessionLocal()
    try:
        opportunities = session.query(Opportunity).all()
        terms = {term.lower() for term in query.split() if term.strip()}
        results = []
        for opportunity in opportunities:
            searchable = f"{opportunity.title or ''} {opportunity.description or ''} {opportunity.sector or ''}".lower()
            score = sum(term in searchable for term in terms) / len(terms) if terms else 0.0
            if not terms or score > 0:
                results.append(opportunity_to_dict(opportunity, score))
        results.sort(key=lambda item: item["score"], reverse=True)
        return {"count": len(results), "results": results[:50]}
    finally:
        session.close()


@app.delete("/api/opportunities/{opportunity_id}")
def delete_opportunity(opportunity_id: int):
    session = SessionLocal()
    try:
        opportunity = session.get(Opportunity, opportunity_id)
        if opportunity is None:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        session.query(SimilarityResult).filter(
            SimilarityResult.opportunity_id == opportunity_id
        ).delete(synchronize_session=False)
        session.delete(opportunity)
        session.commit()

        qdrant_client = get_qdrant_client()
        if qdrant_client is not None:
            try:
                from qdrant_client import models

                qdrant_client.delete(
                    collection_name=get_collection_name(),
                    points_selector=models.PointIdsList(points=[opportunity_id]),
                )
            except Exception as error:
                print(f"Qdrant deletion skipped: {error}")

        return {"status": "deleted", "id": opportunity_id}
    except HTTPException:
        raise
    except Exception as error:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(error)) from error
    finally:
        session.close()


@app.post("/api/scrape")
def scrape():
    create_database()
    session = SessionLocal()
    stored_count = 0
    try:
        for source in get_all_sources():
            dataframe = (get_filtred_df_static(source) if source.scrape_type == "static"
                         else get_filtred_df_dynamic(source))
            opportunities = insert_opportunities(session, source, dataframe)
            embed_and_store_ami_descriptions(opportunities)
            stored_count += len(opportunities)
        return {"status": "success", "stored_count": stored_count}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    finally:
        session.close()



def main():
    create_database()

    session = SessionLocal()

    SOURCE = get_all_sources()                              

    client = get_qdrant_client()

    for source in SOURCE:
        print(f"======= Processing source: {source.title} (ID: {source.id}) =======")
        if(source.scrape_type == "static"):
            final_df = get_filtred_df_static(source)
        else:
            final_df = get_filtred_df_dynamic(source)

        opportunities = insert_opportunities(session, source, final_df)
      

        embed_and_store_ami_descriptions(opportunities)

    retrive_spesific_data(get_collection_name())



if __name__ == "__main__":
    main()