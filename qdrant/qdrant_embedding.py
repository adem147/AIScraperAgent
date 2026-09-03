import hashlib

import pandas as pd
from database.models import Opportunity
from database.models import SimilarityResult
from database.storage import save_similarity_results
from scraper.embedding import get_model
from qdrant.qdrant_connection import get_collection_name, get_qdrant_client
from qdrant_client import models



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

def check_duplicates(embedding, client):
    THRESH_HOLD = 0.9

    result = client.query_points(
        collection_name=get_collection_name(),
        query=embedding,
        limit=1,
        with_payload=False,
    )

    if result and result.points and result.points[0].score >= THRESH_HOLD:
        return False
    return True



def get_unique_opportunity_embeddings(opportunities: list[Opportunity]):
    """Return embeddings whose opportunities are not semantic duplicates in Qdrant."""
    collection_name = get_collection_name()

    client = CLIENT
    if client is None:
        return []

    embed_model = get_model()
    
    if not ensure_collection(collection_name):
        return []

    unique_embeddings = []
    for el in opportunities:
        try : 
            print(f"Embedding and storing description for opportunity: {el.title[:30]}...")
            embedding_text = f"{el.title} {el.description}"
            embedding = embed_model.encode(
                embedding_text,
                normalize_embeddings=True
            ).tolist()

            if(check_duplicates(embedding,client) is not True):
                print("duplicate found : ",el.title)
                continue

            unique_embeddings.append((el, embedding))
        except Exception as e:
            print(f"Failed to embed and store description for opportunity: {el.title[:30]}... ({e})")
            continue

    return unique_embeddings


def store_ami_embedding(opportunity, embedding):
    """Store one database-backed opportunity embedding in Qdrant."""
    if CLIENT is None:
        return False
    CLIENT.upsert(
        collection_name=get_collection_name(),
        points=[models.PointStruct(
            id=opportunity.id,
            vector=embedding,
            payload={
                "title": opportunity.title,
                "source_id": opportunity.source_id,
            },
        )],
    )
    return True


CERT_RELEVANCE_QUERY = (
    "Find procurement opportunities relevant to an IT engineering company. "
    "The opportunity should involve artificial intelligence, machine learning, "
    "software development, cybersecurity, cloud computing, data science, "
    "automation, digital platforms, information systems, or technology consulting. "
    "Include tenders, calls for proposals, expressions of interest, and contracts "
    "where technical skills in programming, AI, cybersecurity, or IT infrastructure are required."
)


def search_qdrant_opportunities(query: str = "", limit: int = 1000):
    """Return Qdrant-ranked opportunities for a query or the CERT relevance profile."""
    if CLIENT is None:
        return []

    search_text = query.strip() or CERT_RELEVANCE_QUERY
    query_vector = get_model().encode(search_text, normalize_embeddings=True).tolist()
    try:
        response = CLIENT.query_points(
            collection_name=get_collection_name(),
            query=query_vector,
            limit=limit,
            with_payload=True,
        )
    except Exception as error:
        print(f"Qdrant search failed: {error}")
        return []

    return [
        {
            "id": int(result.id),
            "score": float(result.score),
            **(result.payload or {}),
        }
        for result in response.points
    ]


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
    query = CERT_RELEVANCE_QUERY
    query_vector = get_model().encode(
    query,
    normalize_embeddings=True
    ).tolist()

    try:

        results = client.query_points(
            collection_name=collection_name,
            query=query_vector,
        )

        similarity_results = [
            SimilarityResult(
                opportunity_id=int(r.id),
                similarity_score=float(r.score),
                title=(r.payload or {}).get("title", ""),
            )
            for r in results.points
        ]
        save_similarity_results(similarity_results)

        print("======= Embedding results saved ! =======")

        for r in results.points:
            print(r.payload.get("title",": "),f"{r.score:.2f}")   # your stored data
            print("-" *40)

        return similarity_results


    except Exception as e:
        print(e)
        return []

    