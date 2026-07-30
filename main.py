import pandas as pd

from database.db import engine, Base
from qdrant_connection import get_collection_name, get_qdrant_client
from qdrant_embedding import embed_and_store_ami_descriptions, retrieve_data
from sc2 import  get_filtered_df


def create_database():
    print("Creating database...")
    Base.metadata.create_all(engine)
    print("Database created successfully!")



def main():
    create_database()

    client = get_qdrant_client()
    print(f"Qdrant client initialized: {client}" if client else "Qdrant client not initialized.")

    test_df = pd.DataFrame(
        {
            "id": [1, 2],
            "title": ["Test Opportunity 1", "Test Opportunity 2"],
            "description": [
                "This is a test description for opportunity 1.",
                "This is a test description for opportunity 2.",
            ],
            "organization": ["Test Org 1", "Test Org 2"],
        }
    )

    filtered_df =  get_filtered_df()

    embed_and_store_ami_descriptions(filtered_df)

    #print(retrieve_data(get_collection_name()))



if __name__ == "__main__":
    main()