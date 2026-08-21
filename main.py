from sqlite3 import IntegrityError
import json
import pandas as pd
from dateutil import parser

from database.db import engine, Base, SessionLocal
from database.models import Opportunity, Source
from database.storage import (
    get_all_sources,
    seed_default_sources,
    get_top_5_results,
    save_similarity_results
)
from scraper.hashing import generate_hash
from qdrant_connection import get_collection_name, get_qdrant_client
from qdrant_embedding import embed_and_store_ami_descriptions, retrive_spesific_data
from sc2 import get_filtered_df
from static_sc import get_filtred_data


def create_database():
    Base.metadata.create_all(engine)
    print("Database tables verified/created successfully!")


def parse_date(value):
    if not value:
        return None
    try:
        return parser.parse(str(value))
    except Exception:
        return None


def run_pipeline():
    """Core pipeline function that can be called by CLI or API server."""
    create_database()
    seed_default_sources()

    session = SessionLocal()
    client = get_qdrant_client()
    print(f"Qdrant client initialized: {client}" if client else "Qdrant client not initialized.")

    sources = get_all_sources()
    newly_added_opportunities = []

    # Process registered sources
    for source in sources:
        print(f"======= Processing source: {source.title} (ID: {source.id}) =======")
        try:
            filtered_df = get_filtered_df(source)
            filtered_data = []

            # Add static data if applicable
            try:
                static_data = get_filtred_data()
                if static_data:
                    filtered_data += static_data
            except Exception as se:
                print(f"Static filter note: {se}")

            if not filtered_df.empty:
                filtered_data += filtered_df.to_dict(orient="records")

            for item in filtered_data:
                try:
                    title = item.get("title", "").strip()
                    if not title:
                        continue

                    desc = item.get("description", "")
                    deadline = item.get("submission_deadline", "")
                    hash_val = generate_hash(title, str(deadline), str(desc))

                    opp = Opportunity(
                        source_id=source.id,
                        title=title,
                        description=desc,
                        document_url=item.get("url", item.get("document_url", "")),
                        submission_deadline=str(deadline) if deadline else None,
                        published_date=item.get("published_date"),
                        sector=item.get("sector", "Information Technology"),
                        country=item.get("country", "Global"),
                        organization=item.get("organization", source.title),
                        hash_id=hash_val,
                    )

                    session.add(opp)
                    session.commit()
                    newly_added_opportunities.append(opp)

                except IntegrityError:
                    session.rollback()
                except Exception as e:
                    session.rollback()
                    print(f"Skipping duplicate or invalid item: {e}")

        except Exception as err:
            print(f"Could not process source {source.title}: {err}")

    # Fetch all opportunities from SQLite database for vector indexing
    all_opportunities = session.query(Opportunity).all()
    print(f"Total opportunities in database: {len(all_opportunities)}")

    if all_opportunities:
        print("Embedding and storing opportunities in vector index...")
        embed_and_store_ami_descriptions(all_opportunities)

        print("Querying top relevant opportunities and persisting top 5 in SQLite...")
        retrive_spesific_data(get_collection_name())

    session.close()

    # Retrieve and return top 5 results from SQLite
    top_5 = get_top_5_results()
    return top_5


def main():
    print("=" * 70)
    print("  AIScraperAgent Pipeline Runner")
    print("=" * 70)

    top_results = run_pipeline()

    print("\n" + "=" * 70)
    print("  TOP 5 OPPORTUNITIES SAVED IN DATABASE")
    print("=" * 70)

    if not top_results:
        print("No results found.")
    else:
        for idx, item in enumerate(top_results, 1):
            score_display = item.get("similarity_score_pct", "N/A")
            print(f"[{idx}] {item.get('title')}")
            print(f"    Match Score : {score_display} (raw: {item.get('similarity_score')})")
            print(f"    Organization: {item.get('organization')} | Country: {item.get('country')}")
            print(f"    Sector      : {item.get('sector')}")
            print(f"    Deadline    : {item.get('submission_deadline')}")
            print(f"    URL         : {item.get('document_url')}")
            print("-" * 70)

    return top_results


if __name__ == "__main__":
    main()