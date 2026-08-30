import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "0"

from sklearn.metrics.pairwise import cosine_similarity


MODEL = None


def get_model():
    """Load the embedding model only when an embedding operation needs it."""
    global MODEL
    if MODEL is None:
        from sentence_transformers import SentenceTransformer

        MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return MODEL


def build_usefulness_query(sample_text):
    """Create a semantic query from a response sample to evaluate endpoint usefulness."""
    sample_text = sample_text[:500]
    return (
        "Evaluate whether this API endpoint is useful for CERT procurement intelligence. "
        "Look for public procurement opportunities, tenders, calls for proposals, expressions of interest, "
        "notices, or contracts related to software engineering, artificial intelligence, machine learning, "
        "data science, cybersecurity, digital transformation, automation, cloud computing, and information systems. "
        f"Sample response: {sample_text}"
    )


def score_response_usefulness(sample_text):
    """Embed the sample and compare it with the usefulness query."""
    if not sample_text:
        return None

    query = build_usefulness_query(sample_text)
    model = get_model()
    sample_embedding = model.encode([sample_text])
    query_embedding = model.encode([query])
    score = cosine_similarity(query_embedding, sample_embedding)[0][0]

    return {
        "query": query,
        "similarity_score": round(float(score), 4),
    }
