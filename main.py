from sqlite3 import IntegrityError

import pandas as pd

from database.db import engine, Base, SessionLocal
from database.models import Opportunity,Source
from database.storage import get_all_sources
from scraper.hashing import generate_hash
from qdrant_connection import get_collection_name, get_qdrant_client
from qdrant_embedding import embed_and_store_ami_descriptions, retrieve_data,retrive_spesific_data
from sc2 import  get_filtered_df
from static_sc import get_filtred_data
import json


SOURCE = []

with open("tests/test_data.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)


def create_database():
    print("Creating database...")
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
        print(f"======= Processing source: {source.title} (ID: {source.id}) =======")
        filtered_df = get_filtered_df(source) #data coming from ths dynamic api filter

        filtered_data = get_filtred_data() #data coming from the static html filter

        filtered_data += filtered_df.to_dict(orient="records") 


        #print(f"Filtered data for source {source.title}: {filtered_data}")

        opportunities = []

        for item in filtered_data:
            try:
                opp = Opportunity(
                    source_id=source.id,
                    title=item.get("title",""),
                    description=item.get("description",""),
                    url=item.get("url",""),
                    published_date = item.get("published_date",""),
                    submission_deadline=item.get("submission_deadline",""),
                    sector=item.get("sector",""),
                    hash_id=generate_hash(item.get("title",""), 
                                          item.get("submission_deadline",""), 
                                          item.get("description","")
                                        )
                )

                print("opportunite title " : opp.title)

                session.add(opp)
                session.commit()

                opportunities.append(opp)

            except IntegrityError:
                session.rollback()
                print(f"IntegrityError: Duplicate entry for opportunity with hash_id {opp.hash_id}. Skipping.")

            except Exception as e:
                session.rollback()
                print(f"Error while processing opportunity: {e}")

        embed_and_store_ami_descriptions(opportunities)

    retrive_spesific_data(get_collection_name())



if __name__ == "__main__":
    main()