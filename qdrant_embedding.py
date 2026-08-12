import hashlib

import pandas as pd
from database.models import Opportunity
from scraper.embedding import MODEL
from qdrant_connection import get_collection_name, get_qdrant_client
from qdrant_client import models



EMBED_MODEL = MODEL
CLIENT = get_qdrant_client()


def ensure_collection(collection_name: str = None):
    if models is None:
        print("models not available !")
        return False

    collection_name = get_collection_name()
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


def embed_and_store_ami_descriptions(opportunities: list[Opportunity]):
   
    collection_name = get_collection_name()

    client = CLIENT
    if client is None:
        return False
    
    if not ensure_collection(collection_name):
        return False

    points = []
    for el in opportunities:
        try : 
            print(f"Embedding and storing description for opportunity: {el.title[:30]}...")
            embedding_text = el.title + " " + el.description
            embedding = EMBED_MODEL.encode(
                embedding_text,
                normalize_embeddings=True
            ).tolist()
            points.append(
                models.PointStruct(
                    id=el.id,
                    vector=embedding,
                    payload={
                        "hash_id": el.hash_id,
                        "title": el.title,
                        "description": embedding_text,
                    },
                )
            )
        except Exception as e:
            print(f"Failed to embed and store description for opportunity: {el.title[:30]}... ({e})")
            continue

    client.upsert(collection_name=collection_name, points=points)
    return True


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


def retrive_spesific_data(collection_name: str = None):
    client = CLIENT
    query = (
    "Find procurement opportunities relevant to an IT engineering company. "
    "The opportunity should involve artificial intelligence, machine learning, "
    "software development, cybersecurity, cloud computing, data science, "
    "automation, digital platforms, information systems, or technology consulting. "
    "Include tenders, calls for proposals, expressions of interest, and contracts "
    "where technical skills in programming, AI, cybersecurity, or IT infrastructure are required."
    )
    query_vector = EMBED_MODEL.encode(
    query,
    normalize_embeddings=True
    ).tolist()

    results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
    )

    for r in results.points[:10]:
        print(r.payload)   # your stored data
        print(f"{r.score:.2f}")     # similarity score