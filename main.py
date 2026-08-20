from sqlite3 import IntegrityError

import pandas as pd

from database.db import engine, Base, SessionLocal
from database.models import Opportunity,Source
from database.storage import get_all_sources
from scraper.hashing import generate_hash
from qdrant_connection import get_collection_name, get_qdrant_client
from qdrant_embedding import embed_and_store_ami_descriptions, retrieve_data,retrive_spesific_data
from sc2 import  get_filtered_df
import json


SOURCE = []

with open("tests/test_data.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)


def create_database():
    Base.metadata.create_all(engine)
    print("Database created successfully!")



def main():
    create_database()

    session = SessionLocal()

    SOURCE = get_all_sources()                              

    client = get_qdrant_client()
    print(f"Qdrant client initialized: {client}" if client else "Qdrant client not initialized.")

    test_df = pd.DataFrame(
        test_data
    )

    for source in SOURCE:
        print(f"Processing source: {source.title} (ID: {source.id})")
        filtered_df = get_filtered_df(source)
        filtered_data = filtered_df.to_dict(orient="records")
        #print(f"Filtered data for source {source.title}: {filtered_data}")

        opportunities = []

        for item in filtered_data:
            try:
                opp = Opportunity(
                    source_id=source.id,
                    title=item["title"],
                    description=item["description"],
                    document_url=" ",
                    submission_deadline=item["submission_deadline"],
                    sector=" ",
                    hash_id=generate_hash(item["title"], item["submission_deadline"], item["description"])
                )

               # print(opp.title)

                session.add(opp)
                session.commit()

                opportunities.append(opp)

            except IntegrityError:
                session.rollback()
                #print(f"IntegrityError: Duplicate entry for opportunity with hash_id {opp.hash_id}. Skipping.")

            except Exception as e:
                session.rollback()
                #print(f"Error while processing opportunity: {e}")

        embed_and_store_ami_descriptions(opportunities)

        retrive_spesific_data(get_collection_name())



if __name__ == "__main__":
    main()