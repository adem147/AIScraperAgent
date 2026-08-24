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
from datetime import datetime


SOURCE = []

with open("tests/test_data.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)


def parse_datetime(value):
    if not value or isinstance(value, datetime):
        return value or None

    if isinstance(value, str):
        normalized_value = value.strip()
        if not normalized_value:
            return None

        try:
            return datetime.fromisoformat(normalized_value.replace("Z", "+00:00"))
        except ValueError:
            for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    return datetime.strptime(normalized_value, date_format)
                except ValueError:
                    continue

    raise ValueError(f"Unsupported datetime value: {value!r}")


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
                published_date = parse_datetime(item.get("published_date"))
                submission_deadline = parse_datetime(item.get("submission_deadline"))

                opp = Opportunity(
                    source_id=source.id,
                    title=item.get("title",""),
                    description=item.get("description",""),
                    url=item.get("url",""),
                    published_date=published_date,
                    submission_deadline=submission_deadline,
                    sector=item.get("sector",""),
                    hash_id=generate_hash(item.get("title",""), 
                                          submission_deadline.isoformat() if submission_deadline else "", 
                                          item.get("description","")
                                        )
                )

                session.add(opp)
                session.commit()

                opportunities.append(opp)

            except IntegrityError:
                session.rollback()
            except Exception as e:
                session.rollback()

        embed_and_store_ami_descriptions(opportunities)

    retrive_spesific_data(get_collection_name())



if __name__ == "__main__":
    main()