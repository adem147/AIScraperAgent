import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent / ".env")


try:
    from qdrant_client import QdrantClient
except ImportError:  # pragma: no cover
    QdrantClient = None

def get_qdrant_client():
    url = os.getenv("QDRANT_URL", ":memory:").strip()

    try:
        if url == ":memory:":
            print("Using Qdrant in-memory mode")
            return QdrantClient(location=":memory:")

        print(f"Connecting to Qdrant at {url}")
        client = QdrantClient(url=url)
        client.get_collections()
        print("Qdrant connected successfully")
        return client

    except Exception as e:
        print("Qdrant connection failed")
        print(e)
        return None


def get_collection_name():
    return os.getenv("QDRANT_COLLECTION", "cert_ami_documents")
