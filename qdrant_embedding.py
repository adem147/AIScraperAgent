import hashlib

import pandas as pd
from scraper.embedding import MODEL
from qdrant_connection import get_collection_name, get_qdrant_client


try:
    from qdrant_client import models
except ImportError:  # pragma: no cover
    models = None


EMBED_MODEL = MODEL
CLIENT = get_qdrant_client()


def ensure_collection(collection_name: str = None):
    if models is None:
        print("❌ models not available")
        return False

    collection_name = collection_name or get_collection_name()
    client = CLIENT

    if client is None:
        print("client is None")
        return False

    try:
        client.get_collection(collection_name)
        print(f"Collection {collection_name} already exists")
        return True

    except Exception as e:
        print(f"Collection not found, creating it... ({e})")

        try:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=384,
                    distance=models.Distance.COSINE
                ),
            )
            print(f"Collection {collection_name} created")
            return True

        except Exception as e:
            print("Failed to create collection:", e)
            return False


def embed_and_store_ami_descriptions(df: pd.DataFrame, collection_name: str = None):
    """Embed AMI descriptions and store them in Qdrant for a simple local test."""
    if df is None or df.empty:
        return []

    if models is None:
        return []

    if "description" not in df.columns:
        return []

    rows = df[df["description"].notna() & df["description"].astype(str).str.strip().ne("")].copy()
    if rows.empty:
        return []

    rows["description_text"] = rows["description"].astype(str)
    collection_name = collection_name or get_collection_name()

    client = CLIENT
    if client is None:
        return []

    if not ensure_collection(collection_name):
        return []

    points = []
    for index, row in rows.iterrows():
        print(f"Embedding and storing description for row {index}: {row['description_text'][:30]}...")
        description_text = row["description_text"]
        embedding = EMBED_MODEL.encode([description_text])[0].tolist()
        points.append(
            models.PointStruct(
                id= hashlib.md5(description_text.encode()).hexdigest(),
                vector=embedding,
                payload={
                    "id": row.get("id", ""),
                    "title": row.get("title", ""),
                    "description": description_text,
                },
            )
        )

    client.upsert(collection_name=collection_name, points=points)
    return [point.payload for point in points]


def retrieve_data(collection_name: str = None):
    print("Retrieving data from Qdrant...") 
    client = CLIENT
    if client is None:
        return []

    collection_name = collection_name or get_collection_name()

    info = client.get_collection(collection_name)

    print("Points count:", info.points_count)

    response = client.scroll(collection_name=collection_name)
    return [point for point in response[0]]