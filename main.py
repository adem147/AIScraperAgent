import pandas as pd
from pathlib import Path
from typing import Any
from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database.models import Opportunity, Source
from scraper.hashing import generate_hash
from database.storage import (count_opportunities, delete_opportunity as remove_opportunity,
                               get_all_sources,
                               get_opportunities_by_ids,
                               initialize_database,
                               insert_opportunity, parse_datetime,
                               search_opportunities as find_opportunities)
from qdrant_connection import get_collection_name, get_qdrant_client
from qdrant_embedding import (store_ami_embedding,
                               get_unique_opportunity_embeddings,
                               retrive_spesific_data, search_qdrant_opportunities)
from sc2 import get_filtred_df_dynamic
from static_sc import get_filtred_df_static
from notification import SMTPSettings, SMTP_PROVIDERS, get_smtp_settings, save_smtp_settings, send_new_opportunities_email
import json


SOURCE = []
FRONTEND_DIR = Path(__file__).parent / "frontend"
app = FastAPI(title="CERT Opportunity Monitor")
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


with open("tests/test_data.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)


def create_database():
    print("Creating database...")
    initialize_database()
    print("Database created successfully!")


def opportunity_to_dict(opportunity: Opportunity, source: Source | None = None, score: float = 0.0) -> dict[str, Any]:
    return {
        "id": opportunity.id,
        "title": opportunity.title or "Untitled opportunity",
        "description": opportunity.description or "",
        "url": opportunity.url or "",
        "sector": opportunity.sector or "",
        "source_id": source.id if source else opportunity.source_id,
        "source_title": source.title if source else "Unknown source",
        "source_url": source.url if source else "",
        "published_date": opportunity.published_date.isoformat() if opportunity.published_date else None,
        "submission_deadline": opportunity.submission_deadline.isoformat() if opportunity.submission_deadline else None,
        "score": round(score, 3),
    }


def create_opportunities(source, dataframe):
    """Build opportunities in memory before embedding and persistence."""
    opportunities = []
    for item in dataframe.to_dict(orient="records"):
        submission_deadline = parse_datetime(item.get("submission_deadline"))
        opportunities.append(Opportunity(
            source_id=source.id,
            title=item.get("title", ""),
            description=item.get("description", ""),
            url=item.get("url", ""),
            published_date=parse_datetime(item.get("published_date")),
            submission_deadline=submission_deadline,
            sector=item.get("sector", ""),
            hash_id=generate_hash(
                item.get("title", ""),
                submission_deadline.isoformat() if submission_deadline else "",
                item.get("description", ""),
            ),
        ))
    return opportunities


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
    return {"opportunities": count_opportunities(), "sources": len(get_all_sources())}


@app.get("/api/settings/smtp")
def smtp_settings():
    return {"providers": SMTP_PROVIDERS, "settings": get_smtp_settings()}


@app.put("/api/settings/smtp")
def update_smtp_settings(settings: SMTPSettings):
    provider_settings = SMTP_PROVIDERS[settings.provider]
    save_smtp_settings({
        **settings.model_dump(),
        "host": provider_settings["host"],
        "port": provider_settings["port"],
        "use_ssl": provider_settings["use_ssl"],
    })
    return {"status": "saved", "settings": get_smtp_settings()}


@app.get("/api/opportunities")
def search_opportunities(
    query: str = Query(default="", max_length=200),
    source_id: int | None = Query(default=None),
    deadline_after: date | None = Query(default=None),
):
    results = [opportunity_to_dict(opportunity, source, score)
               for opportunity, source, score in find_opportunities(query, source_id, deadline_after)]
    return {"count": len(results), "results": results}


@app.get("/api/search")
def search_qdrant(query: str = Query(default="", max_length=500)):
    """Return Qdrant-ranked opportunities, using the CERT profile when query is empty."""

    qdrant_results = search_qdrant_opportunities(query)

    qdrant_map = {r["id"]: r["score"] for r in qdrant_results}

    ids = [int(result["id"]) for result in qdrant_results if result.get("id") is not None]

    db_query_results = get_opportunities_by_ids(ids)

    results = [
        opportunity_to_dict(
            opportunity=opportunity,
            source=source,
            score=qdrant_map.get(opportunity.id, 0.0)
        )
        for (opportunity, source) in db_query_results
    ]
    
    results.sort(key=lambda x: x["score"], reverse=True)

    return {"count": len(results), "results": results}


@app.delete("/api/opportunities/{opportunity_id}")
def delete_opportunity(opportunity_id: int):
    try:
        if not remove_opportunity(opportunity_id):
            raise HTTPException(status_code=404, detail="Opportunity not found")

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
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.post("/api/scrape")
def scrape():
    create_database()
    stored_count = 0
    try:
        for source in get_all_sources():
            dataframe = (get_filtred_df_static(source) if source.scrape_type == "static"
                         else get_filtred_df_dynamic(source))
            opportunities = create_opportunities(source, dataframe)
            for opportunity, embedding in get_unique_opportunity_embeddings(opportunities):
                saved_opportunity = insert_opportunity(opportunity)
                store_ami_embedding(saved_opportunity, embedding)
                stored_count += 1
                send_new_opportunities_email([saved_opportunity])
        return {"status": "success", "stored_count": stored_count}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error



def main():
    create_database()

    SOURCE = get_all_sources()                              

    client = get_qdrant_client()

    for source in SOURCE:
        print(f"======= Processing source: {source.title} (ID: {source.id}) =======")
        if(source.scrape_type == "static"):
            final_df = get_filtred_df_static(source)
        else:
            final_df = get_filtred_df_dynamic(source)

        opportunities = create_opportunities(source, final_df)
        for opportunity, embedding in get_unique_opportunity_embeddings(opportunities):
            saved_opportunity = insert_opportunity(opportunity)
            store_ami_embedding(saved_opportunity, embedding)
            send_new_opportunities_email([saved_opportunity])

    retrive_spesific_data(get_collection_name())



if __name__ == "__main__":
    #main()
    pass