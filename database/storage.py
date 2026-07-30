from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import BestApiEndpoint


def save_best_api_for_source(source_url, endpoint_url, method="GET", similarity_score=None):
    """Persist the best API endpoint for a website, only once per source URL."""
    session: Session = SessionLocal()
    try:
        existing = (
            session.query(BestApiEndpoint)
            .filter(BestApiEndpoint.source_url == source_url)
            .first()
        )

        if existing:
            existing.endpoint_url = endpoint_url
            existing.method = method
            existing.similarity_score = str(similarity_score)
        else:
            session.add(
                BestApiEndpoint(
                    source_url=source_url,
                    endpoint_url=endpoint_url,
                    method=method,
                    similarity_score=str(similarity_score),
                )
            )

        session.commit()
        return True
    finally:
        session.close()
