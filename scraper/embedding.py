from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


MODEL = SentenceTransformer("all-MiniLM-L6-v2")


def build_usefulness_query(sample_text):
    """Create a semantic query from a response sample to evaluate endpoint usefulness."""
    sample_text = sample_text[:1000]
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
    sample_embedding = MODEL.encode([sample_text])
    query_embedding = MODEL.encode([query])
    score = cosine_similarity(query_embedding, sample_embedding)[0][0]

    return {
        "query": query,
        "similarity_score": round(float(score), 4),
    }
