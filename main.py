from sqlite3 import IntegrityError

import pandas as pd

from database.db import engine, Base, SessionLocal
from database.models import Opportunity
from scraper.hashing import generate_hash
from qdrant_connection import get_collection_name, get_qdrant_client
from qdrant_embedding import embed_and_store_ami_descriptions, retrieve_data,retrive_spesific_data
from sc2 import  get_filtered_df
import json

with open("tests/test_data.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)


def create_database():
    print("Creating database...")
    Base.metadata.create_all(engine)
    print("Database created successfully!")



def main():
    create_database()

    session = SessionLocal()

    client = get_qdrant_client()
    print(f"Qdrant client initialized: {client}" if client else "Qdrant client not initialized.")

    test_df = pd.DataFrame(
        test_data
    )

    filtered_df =  get_filtered_df()
    filtered_data = filtered_df.to_dict(orient="records")

    for item in filtered_data:

        try :
            opp = Opportunity(
            source_id=1,
            title=item["title"],
            description=item["description"],
            document_url=" ",
            submission_deadline=item["submission_deadline"],
            sector=" ",
            hash_id=generate_hash(item["title"], item["submission_deadline"], item["description"])
            )
            session.add(opp)
            session.commit()
        except Exception as e:
            session.rollback()


    embed_and_store_ami_descriptions(filtered_df)

    #print(retrieve_data(get_collection_name()))
    retrive_spesific_data(get_collection_name())



if __name__ == "__main__":
    main()