from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import BestApiEndpoint


def get_best_api_for_source(source_id):
    """Retrieve the best API endpoint for a given source ID."""
    session: Session = SessionLocal()
    try:
        return (
            session.query(BestApiEndpoint)
            .filter(BestApiEndpoint.source_id == source_id)
            .first()
        )
    finally:
        session.close()

def save_best_api_for_source(source_id, endpoint_url, method="GET", similarity_score=None):
    """Persist the best API endpoint for a website, only once per source ID."""
    session: Session = SessionLocal()
    try:
        session.add(
            BestApiEndpoint(    
                source_id=source_id,
                endpoint_url=endpoint_url,
                method=method,
                similarity_score=similarity_score,
            )
        )
        session.commit()
        return True
    finally:
        session.close()
