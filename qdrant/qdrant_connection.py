import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent.parent / ".env")


from qdrant_client import QdrantClient


def get_qdrant_client():
    url = os.getenv("QDRANT_URL", "").strip()
    api_key = os.getenv("QDRANT_API_KEY", "").strip() or None

    if not url:
        print("QDRANT_URL is not configured")
        return None

    try:
        print(f"Connecting to Qdrant at {url}")
        client = QdrantClient(url=url, api_key=api_key)
        client.get_collections()
        print("Qdrant connected successfully")
        return client

    except Exception as e:
        print("Qdrant connection failed")
        print(e)
        return None


def get_collection_name():
    return os.getenv("QDRANT_COLLECTION", "cert_ami_documents")
